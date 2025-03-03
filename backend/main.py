import json
import boto3
from botocore.exceptions import ClientError
import base64
from datetime import datetime
import os
from google import genai
from google.genai import types
import pathlib
import re
import csv
import time

def init_gemini_client():
    set_gemini_apikey()
    global client
    if client is None:
        try:
            client = genai.Client(api_key=_gemini_apikey_cache)
        except Exception as e:
            print(f"Error initializing Gemini client: {e}")
            client = None




def lambda_handler(event, context):
    init_gemini_client()
    print("Received event:")
    print(f"{json.dumps(event)}")
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }
    
    try:
        body = event['body']
        if not body:
            raise ValueError("Request body is empty")
            
        try:
            decoded_body = base64.b64decode(body)
        except Exception as e:
            raise ValueError(f"Failed to decode base64 body: {str(e)}")
            
        try:
            json_body = json.loads(decoded_body)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON body: {str(e)}")
            
        if 'command' not in json_body:
            raise ValueError("Missing required 'command' field in request")
            
        command = json_body['command']
        content = json_body.get('content', "")
        
        print(f"command: {command}")
        print(f"content: {content}")
        

        command_result = command_dispatch(command, content)
        
        if command_result is False:
            raise ValueError(f"Invalid command: {command}")
            
        response_body = json.dumps(command_result)
        print(f"response_body: {response_body}")
        
        response = {
            'statusCode': 200 if 'msg' in command_result else 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': response_body
        }
        
    except ValueError as e:
        error_msg = str(e)
        print(f"Validation error: {error_msg}")
        response = {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET', 
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({'error': error_msg})
        }
    except Exception as e:
        error_msg = f"Internal server error: {str(e)}"
        print(f"Error: {error_msg}")
        response = {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({'error': error_msg})
        }
    
    return response

def command_dispatch(command, content):
    if command == "create_set":
        return create_set(content["name"], content["description"], content.get("filename", ""))
    elif command == "get_sets":
        return get_sets()
    elif command == "add_flashcard":
        return add_flashcard(content["set_name"], content["question"], content["answer"])
    elif command == "update_flashcard":
        return update_flashcard(content["set_name"], content["id"], content["question"], content["answer"])
    elif command == "delete_flashcard":
        return delete_flashcard(content["set_name"], content["id"])
    elif command == "delete_set_with_flashcards":
        return delete_set_with_flashcards(content["set_name"])
    elif command == "get_flashcards":
        return get_flashcards(content["set_name"])
    elif command == "suggest_flashcard_answer":
        return suggest_flashcard_answer(content["question"])
    elif command == "suggest_flashcards":
        return suggest_flashcards(content["set_name"])
    elif command == "import_flashcards_from_csv":
        return import_flashcards_from_csv(content["set_name"], content["filename"])
    elif command == "export_flashcards_to_csv":
        return export_flashcards_to_csv(content["set_name"])
    else:
        return False

