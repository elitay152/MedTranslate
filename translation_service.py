import boto3
import json


class FlexibleProcessingService:
    def __init__(self, storage_service):
        self.rekognition_client = boto3.client('rekognition')
        self.comprehend_medical_client = boto3.client('comprehendmedical')
        self.translate_client = boto3.client('translate')
        self.bucket_name = storage_service.get_storage_location()
        self.storage_service = storage_service

    def process_image(self, file_id, mode='full_text', source_language='auto', target_language='en'):
        """
        Process an image to extract text and provide either full text translation or structured medical output.
        :param file_id: S3 key of the image file.
        :param mode: 'full_text' or 'structured'.
        :param source_language: Source language code for translation (default: 'auto').
        :param target_language: Target language code for translation (default: 'en').
        :return: A dictionary with the processed result.
        """
        # Step 1: Extract text from the image
        extracted_text = self.extract_text_from_image(file_id)
        if not extracted_text:
            return {"error": "No text detected in the image."}

        # Step 2: Process based on the selected mode
        if mode == 'full_text':
            # Full text translation
            translation = self.translate_text(extracted_text, source_language, target_language)
            return {
                "fileId": file_id,
                "mode": "full_text",
                "originalText": extracted_text,
                "translatedText": translation['translatedText'],
                "sourceLanguage": translation['sourceLanguage'],
                "targetLanguage": translation['targetLanguage']
            }
        elif mode == 'structured':
            # Structured medical output
            medical_entities = self.detect_medical_entities(extracted_text)
            return {
                "fileId": file_id,
                "mode": "structured",
                "originalText": extracted_text,
                "medicalEntities": medical_entities
            }
        else:
            return {"error": "Invalid mode specified. Use 'full_text' or 'structured'."}

    def extract_text_from_image(self, file_id):
        """
        Uses Amazon Rekognition to extract text from an image in the S3 bucket.
        """
        try:
            response = self.rekognition_client.detect_text(
                Image={
                    'S3Object': {
                        'Bucket': self.bucket_name,
                        'Name': file_id
                    }
                }
            )
            extracted_text = " ".join([
                item['DetectedText'] for item in response['TextDetections']
                if item['Type'] == 'LINE'
            ])
            return extracted_text
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return None

    def detect_medical_entities(self, text):
        """
        Uses Amazon Comprehend Medical to analyze text and extract medical entities.
        """
        try:
            response = self.comprehend_medical_client.detect_entities(Text=text)
            medical_entities = [
                {
                    "Text": entity['Text'],
                    "Category": entity['Category'],
                    "Type": entity['Type'],
                    "Traits": entity.get('Traits', [])
                }
                for entity in response['Entities']
            ]
            return medical_entities
        except Exception as e:
            print(f"Error detecting medical entities: {e}")
            return []

    def translate_text(self, text, source_language, target_language):
        """
        Uses Amazon Translate to translate text into the target language.
        """
        try:
            response = self.translate_client.translate_text(
                Text=text,
                SourceLanguageCode=source_language,
                TargetLanguageCode=target_language
            )
            return {
                "translatedText": response['TranslatedText'],
                "sourceLanguage": response['SourceLanguageCode'],
                "targetLanguage": response['TargetLanguageCode']
            }
        except Exception as e:
            print(f"Error translating text: {e}")
            return {"error": "Translation failed."}
