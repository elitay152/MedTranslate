from chalice import Chalice, Response
from chalicelib import storage_service
from chalicelib import transcription_service
from chalicelib.translation_service import TranslationService
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
translation_service = TranslationService()
speech_service = speech_service.SpeechService(storage_service)


@app.route('/upload/{file_name}', methods=['PUT'], content_types=['application/octet-stream'])
def upload_to_s3(file_name):
    """
    Uploads a raw binary file to S3.
    """
    try:
        # Get the raw body of the request
        body = app.current_request.raw_body

        # Pass the file bytes and original file name to the upload_file method
        result = storage_service.upload_file(body, file_name)

        # Respond with the unique file ID and public URL
        response = {
            'message': f'The file {file_name} was uploaded successfully.',
            'fileId': result['fileId'],  # Unique S3 key
            'fileUrl': result['fileUrl']  # Public file URL
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
    Endpoint to process a file (extract text) and optionally translate it.
    """
    request = app.current_request
    data = request.json_body

    file_id = data.get('fileId')
    mode = data.get('mode', 'full_text')  # Default to 'full_text'
    source_language = data.get('sourceLanguage', 'auto')
    target_language = data.get('targetLanguage', 'en')

    if not file_id:
        return Response(
            body={"error": "File ID is required."},
            status_code=400,
            headers={'Access-Control-Allow-Origin': '*'}
        )

    if mode not in ['full_text', 'structured']:
        return Response(
            body={"error": "Invalid mode. Choose 'full_text' or 'structured'."},
            status_code=400,
            headers={'Access-Control-Allow-Origin': '*'}
        )

    try:
        # Step 1: Extract text using TranscriptionService
        transcription_result = transcription_service.process_image(file_id)

        if "error" in transcription_result:
            return Response(
                body={"error": transcription_result["error"]},
                status_code=500,
                headers={'Access-Control-Allow-Origin': '*'}
            )

        # Step 2: Translate based on the mode
        translation_result = translation_service.process_text(
            text=transcription_result["extractedText"],
            mode=mode,
            source_language=source_language,
            target_language=target_language
        )

        if "error" in translation_result:
            return Response(
                body={"error": translation_result["error"]},
                status_code=500,
                headers={'Access-Control-Allow-Origin': '*'}
            )

        # Combine results and return
        response = {
            "fileId": file_id,
            "mode": mode,
            "transcriptionResult": transcription_result,
            "translationResult": translation_result
        }
        return Response(
            body=response,
            status_code=200,
            headers={'Access-Control-Allow-Origin': '*'}
        )

    except Exception as e:
        return Response(
            body={"error": f"Processing failed: {str(e)}"},
            status_code=500,
            headers={'Access-Control-Allow-Origin': '*'}
        )


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
        return Response(
            body={"error": "Text is required for speech synthesis."},
            status_code=400,
            headers={'Access-Control-Allow-Origin': '*'}
        )

    try:
        speech_url = speech_service.synthesize_speech(text, target_language)
        return Response(
            body={"speechUrl": speech_url},
            status_code=200,
            headers={'Access-Control-Allow-Origin': '*'}
        )
    except ValueError as ve:
        return Response(
            body={"error": str(ve)},
            status_code=400,
            headers={'Access-Control-Allow-Origin': '*'}
        )
    except RuntimeError as re:
        return Response(
            body={"error": str(re)},
            status_code=500,
            headers={'Access-Control-Allow-Origin': '*'}
        )