def export_flashcards_to_csv(set_name):
    print(f"Exporting flashcards from set {set_name} to CSV file")
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('flashcards')
    response = table.scan(
        FilterExpression='#set = :set_name',
        ExpressionAttributeNames={
            '#set': 'set'
        },
        ExpressionAttributeValues={
            ':set_name': set_name
        }
    )
    flashcards = response['Items']
    if not flashcards:
        return {'msg': f'No flashcards found for set {set_name}'}
    
    filename = f'{set_name}_flashcards_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    tmp_filepath = f"/tmp/{filename}"
    with open(tmp_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Question', 'Answer'])
        for flashcard in flashcards:
            writer.writerow([flashcard['question'], flashcard['answer']])
    
    s3 = boto3.client('s3')
    bucket_name = 'flashcards-ai'
    try:
        result=s3.upload_file(tmp_filepath, bucket_name, "exports/" + filename)
        print(f"File {filename} uploaded successfully to S3 bucket {bucket_name}")
        print(f"Result: {result}")
    except ClientError as e:
        error_msg = f"Error uploading file to S3: {e.response['Error']['Message']}"
        print(error_msg)
        return {'error': error_msg}
    file_url = f'https://{bucket_name}.s3.amazonaws.com/exports/{filename}'
    return {
        'msg': f'Successfully exported flashcards to {filename}',
        'filename': filename,
        'file_url': file_url
    }
    

def import_flashcards_from_csv(set_name, filename):
    print(f"Importing flashcards from CSV file {filename} for set {set_name}")
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('flashcards')

    s3 = boto3.client('s3')
    try:
        response = s3.get_object(
            Bucket='flashcards-files',
            Key=filename
        )
        file_content = response['Body'].read().decode('utf-8')
        print(f"Successfully downloaded file {filename} from S3")
    except ClientError as e:
        error_msg = f"Error downloading file from S3: {e.response['Error']['Message']}"
        print(error_msg)
        return {'error': error_msg}

    tmp_filepath = f"/tmp/{filename}"
    pathlib.Path(tmp_filepath).write_text(file_content)
    print(f"File content written to {tmp_filepath}")

    with open(tmp_filepath, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            if len(row) < 2:
                print(f"Skipping invalid row: {row}")
                continue
            question, answer = row[0], row[1]
            print(f"Adding flashcard with question: {question} and answer: {answer[:20]}")

            time.sleep(0.01)
            id=int(round(datetime.now().timestamp() * 1000))
            print(f"Adding flashcard with id: {id}")
            response = table.put_item(Item={'set': set_name, 'id': id, 'question': question, 'answer': answer})
            print(f"Response: {response}")
    return {
        'msg': f'Successfully imported flashcards from {filename} to set {set_name}'
    }




def suggest_flashcard_answer(question):
    print(f"Suggesting flashcard answer for question {question}")

    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction='You are helping to answer the question in a flashcard. The answer should detailed, if possible also with code examples. All you answers must be in MD (markdown) format.',
            max_output_tokens= 8192,
            top_k= 2,
            top_p= 0.5,
            temperature= 0.1,
            response_mime_type= 'text/plain'
        ),
    )
    print(f"Response: {response}")
    return {
        'msg': response.text
    }

def add_flashcard(set_name, question, answer):
    print(f"Adding flashcard to set {set_name} with question {question} and answer {answer}")
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('flashcards')
    response = table.put_item(Item={'set': set_name,'id':int(round(datetime.now().timestamp())), 'question': question, 'answer': answer})
    return {
        'msg': f'Successfully added flashcard to set {set_name}'
    }

def update_flashcard(set_name, id, question, answer):
    print(f"Updating flashcard {id} in set {set_name} with question {question} and answer {answer}")
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('flashcards')
    response = table.update_item(Key={'set': set_name, 'id': id}, UpdateExpression='set question = :q, answer = :a', ExpressionAttributeValues={':q': question, ':a': answer})
    return {
        'msg': f'Successfully updated flashcard {id} in set {set_name}'
    }

def delete_flashcard(set_name, id):
    print(f"Deleting flashcard {id} in set {set_name}")
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('flashcards')
    response = table.delete_item(Key={'set': set_name, 'id': id})
    return {
        'msg': f'Successfully deleted flashcard {id} in set {set_name}'
    }

def get_flashcards(set_name):
    print(f"Getting flashcards for set {set_name}")
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('flashcards')
    response = table.query(
        KeyConditionExpression='#set = :set_name',
        ExpressionAttributeNames={
            '#set': 'set'
        },
        ExpressionAttributeValues={
            ':set_name': set_name
        }
    )
    for item in response['Items']:
        item['id'] = int(item['id'])
    print(f"Items: {response['Items']}")
    return {
        'msg': response['Items']
    }

def delete_set_with_flashcards(set_name):
    print(f"Deleting set {set_name} and all its flashcards")
    dynamodb = boto3.resource('dynamodb')
    
    # Delete all flashcards in the set
    flashcards_table = dynamodb.Table('flashcards')
    response = flashcards_table.query(
        KeyConditionExpression='#set = :set_name',
        ExpressionAttributeNames={
            '#set': 'set'
        },
        ExpressionAttributeValues={
            ':set_name': set_name
        }
    )
    
    # Delete each flashcard
    for item in response['Items']:
        flashcards_table.delete_item(
            Key={
                'set': set_name,
                'id': item['id']
            }
        )
    
    # Delete the set itself
    sets_table = dynamodb.Table('sets')
    sets_table.delete_item(
        Key={
            'name': set_name
        }
    )
    
    return {
        'msg': f'Successfully deleted set {set_name} and all its flashcards'
    }


