import boto3
import json
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Studentslatest')

polly = boto3.client('polly')
s3 = boto3.client('s3')

BUCKET_NAME = 'student-audio-files-sahil-latets'

def lambda_handler(event, context):

    # Get all students
    response = table.scan()
    students = response.get('Items', [])

    # Filter valid students
    valid_students = []
    for s in students:
        if 'CreatedAt' in s and s['CreatedAt']:
            valid_students.append(s)

    # If no students found
    if len(valid_students) == 0:
        return {
            "statusCode": 404,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "*"
            },
            "body": json.dumps("No valid students found")
        }

    # Find latest student
    latest_student = max(
        valid_students,
        key=lambda x: datetime.fromisoformat(x['CreatedAt'])
    )

    name = latest_student.get('Name', '')
    dept = latest_student.get('Department', '')

    # Create message
    message = f"The latest student is {name} from {dept} department."

    # Convert text to speech using Polly
    polly_response = polly.synthesize_speech(
        Text=message,
        OutputFormat='mp3',
        VoiceId='Joanna'
    )

    audio_stream = polly_response['AudioStream'].read()

    # Save MP3 to S3
    file_name = f"latest_student_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=file_name,
        Body=audio_stream,
        ContentType='audio/mpeg'
    )

    # Return response with CORS headers
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        },
        "body": json.dumps({
            "student": latest_student,
            "message": message,
            "audio_file": file_name
        })
    }
