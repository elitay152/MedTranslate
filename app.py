from chalice import Chalice, Response
from chalicelib import storage_service
from chalicelib import transcription_service
from chalicelib import translation_service
import json

####
# chalice app configuration
#####
app = Chalice(app_name='MedTranslate')
app.debug = True

#####
# services initialization
#####
storage_location = 'medtranslate-storage'
storage_service = storage_service.StorageService(storage_location)
transcription_service = transcription_service.TranscriptionService(storage_service)
translation_service = translation_service.FlexibleProcessingService(storage_service)


@app.route('/upload', methods=['POST'], content_types=['multipart/form-data'])
def upload_file():
    """
    Endpoint to upload a file to S3 and return its file ID.
    """
    request = app.current_request
    form_data = request.raw_body

    # Parse multipart form data
    content_type = request.headers['content-type']
    boundary = content_type.split("boundary=")[-1]
    parsed_form = parse_multipart(form_data, boundary)

    # Extract file bytes and name
    if 'file' not in parsed_form:
        return Response(body={"error": "No file part in the request"}, status_code=400)

    file_data = parsed_form['file']
    original_file_name = file_data.filename
    file_bytes = file_data.read()

    try:
        # Upload the file to S3
        result = storage_service.upload_file(file_bytes, original_file_name)
        return {"fileId": result['fileId'], "fileUrl": result['fileUrl']}
    except Exception as e:
        return Response(body={"error": f"File upload failed: {str(e)}"}, status_code=500)


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
        return result
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
        translation_result = translation_service.translate_text(text, source_language, target_language)
        return translation_result
    except Exception as e:
        return Response(body={"error": f"Translation failed: {str(e)}"}, status_code=500)


def parse_multipart(form_data, boundary):
    """
    Utility function to parse multipart form-data for Chalice.
    """
    from werkzeug.formparser import parse_form_data
    from io import BytesIO

    env = {
        'REQUEST_METHOD': 'POST',
        'CONTENT_TYPE': f'multipart/form-data; boundary={boundary}',
        'wsgi.input': BytesIO(form_data)
    }
    return parse_form_data(env)[1]
