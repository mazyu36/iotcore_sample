# MQTT Pythonサンプル
AWS IoT Core, Amazon MQ等を使用してMQTTでメッセージを送受信するサンプル。

## ディレクトリ構成

```bash
.
├── Makefile # protoファイルコンパイル用のMakefile
├── README.md
├── config.ini # 設定ファイル
├── mqtt_helper.py # MQTTのヘルパークラス
├── proto # protoファイルをコンパイルしたもの
│   ├── dummy_commad_pb2.py
│   └── dummy_telemetry_pb2.py
├── publisher.py # パブリッシャーのサンプル
└── subscriber.py # サブスクライバーのサンプル
```

## 実行方法
- パブリッシャー: `python publisher.py --client_id <client_id> --broker_type <broker_type> `
- サブスクライバー: `python subscriber.py --client_id --broker_type <broker_type>`
- broker_typeは以下の3つを指定
  - `localhost`：ローカルで起動したMosquittoブローカーを使用。クライアント証明書で認証を行う。
  - `iotcore`：AWS IoT Coreと接続する場合。クライアント証明書で認証を行う。
## 使用上の注意点
- `config.ini` には、MQTTのエンドポイント、トピック名、クライアントID、CA証明書、クライアント証明書、クライアント秘密鍵のパスを記述する。
  - コマンドライン引数の`broker_type`で、設定値を切り替えることが可能。
- `.proto`を更新した場合は、`make`を行うことで`proto`ディレクトリ以下にコンパイルしたファイルが生成される。
    - `iotcore`：AWS IoT Coreのブローカーと接続する場合。クライアント証明書で認証を行う。