def get_sets():
    print(f"Getting sets")
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('sets')
    response = table.scan()
    return {
        'msg': response['Items']
    }

def suggest_flashcards(set_name):
    print(f"Suggesting new flashcards for set {set_name}")
    dynamodb = boto3.resource('dynamodb')
    
    # Retrieve existing flashcards in the set
    flashcards_table = dynamodb.Table('flashcards')
    response = flashcards_table.query(
        KeyConditionExpression='#set = :set_name',
        ExpressionAttributeNames={
            '#set': 'set'
        },
        ExpressionAttributeValues={
            ':set_name': set_name
        }
    )
    
    existing_flashcards = response['Items']
    if not existing_flashcards:
        return {'msg': 'No existing flashcards found to base suggestions on.'}
    
    existing_flashcards_text = " ".join([f"Question: {card['question']}" for card in existing_flashcards])
    
    # Retrieve the set details to check if it has text content
    sets_table = dynamodb.Table('sets')
    set_response = sets_table.get_item(
        Key={
            'name': set_name
        }
    )
    
    # Initialize text variable
    text = ""
    
    # If content_path exists, try to load the text from S3
    if 'Item' in set_response and 'content_path' in set_response['Item'] and set_response['Item']['content_path'].strip():
        content_path = set_response['Item']['content_path']
        bucket_name, key = content_path.split('/', 1)
        
        try:
            s3 = boto3.client('s3')
            s3_response = s3.get_object(Bucket=bucket_name, Key=key)
            text = s3_response['Body'].read().decode('utf-8')
            print(f"Successfully loaded text from S3: {content_path}")
        except Exception as e:
            print(f"Error loading text from S3: {e}")
            # Continue without the file content
    
    # Prepare the prompt based on available information
    if text:
        question = f"Can you suggest more flashcards based on these existing flashcards: {existing_flashcards_text} and this additional text: {text}?"
    else:
        question = f"Can you suggest more flashcards based on these existing flashcards: {existing_flashcards_text}? Create new flashcards that expand on the topics covered in the existing ones."
    
    print(f"Generating flashcards with prompt: {question[:100]}...")
    
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=[question],
        config=types.GenerateContentConfig(
            system_instruction='You are helping to prepare a set of flashcards. The flashcards should be put in tag <flashcard> and </flashcard>. Each flashcard should have a question and answer. The question should be put in tag <question> and </question>. The answer should be put in tag <answer> and </answer>. The answer should be detailed, if possible also with code examples. All your answers must be in MD (markdown) format. Create flashcards that are different from the existing ones but related to the same topics.',
            max_output_tokens=8192,
            top_k=2,
            top_p=0.5,
            temperature=0.1,
            response_mime_type='text/plain'
        ),
    )

    print(f"Response received, parsing flashcards...")
    
    # Parse suggested flashcards from response text
    suggested_flashcards = []
    pattern = r'<flashcard>(.*?)</flashcard>'
    matches = re.findall(pattern, response.text, re.DOTALL)
    
    for match in matches:
        question_match = re.search(r'<question>(.*?)</question>', match, re.DOTALL)
        answer_match = re.search(r'<answer>(.*?)</answer>', match, re.DOTALL)
        if question_match and answer_match:
            suggested_flashcards.append({
                'question': question_match.group(1).strip(),
                'answer': answer_match.group(1).strip()
            })
    
    print(f"Found {len(suggested_flashcards)} suggested flashcards")
    
    # Persist new flashcards in the set
    table = dynamodb.Table('flashcards')
    for flashcard in suggested_flashcards:
        try:
            table.put_item(
                Item={
                    'set': set_name,
                    'id': int(round(datetime.now().timestamp())),
                    'question': flashcard['question'],
                    'answer': flashcard['answer']
                }
            )
        except Exception as e:
            print(f"Error persisting flashcard: {e}")
            return {'msg': f'Error persisting flashcards: {str(e)}'}
    
    return {
        'msg': f"Successfully added {len(suggested_flashcards)} new flashcards"
    }

