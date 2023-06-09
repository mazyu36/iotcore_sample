from custom import dummy_telemetry_pb2
import base64


def handler(event, context):
    telemetry = dummy_telemetry_pb2.DummyTelemetry()

    print(event)
    data = event["data"]

    payload_data_decoded = base64.b64decode(data)

    telemetry.ParseFromString(payload_data_decoded)

    # Protocol BuffersのTimestampオブジェクトをUNIXエポック時間（ms）に変換
    timestamp_value = telemetry.timestamp.ToMilliseconds()

    # JSONに変換するための辞書を作成
    data = {
        "id": telemetry.id,
        "latitude": telemetry.latitude,
        "longitude": telemetry.longitude,
        "timestamp": timestamp_value
    }

    print(data)

    return data
