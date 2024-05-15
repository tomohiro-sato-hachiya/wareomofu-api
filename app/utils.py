import boto3
import os
import json
from . import const

def get_skip(limit: int, page: int) -> int:
    if limit < 1:
        limit = 100
    if page < 1:
        page = 1
    skip = limit * (page - 1)
    return skip


def get_not_found_message(subject: str) -> str:
    return f'{subject}が存在しないか、公開停止しています'


def get_username(access_token: str) -> str:
    client = boto3.client('cognito-idp')
    user = client.get_user(AccessToken=access_token)
    return user['Username']


def send_email_notification(username: str, subject: str, main: str):
    with open(f'{const.SES_TEMPLATE_DIRECTORY}/header.txt', 'r') as f:
        header_template = f.read()
    header = header_template.format(username)
    with open(f'{const.SES_TEMPLATE_DIRECTORY}/footer.txt', 'r') as f:
        footer = f.read()
    message = f'{header}\n\n{main}\n\n{footer}'
    sqs = boto3.client('sqs')
    queue_url = sqs.get_queue_url(QueueName=os.environ['EMAIL_TO_USER_QUEUE'])['QueueUrl']
    encode = lambda value : value.encode('utf-8').hex()
    body = {
        'username': encode(username),
        'subject': encode(subject),
        'message': encode(message),
    }
    jsoned_body = json.dumps(body)
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=jsoned_body
    )
    print(f'send email to {username}\nresponse:{response}')
