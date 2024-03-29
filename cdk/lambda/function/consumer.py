import boto3
import json
import base64
import os


database_name = os.environ['DATABASE_NAME']
table_name = os.environ['TABLE_NAME']


def handler(event, context):
    timestream_client = boto3.client('timestream-write')

    # ペイロードを受信
    for record in event['Records']:
        data = json.loads(base64.b64decode(record['kinesis']['data']).decode('utf-8'))
        payload = data["payload"]

        # ディメンションの設定
        dimensions = [
            {'Name': 'id', 'Value': payload['id']},
            {'Name': 'timestamp', 'Value': str(payload['timestamp'])}
        ]

        records = []

        latitude = {
            'Name': 'latitude',
            'Value': str(payload['latitude']),
            'Type': 'DOUBLE'
        }

        longitude = {
            'Name': 'longitude',
            'Value': str(payload['longitude']),
            'Type': 'DOUBLE'
        }

        records.append(latitude)
        records.append(longitude)

        # マルチメジャーレコードのデータポイントの作成
        data_point = {
            'Time': str(payload['timestamp']),
            'TimeUnit': 'MILLISECONDS',
            'MeasureName': 'device_metrics',
            'MeasureValueType': 'MULTI',
            'MeasureValues': records,
            'Dimensions': dimensions
        }
        print(data_point)

        # データポイントを書き込む
        try:
            response = timestream_client.write_records(
                DatabaseName='TelemetryDatabase',
                TableName='TelemetryTable',
                Records=[data_point]
            )
            print(response)
        except Exception as e:
            print(f'Error writing records to Timestream: {str(e)}')
            rejected_records = e.response['RejectedRecords']
            # 拒否されたレコードの詳細を処理
            for record in rejected_records:
                print(record)

    return {
        'statusCode': 200,
        'body': 'Records processed successfully'
    }