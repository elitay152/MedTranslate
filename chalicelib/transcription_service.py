import boto3
import json


class TranscriptionService:
    def __init__(self, storage_service):
        self.rekognition_client = boto3.client('rekognition', region_name='us-east-2')  # For text detection in images
        self.comprehend_medical_client = boto3.client('comprehendmedical')  # For medical entity detection
        self.bucket_name = storage_service.get_storage_location()
        self.storage_service = storage_service

    def process_image(self, file_id):
        """
        Extract text from an image in S3 using Rekognition and analyze it with Comprehend Medical.
        """
        # Step 1: Extract text from the image using Amazon Rekognition
        extracted_text = self.extract_text_from_image(file_id)
        if not extracted_text:
            return {"error": "No text detected in the image."}

        # Step 2: Analyze the extracted text with Comprehend Medical
        medical_entities = self.detect_medical_entities(extracted_text)

        return {
            "fileId": file_id,
            "extractedText": extracted_text,
            "medicalEntities": medical_entities
        }

    def extract_text_from_image(self, file_id):
        """
        Uses Amazon Rekognition to extract text from an image in the S3 bucket.
        """
        try:
            # Use Rekognition to detect text in the image
            response = self.rekognition_client.detect_text(
                Image={
                    'S3Object': {
                        'Bucket': self.bucket_name,
                        'Name': file_id
                    }
                }
            )

            # Combine detected text from Rekognition response
            extracted_text = " ".join([
                item['DetectedText'] for item in response['TextDetections']
                if item['Type'] == 'LINE'  # Focus on line-level text
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
            # Call Comprehend Medical to detect entities in the extracted text
            response = self.comprehend_medical_client.detect_entities(Text=text)

            # Extract medical entities from the response
            medical_entities = []
            for entity in response['Entities']:
                medical_entities.append({
                    "Text": entity['Text'],
                    "Category": entity['Category'],
                    "Type": entity['Type'],
                    "Traits": entity.get('Traits', [])
                })

            return medical_entities

        except Exception as e:
            print(f"Error detecting medical entities: {e}")
            return []

