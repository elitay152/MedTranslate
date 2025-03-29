# 🩺 MedTranslate API

MedTranslate is a serverless REST API built with AWS Chalice to support multilingual medical communication. It allows users to upload medical documents, extract and translate text, and convert translations into speech.

#### 🚀 Key Features
Upload medical files to S3
Extract text via OCR (image-to-text)
Translate content between languages
Synthesize speech for accessibility
Serverless with AWS Chalice + Lambda

#### 📦 Stack
Framework: AWS Chalice (Python)
Storage: Amazon S3
Text Extraction: OCR (e.g., Textract/Tesseract)
Translation: Custom or API-based (e.g., DeepL)
Speech: Amazon Polly or equivalent

#### 📚 Endpoints
PUT /upload/{file_name}
Upload a file to S3

POST /process
Extract and translate text
Body: {"fileId": "...", "mode": "full_text", "sourceLanguage": "auto", "targetLanguage": "en"}

POST /synthesize
Convert text to speech
Body: {"text": "...", "targetLanguage": "en"}
  
#### ✅ Use Case
Ideal for healthcare scenarios where documents need to be translated and spoken aloud for patients with limited English proficiency or literacy.

