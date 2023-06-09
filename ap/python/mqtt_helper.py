import ssl
import paho.mqtt.client as mqtt
import configparser


class MQTTHelper:
    def __init__(self, client_name, broker_type):
        # クライアント名を設定
        self.client_name = client_name

        # Configファイルの読み込み
        config = configparser.ConfigParser()
        config.read('config.ini')

        # brokerのホスト名を設定
        self.broker_host = config.get(broker_type, "broker_host")

        # QoSの設定
        self.qos = int(config.get(broker_type, "qos"))

        # 各種証明書、認証情報は設定がある場合のみ値を格納。未設定の場合はNoneとする。
        self.cafile = config.get(broker_type, "ca_file") if config.has_option(broker_type, 'ca_file') else None
        self.certfile = config.get(broker_type, "cert_file") if config.has_option(broker_type, 'cert_file') else None
        self.keyfile = config.get(broker_type, "key_file") if config.has_option(broker_type, 'key_file') else None
        self.username = config.get(broker_type, "username") if config.has_option(broker_type, 'username') else None
        self.password = config.get(broker_type, "password") if config.has_option(broker_type, 'password') else None

        # MQTTクライアントの作成
        self.client = mqtt.Client(protocol=mqtt.MQTTv311, client_id=self.client_name, clean_session=None)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flag, rc):
        print("Connected with result code " + str(rc))

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print("Unexpected disconnection.")

    def set_on_publish_callback(self, callback):
        # コールバック関数の設定
        self.client.on_publish = callback

    def set_on_message_callback(self, callback):
        # コールバック関数の設定
        self.client.on_message = callback

    def set_will_message(self, topic, payload, retain=False):
        # Willメッセージの設定
        self.client.will_set(topic, payload, self.qos, retain)

    def publish(self, topic, payload=None, retain=False):
        # トピック名とメッセージを指定して送信
        self.client.publish(topic, payload, self.qos, retain)

    def subscribe(self, topic):
        # トピック名とQoSを指定して購読を開始
        self.client.subscribe(topic, self.qos)

    def connect(self):
        # SSL/TLSのコンテキストを作成
        context = ssl.create_default_context()

        # 自己証明書、クライアント証明書、秘密鍵のパスが設定されている場合は、コンテキストに設定
        if self.cafile:
            context.load_verify_locations(cafile=self.cafile)

        if self.certfile and self.keyfile:
            context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)

        # TLSのバージョンを指定
        self.client.tls_set_context(context=context)

        # ユーザー名とパスワードが設定されている場合は、ユーザー名とパスワードを設定
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        # MQTTブローカーへの接続
        self.client.connect(self.broker_host, 8883, 60)

        # ループ処理を開始
        self.client.loop_start()

    def disconnect(self):
        # ループ処理を停止
        self.client.loop_stop()

        # MQTTブローカーとの接続を切断
        self.client.disconnect()
