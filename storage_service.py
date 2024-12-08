import boto3
import uuid


class StorageService:
    def __init__(self, storage_location):
        self.client = boto3.client('s3')
        self.bucket_name = storage_location

    def get_storage_location(self):
        return self.bucket_name

    def upload_file(self, file_bytes, original_file_name):
        # Generate a unique file ID and preserve the original file extension
        file_extension = original_file_name.split('.')[-1]  # Extract file extension
        file_id = f"{uuid.uuid4()}.{file_extension}"  # Unique file ID with extension

        # Upload the file to S3
        self.client.put_object(
            Bucket=self.bucket_name,
            Body=file_bytes,
            Key=file_id,
            ACL='public-read'
        )

        # Return the unique file ID and public file URL
        return {
            'fileId': file_id,
            'fileUrl': f"http://{self.bucket_name}.s3.amazonaws.com/{file_id}"
        }

    def get_file(self, file_name):
        # Retrieve the file content from S3
        response = self.client.get_object(Bucket=self.bucket_name, Key=file_name)
        return response['Body'].read().decode('utf-8')

    def make_file_public(self, uri):
        # Make a file in S3 publicly accessible
        parts = uri.split('/')
        key = parts[-1]
        bucket_name = parts[-2]

        self.client.put_object_acl(
            Bucket=bucket_name,
            Key=key,
            ACL='public-read'
        )
