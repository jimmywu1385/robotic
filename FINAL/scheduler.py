from os import environ
from boto3 import resource, client
from boto3.dynamodb.conditions import Key
from datetime import timedelta, datetime, timezone
from decimal import Decimal
import uuid
import json
import re
import dateutil.parser

# This is used to calculate the partition key, based of the current time, to find scheduled jobs correctly
partition_interval_in_minutes = 5

dynamodb_table = resource('dynamodb').Table(environ['TABLE_NAME'])
eventbridge_client = client('events')

def lambda_handler(event, context):
    event_time_in_utc = event['time']
    #print(type(event_time_in_utc))
    previous_partition, current_partition = get_partitions(event_time_in_utc)

    previous_jobs = query_jobs(previous_partition, event_time_in_utc)
    current_jobs = query_jobs(current_partition, event_time_in_utc)
    all_jobs = previous_jobs + current_jobs

    print('dispatching {} jobs'.format(len(all_jobs)))

    put_all_jobs_into_event_bridge(all_jobs)
    delete_all_jobs(all_jobs)
    recordTime(all_jobs)

    print('dispatched and deleted {} jobs'.format(len(all_jobs)))

def recordTime(jobs) :
    dynamodb = resource('dynamodb')
    table = dynamodb.Table('testTable')
    
    tz = timezone(timedelta(hours=+8))
    date_ymd, h, m, _a, _b = re.split('T|:', datetime.now(tz).isoformat());
    
    for job in jobs:
        if job['detail']['task'] == 'feed' or job['detail']['task'] == 'water':
            print(job['detail']['pet'])
            response = table.update_item(
                Key={
                    "pet": job['detail']['pet']
                },
                UpdateExpression= "SET #a = :vals",
                ExpressionAttributeNames={
                    "#a": "RECORD"
                },
                ExpressionAttributeValues={
                    ":vals": [date_ymd, h+':'+m]
                }    
            )
            return response

def put_all_jobs_into_event_bridge(jobs): #to SQS
    for job in jobs:
        sqs = client('sqs')
        queue_url = 'https://sqs.ap-northeast-1.amazonaws.com/739183738838/pizzaQueue.fifo'
        # Send message to SQS queue
        #ID = str(random.randint(0,99))
        #time.sleep(2)
        response = sqs.send_message(
            QueueUrl=queue_url,
            #DelaySeconds=1,
            MessageAttributes={
                'pet': {
                    'DataType': 'String',
                    'StringValue': job['detail']['pet']
                },
                'task': {
                    'DataType': 'String',
                    'StringValue': job['detail']['task']
                }
            },
            MessageBody=(
                str(uuid.uuid4())
            ),
            #MessageDeduplicationId=ID,
            MessageGroupId="Group1"
        )
        print(response['MessageId'])
        
        # eventbridge_client.put_events(
        #     Entries=[
        #         {
        #             'DetailType': job['detail_type'],
        #             'Detail': convert_dynamodb_object_to_json(job['detail']),
        #             'Source': 'Scheduler',
        #             'EventBusName': environ['EVENT_BRIDGE_NAME'],
        #         }
        #     ]
        # )


def delete_all_jobs(all_jobs):
    for job in all_jobs:
        dynamodb_table.delete_item(
            Key={
                'pk': job['pk'],
                'sk': job['sk']
            }
        )


def query_jobs(pk, upper_bound_sk):
    response = dynamodb_table.query(
        KeyConditionExpression=Key('pk').eq(
            'j#' + pk) & Key('sk').lte(upper_bound_sk),
    )
    return response['Items']


# calculate the previous and current partitions based on the event time and partition interval
def get_partitions(event_time_in_utc):
    date_hour, strminute, *_ = event_time_in_utc.split(':')
    minute = int(strminute)
    current_partition = f'{date_hour}:{(minute - minute % partition_interval_in_minutes):02d}'
    current_partition_date_time = dateutil.parser.parse(current_partition)
    previous_partition_date_time = current_partition_date_time - \
        timedelta(minutes=partition_interval_in_minutes)
    previous_partition = previous_partition_date_time.strftime(
        '%Y-%m-%dT%H:%M')

    return previous_partition, current_partition


def convert_dynamodb_object_to_json(value):
    return json.dumps(value, cls=DynamoDBTypeEncoder)


class DynamoDBTypeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 > 0:
                return float(obj)
            else:
                return int(obj)
        if isinstance(obj, set):
            return list(obj)
        return super(DynamoDBTypeEncoder, self).default(obj)
