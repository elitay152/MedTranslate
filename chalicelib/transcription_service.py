import boto3


class TranslationService:
    def __init__(self, comprehend_medical_client=None):
        # Initialize Amazon Translate and optionally Comprehend Medical
        self.translate_client = boto3.client('translate', region_name='us-east-2')
        self.comprehend_medical_client = comprehend_medical_client or boto3.client('comprehendmedical')

    def process_text(self, text, mode='full_text', source_language='auto', target_language='en'):
        """
        Translates full text or structured medical entities.
        :param text: The input text to process.
        :param mode: 'full_text' for full text translation or 'structured' for medical entities.
        :param source_language: Source language code (default: 'auto').
        :param target_language: Target language code (default: 'en').
        :return: A dictionary with translation results.
        """
        if mode == 'full_text':
            # Translate full text
            return self.translate_full_text(text, source_language, target_language)
        elif mode == 'structured':
            # Analyze medical entities and translate them
            return self.translate_medical_entities(text, source_language, target_language)
        else:
            return {"error": "Invalid mode specified. Use 'full_text' or 'structured'."}

    def translate_full_text(self, text, source_language, target_language):
        """
        Translates the input text using Amazon Translate.
        """
        try:
            response = self.translate_client.translate_text(
                Text=text,
                SourceLanguageCode=source_language,
                TargetLanguageCode=target_language
            )
            return {
                "mode": "full_text",
                "originalText": text,
                "translatedText": response['TranslatedText'],
                "sourceLanguage": response['SourceLanguageCode'],
                "targetLanguage": response['TargetLanguageCode']
            }
        except Exception as e:
            print(f"Error translating full text: {e}")
            return {"error": "Translation failed for full text."}

    def translate_medical_entities(self, text, source_language, target_language):
        """
        Detects medical entities in the text and translates their descriptions.
        """
        try:
            # Analyze text using Comprehend Medical
            response = self.comprehend_medical_client.detect_entities(Text=text)

            # Collect and translate each medical entity's text
            translated_entities = []
            for entity in response['Entities']:
                translated_entity = {
                    "originalText": entity['Text'],
                    "category": entity['Category'],
                    "type": entity['Type'],
                    "traits": entity.get('Traits', [])
                }

                # Translate the entity text
                try:
                    translation = self.translate_client.translate_text(
                        Text=entity['Text'],
                        SourceLanguageCode=source_language,
                        TargetLanguageCode=target_language
                    )
                    translated_entity["translatedText"] = translation['TranslatedText']
                except Exception as te:
                    print(f"Error translating medical entity: {entity['Text']} - {te}")
                    translated_entity["translatedText"] = "Translation failed."

                translated_entities.append(translated_entity)

            return {
                "mode": "structured",
                "originalText": text,
                "medicalEntities": translated_entities,
                "sourceLanguage": source_language,
                "targetLanguage": target_language
            }
        except Exception as e:
            print(f"Error detecting medical entities: {e}")
            return {"error": "Failed to process medical entities."}
