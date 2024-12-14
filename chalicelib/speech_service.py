import boto3
import time


class SpeechService:
    def __init__(self, storage_service):
        self.client = boto3.client('polly')
        self.bucket_name = storage_service.get_storage_location()
        self.storage_service = storage_service

    def synthesize_speech(self, text, target_language):
        """
        Converts translated text into speech using AWS Polly and stores the output in S3.
        :param text: The translated text to convert into speech.
        :param target_language: Target language code (e.g., 'en', 'es', 'fr').
        :return: Public S3 URL of the generated speech file.
        """
        POLL_DELAY = 5

        # Map target languages to Polly voice IDs
        voice_map = {
            'en': 'Ivy',
            'de': 'Marlene',
            'fr': 'Celine',
            'it': 'Carla',
            'es': 'Conchita'
        }

        # Check if the target language is supported
        if target_language not in voice_map:
            raise ValueError(f"Target language '{target_language}' is not supported for speech synthesis.")

        try:
            # Start the Polly speech synthesis task
            response = self.client.start_speech_synthesis_task(
                Text=text,
                VoiceId=voice_map[target_language],
                OutputFormat='mp3',
                OutputS3BucketName=self.bucket_name
            )

            # Get the task ID and monitor its progress
            synthesis_task = {
                'taskId': response['SynthesisTask']['TaskId'],
                'taskStatus': 'inProgress'
            }

            while synthesis_task['taskStatus'] in ['inProgress', 'scheduled']:
                time.sleep(POLL_DELAY)
                response = self.client.get_speech_synthesis_task(
                    TaskId=synthesis_task['taskId']
                )
                synthesis_task['taskStatus'] = response['SynthesisTask']['TaskStatus']

            # Check if the task completed successfully
            if synthesis_task['taskStatus'] == 'completed':
                speech_uri = response['SynthesisTask']['OutputUri']
                self.storage_service.make_file_public(speech_uri)
                return speech_uri
            else:
                raise RuntimeError(f"Speech synthesis task failed with status: {synthesis_task['taskStatus']}")

        except Exception as e:
            raise RuntimeError(f"An error occurred during speech synthesis: {str(e)}")
