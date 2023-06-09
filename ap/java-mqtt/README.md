# MQTT Javaサンプル
- AWS IoT Core, Amazon MQ等を使用してMQTTでメッセージを送受信するサンプル。
- 送受信するメッセージはProtocol Buffersで定義したメッセージを使用している

## ディレクトリ構成
`src/main/java` 以下にソースコードを配置。

```bash
.
├── java
│   ├── helper
│   │   └── MqttHelper.java # MQTTのヘルパークラス
│   ├── publish
│   │   └── PublishMain.java # パブリッシュ用のメインクラス
│   └── subscribe
│       └── SubscribeMain.java # サブスクライブ用のメインクラス
└── resources
    └── config.properties # 設定ファイル
```

## 実行方法
gradleタスクを定義しているので以下で実行可能
- パブリッシャー：`gradle publish`
- サブスクライバー：`gradle subscribe`


## 使用上の注意点
- `config.properties` には、MQTTのエンドポイント、トピック名、クライアントID、CA証明書、クライアント証明書、クライアント秘密鍵のパスを記述する。設定値を動的に切り替える仕組みは導入していないので、当該ファイルの書き換え必要。


