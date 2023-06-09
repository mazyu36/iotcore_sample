import argparse
from time import sleep
from datetime import datetime, timedelta, timezone
from google.protobuf.timestamp_pb2 import Timestamp
# プロトコルバッファから生成したクラスをインポート
from proto.dummy_telemetry_pb2 import DummyTelemetry
# mqtt_helperからMQTTHelperクラスをインポート
from mqtt_helper import MQTTHelper


def create_message(client_name="dummy"):
    # ダミーテレメトリオブジェクトを作成
    dummy_telemetry = DummyTelemetry()

    # idおよび緯度経度を設定
    dummy_telemetry.id = client_name
    dummy_telemetry.latitude = 35.681236
    dummy_telemetry.longitude = 139.767125

    # 現在時刻JSTを設定
    JST = timezone(timedelta(hours=+9), 'JST')
    now = datetime.now(JST)
    timestamp = Timestamp()
    timestamp.FromDatetime(now)
    dummy_telemetry.timestamp.CopyFrom(timestamp)

    # メッセージのシリアライズ
    serialized_message = dummy_telemetry.SerializeToString()

    return serialized_message


def on_publish(client, userdata, mid):
    print("publish: {0}".format(mid))


def main():
    # argparseの設定
    parser = argparse.ArgumentParser(description='MQTT Publisher')

    # client_nameはコマンドライン引数から取得。未指定の場合は"dummy_client"を設定
    parser.add_argument('--client_name', type=str, default="dummy_client", help='client name')

    # broker_typeはコマンドライン引数から取得。未指定の場合は"localhost"を設定
    parser.add_argument('--broker_type',
                        choices=['localhost', 'amazonmq', 'iotcore'],
                        default='localhost',
                        help='select broker type. localhost or amazonmq or iotcore')

    # コマンドライン引数をパース
    args = parser.parse_args()

    # クライアントネームをコマンドライン引数から取得
    client_name = args.client_name

    # env
    broker_type = args.broker_type

    # トピック名
    topic = f"python/messages/{client_name}"

    # MQTTの接続設定
    mqtt_helper = MQTTHelper(client_name=client_name, broker_type=broker_type)

    # コールバック関数の設定
    mqtt_helper.set_on_publish_callback(on_publish)

    # Willメッセージの設定
    # will_topic = f"python/messages/will/{client_name}"
    # will_message = "Connection aborted"
    # mqtt_helper.set_will_message(topic=will_topic,
    #                              payload=will_message,
    #                              retain=False)

    # MQTTブローカーへの接続
    mqtt_helper.connect()

    try:
        while True:
            # 送信するメッセージの作成
            publish_message = create_message(client_name=client_name)

            # メッセージの送信
            mqtt_helper.publish(topic=topic,
                                payload=publish_message,
                                retain=False)

            sleep(2)

    except KeyboardInterrupt:
        # キーボード割り込みが発生した場合
        # mqtt_helper.disconnect()
        pass


if __name__ == '__main__':
    main()
