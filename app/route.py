from time import time
from datetime import datetime
import pytz
import json
from typing import Callable
from fastapi import Request, Response
from fastapi.routing import APIRoute
import hashlib
import uuid
import boto3
from . import utils


class LoggingContextRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            ignore_paths = [
                '/'
            ]
            response = {}
            if request.url.path not in ignore_paths:
                before = time()
                response: Response = await original_route_handler(request)
                duration = round(time() - before, 4)

                record = {}
                time_local = datetime.fromtimestamp(before)
                time_local = pytz.timezone('Asia/Tokyo').localize(time_local)
                record['created_at'] = time_local.strftime('%Y-%m-%d %H:%M:%S%Z')
                timestamp = f'{datetime.timestamp(time_local)}-{uuid.uuid4()}'
                record['timestamp'] = timestamp
                record['username'] = 'cannot_identify'
                record['request_body'] = {}
                secret = '*****'
                if await request.body():
                    request_body = json.loads((await request.body()).decode('utf-8'))
                    for key, value in request_body.items():
                        if key == 'access_token':
                            try:
                                username = utils.get_username(value)
                                hashed_username = hashlib.sha256(username.encode()).hexdigest()
                                record['username'] = hashed_username
                            except Exception as e:
                                print(e)
                            record['request_body'][key] = secret
                        else:
                            record['request_body'][key] = value
                record['request_headers'] = {
                    k.decode('utf-8'): v.decode('utf-8') for (k, v) in request.headers.raw
                }
                record['remote_addr'] = request.client.host
                record['request_uri'] = request.url.path
                record['request_method'] = request.method
                record['request_time'] = str(duration)
                record['status'] = response.status_code
                record['response_body'] = response.body.decode('utf-8')
                record['response_headers'] = {
                    k.decode('utf-8'): v.decode('utf-8') for (k, v) in response.headers.raw
                }
                try:
                    table_name = 'wareomofu_api_access_logs'
                    dynamodb = boto3.resource('dynamodb')
                    dynamodb_table = dynamodb.Table(table_name)
                    dynamodb_table.put_item(Item=record)
                except Exception as e:
                    print(e)
            return response

        return custom_route_handler