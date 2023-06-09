import argparse
from datetime import datetime, timedelta, timezone

from proto.dummy_commad_pb2 import DummyCommand
import proto.dummy_commad_pb2 as dummy_commad_pb2
# mqtt_helperからMQTTHelperクラスをインポート
from mqtt_helper import MQTTHelper


def on_message(client, userdata, msg):
    # ダミーコマンドオブジェクトを作成
    message = DummyCommand()

    # タイムゾーンの生成
    JST = timezone(timedelta(hours=+9), 'JST')

    # メッセージのデシリアライズ
    message.ParseFromString(msg.payload)

    # TimestampをDateに変換
    unix_timestamp = message.timestamp.seconds
    nanos = message.timestamp.nanos
    datetime_object = datetime.fromtimestamp(unix_timestamp, JST)
    datetime_object += timedelta(milliseconds=nanos // 1000000)  # ミリ秒を追加

    # トピック名をプリント
    print("##### Topic:")
    print(msg.topic)
    print()

    # デシリアライズ前のメッセージを表示
    print("##### Received message:")
    print(f'Received Message:{msg} with Qos{msg.qos}')

    # 改行
    print()

    print("##### Deserialized message:")
    print(message)

    # CommandTypeのキーを取得して表示
    command_key = dummy_commad_pb2.CommandType.Name(message.commandType)
    print(f'Command: value:{message.commandType}, name:{command_key}')

    # TimestampはDateに変換
    print(f'Timestamp:{datetime_object.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]}')

    # 改行
    print()


def main():
    # argparseの設定
    parser = argparse.ArgumentParser(description='MQTT Subscriber')

    # client_nameはコマンドライン引数から取得。未指定の場合は"dummy_client"を設定
    parser.add_argument('--client_name', type=str, default="python-subscriber", help='client name')

    # broker_typeはコマンドライン引数から取得。未指定の場合は"localhost"を設定
    parser.add_argument('--broker_type',
                        choices=['localhost', 'amazonmq', 'iotcore'],
                        default='localhost',
                        help='select broker type. localhost or amazonmq or iotcore')

    # コマンドライン引数をパース
    args = parser.parse_args()

    # クライアントネームをコマンドライン引数から取得
    client_name = args.client_name

    # broker_typeをコマンドライン引数から取得
    broker_type = args.broker_type

    # トピック名
    topic = "java/messages/#"

    # MQTTの接続設定
    mqtt_helper = MQTTHelper(client_name=client_name, broker_type=broker_type)

    # MQTTブローカーへの接続
    mqtt_helper.connect()

    # コールバック関数の設定
    mqtt_helper.set_on_message_callback(on_message)

    # 購読の開始
    mqtt_helper.subscribe(topic=topic)  # subscribeをここに移動

    try:
        while True:
            # メインの処理を続ける
            pass
    except KeyboardInterrupt:
        mqtt_helper.disconnect()


if __name__ == '__main__':
    main()
