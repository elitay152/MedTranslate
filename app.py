from chalice import Chalice, Response
from chalicelib import storage_service
from chalicelib import transcription_service
from chalicelib import translation_service
from chalicelib import speech_service

#####
# Chalice app configuration
#####
app = Chalice(app_name='MedTranslate')
app.debug = True

#####
# Services initialization
#####
storage_location = 'medtranslate-storage-2'  # Replace with your S3 bucket name
storage_service = storage_service.StorageService(storage_location)
transcription_service = transcription_service.TranscriptionService(storage_service)
processing_service = translation_service.FlexibleProcessingService(storage_service)
speech_service = speech_service.SpeechService(storage_service)


@app.route('/upload/{file_name}', methods=['PUT'], content_types=['application/octet-stream'])
def upload_to_s3(file_name):
    """
    Uploads a raw binary file to S3.
    """
    try:
        # Get the raw body of the request
        body = app.current_request.raw_body

        # Upload the file to S3 directly
        storage_service.upload_file(body, file_name)

        # Create a public URL for the uploaded file
        file_url = f'https://{storage_location}.s3.amazonaws.com/{file_name}'

        # Respond with a success message and the file URL
        response = {
            'message': f'The file {file_name} was uploaded successfully.',
            'fileUrl': file_url
        }
        return Response(
            body=response,
            status_code=200,
            headers={'Access-Control-Allow-Origin': '*'}  # CORS support
        )
    except Exception as e:
        # Handle errors gracefully
        error_response = {
            'error': f'Failed to upload file: {str(e)}'
        }
        return Response(
            body=error_response,
            status_code=500,
            headers={'Access-Control-Allow-Origin': '*'}  # CORS support
        )


@app.route('/process', methods=['POST'])
def process_file():
    """
    Endpoint to process a file and return either full text translation or structured medical data.
    """
    request = app.current_request
    data = request.json_body

    file_id = data.get('fileId')
    mode = data.get('mode', 'full_text')  # Default to 'full_text'
    target_language = data.get('targetLanguage', 'en')

    if not file_id:
        return Response(body={"error": "File ID is required."}, status_code=400)

    if mode not in ['full_text', 'structured']:
        return Response(body={"error": "Invalid mode. Choose 'full_text' or 'structured'."}, status_code=400)

    try:
        # Process the file based on the selected mode
        result = transcription_service.process_image(file_id, mode=mode, target_language=target_language)
        return Response(body=result, status_code=200)
    except Exception as e:
        return Response(body={"error": f"Processing failed: {str(e)}"}, status_code=500)


@app.route('/translate', methods=['POST'])
def translate_text():
    """
    Endpoint to translate arbitrary text.
    """
    request = app.current_request
    data = request.json_body

    text = data.get('text')
    source_language = data.get('sourceLanguage', 'auto')
    target_language = data.get('targetLanguage', 'en')

    if not text:
        return Response(body={"error": "Text is required for translation."}, status_code=400)

    try:
        # Translate the provided text
        translation_result = processing_service.translate_text(text, source_language, target_language)
        return Response(body=translation_result, status_code=200)
    except Exception as e:
        return Response(body={"error": f"Translation failed: {str(e)}"}, status_code=500)


@app.route('/synthesize', methods=['POST'])
def synthesize_speech():
    """
    Endpoint to convert translated text to speech.
    """
    request = app.current_request
    data = request.json_body

    text = data.get('text')
    target_language = data.get('targetLanguage', 'en')  # Default to English

    if not text:
        return Response(body={"error": "Text is required for speech synthesis."}, status_code=400)

    try:
        speech_url = speech_service.synthesize_speech(text, target_language)
        return Response(body={"speechUrl": speech_url}, status_code=200)
    except ValueError as ve:
        return Response(body={"error": str(ve)}, status_code=400)
    except RuntimeError as re:
        return Response(body={"error": str(re)}, status_code=500)
