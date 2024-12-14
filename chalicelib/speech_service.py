import boto3
import time

class SpeechService:
    def __init__(self, storage_service):
        self.client = boto3.client('polly', region_name='us-east-2')
        self.bucket_name = storage_service.get_storage_location()
        self.storage_service = storage_service

    def synthesize_speech(self, text, target_language):
        POLL_DELAY = 5

        # Map target languages to Polly voices
        voice_map = {
            'en': 'Joanna',
            'es': 'Conchita',
            'de': 'Marlene',
            'fr': 'Celine',
            'it': 'Carla'
        }

        if target_language not in voice_map:
            raise ValueError(f"Unsupported target language: {target_language}")

        try:
            # Start a Polly speech synthesis task
            response = self.client.start_speech_synthesis_task(
                Text=text,
                VoiceId=voice_map[target_language],
                OutputFormat='mp3',
                OutputS3BucketName=self.bucket_name,
                OutputS3KeyPrefix="speech/"
            )

            synthesis_task = response['SynthesisTask']

            # Poll for task completion
            while synthesis_task['TaskStatus'] in ['scheduled', 'inProgress']:
                time.sleep(POLL_DELAY)
                synthesis_task = self.client.get_speech_synthesis_task(
                    TaskId=synthesis_task['TaskId']
                )['SynthesisTask']

            # Check if the task completed successfully
            if synthesis_task['TaskStatus'] != 'completed':
                raise RuntimeError("Polly synthesis task failed.")

            # Return the public URL of the generated file
            speech_uri = synthesis_task['OutputUri']
            return speech_uri

        except Exception as e:
            # Handle errors gracefully
            raise RuntimeError(f"An error occurred during speech synthesis: {e}")