def create_flashcards_from_file(set_name, filename):
    print(f"Creating flashcards from file {filename} for set {set_name}")
    # Load file from S3 bucket
    s3 = boto3.client('s3')
    try:
        response = s3.get_object(
            Bucket='flashcards-files',
            Key=filename
        )
        file_content = response['Body'].read()
        print(f"Successfully loaded file {filename} from S3")
    except ClientError as e:
        error_msg = f"Error loading file from S3: {e.response['Error']['Message']}"
        print(error_msg)
        return {'error': error_msg}

    file_content_str = file_content.decode('utf-8')
    tmp_filepath = f"/tmp/{filename}"
    pathlib.Path(tmp_filepath).write_text(file_content_str)
    print(f"File content written to {tmp_filepath}")
    my_file = client.files.upload(file=tmp_filepath)
    print(f"File uploaded to Gemini: {my_file}")
    question = f"Can you prepare flashcards based on this file: {filename}?"
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=[question,my_file],
        config=types.GenerateContentConfig(
            system_instruction='You are helping to prepare a set flashcards based on given text. The flashcards should be put in tag <flashcard> and </flashcard>. Each flashcard should have a question and answer. The question should be put in tag <question> and </question>. The answer should be put in tag <answer> and </answer>. The answer should detailed, if possible also with code examples. All you answers must be in MD (markdown) format.',
            max_output_tokens= 8192,
            top_k= 2,
            top_p= 0.5,
            temperature= 0.1,
            response_mime_type= 'text/plain'
        ),
    )


    print(f"Response text: {response.text}")
    print("\n"*5)
    # Parse flashcards from response text
    flashcards = []
    flashcard_parts = []
    
    # Find all flashcard tags
    pattern = r'<flashcard>(.*?)</flashcard>'
    matches = re.findall(pattern, response.text, re.DOTALL)
    
    for match in matches:
        # Extract question and answer from each flashcard
        question_pattern = r'<question>(.*?)</question>'
        answer_pattern = r'<answer>(.*?)</answer>'
        question_match = re.search(question_pattern, match, re.DOTALL)
        answer_match = re.search(answer_pattern, match, re.DOTALL)
        
        if question_match and answer_match:
            question = question_match.group(1).strip()
            answer = answer_match.group(1).strip()
            flashcard_parts = [question, answer]
            flashcards.append(flashcard_parts)
    print(f"Flashcards: {len(flashcards)}")
    for flashcard in flashcards:
        add_flashcard(set_name, flashcard[0], flashcard[1])



def create_set(name, description="", filename=""):
    # Create a DynamoDB resource
    print(f"Creating set with name: {name} and description: {description} and filename: {filename}")
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('sets')
    
    try:
        # Create new set item
        item = {
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat(),
        }
        
        # If a filename was provided, store the content path
        if filename and len(filename) > 0:
            # Store the S3 path to the file content
            item['content_path'] = f"flashcards-files/{filename}"
            
        response = table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(#n)",
            ExpressionAttributeNames={
                "#n": "name"
            }
        )
        
        if filename and len(filename) > 0:
            create_flashcards_from_file(name, filename)

        return {
            'msg': f'Successfully created set {name} with description {description}'
        }
    except ClientError as e:
        error_msg = f"Error creating set: {e.response['Error']['Message']}"
        print(error_msg)
        return {'error': error_msg}

client = None
# Cache for storing the API key
_gemini_apikey_cache = None

MODEL_NAME="gemini-2.0-flash"


def set_gemini_apikey():
    global _gemini_apikey_cache
    if _gemini_apikey_cache is None:
        _gemini_apikey_cache=json.loads(load_gemini_apikey())['GEMINI_API_KEY']

def load_gemini_apikey():
    print("Loading Gemini API key")
    secret_name = "gemini_apikey"
    region_name = "eu-central-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    return get_secret_value_response['SecretString']

    # Your code goes here.

def __main__():
    response = suggest_flashcard_answer("What is the capital of France?")
    print(response)

if __name__ == "__main__":
    __main__()