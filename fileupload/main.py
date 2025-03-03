import json
import boto3
from botocore.exceptions import ClientError
import base64
from datetime import datetime
import os



def lambda_handler(event, context):
    print(f"File upload event received. Body present: {event['body'] is not None}")
    body = base64.b64decode(event['body'])
    # Parse the multipart form data to extract file content
    try:
        # Find boundary in content type
        content_type = event['headers'].get('content-type', '')
        boundary = content_type.split('boundary=')[1]
        
        # Split body into parts using boundary
        parts = body.split(('--' + boundary).encode())
        
        # Find the file content part
        file_content = None
        for part in parts:
            if b'Content-Type' in part and b'filename' in part:
                # Extract content after headers (double newline)
                headers_end = part.find(b'\r\n\r\n')
                if headers_end > 0:
                    file_content = part[headers_end + 4:]
                break
                
        if not file_content:
            raise ValueError("No file content found in request")

        # Generate unique filename using timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Determine file extension based on content type
        file_extension = 'txt'  # Default to .txt if content type is not found
        for part in parts:
            if b'Content-Type' in part:
                content_type_line = part.split(b'\r\n')[1]
                content_type = content_type_line.split(b': ')[1].decode()
                if 'text/plain' in content_type:
                    file_extension = 'txt'
                elif 'application/pdf' in content_type:
                    file_extension = 'pdf'
                elif 'image/jpeg' in content_type:
                    file_extension = 'jpg'
                elif 'image/png' in content_type:
                    file_extension = 'png'
                elif 'text/csv' in content_type:
                    file_extension = 'csv'
                break

        filename = f'upload_{timestamp}.{file_extension}'

        # Upload to S3
        s3 = boto3.client('s3')
        s3.put_object(
            Bucket='flashcards-files',
            Key=filename,
            Body=file_content
        )
        
        print(f"File {filename} uploaded successfully")
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'message': 'File uploaded successfully',
                'location': {
                    'bucket': 'flashcards-files',
                    'key': filename
                }
            })
        }
    except Exception as e:
        print(f"Error processing upload: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*', 
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps(f'Error uploading file: {str(e)}')
        }
