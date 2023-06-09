# MQTTサンプル
Java, PythonでMQTT通信を行うサンプルアプリ、および関連するAWSアーキテクチャを構築するAWS CDKのコードを格納

## サンプルアプリ(MQTT Client)について
Java, PythonでそれぞれPublisherとSubscriberを作成。なお送受信するメッセージはProtocol Buffersを使用している。

python側はTelemetryを配信するIoTデバイス、Java側はIoTデバイスに対してCommandを送信するサーバーをイメージして作成している。

* Python(publisher)-Java(subscriber)：pythonからはDummy Telemetryを配信する。Javaではワイルドカードを使用してDummy Telemetryのトピックを全てsubscribeする。
* Java(publisher)-Python(subscriber)：JavaからDummy Commandを配信し、Python側でsubscribeする。


## アーキテクチャ
![構成](architecture.drawio.svg)

大きくはクライアント、MQTTブローカー（localhost, AWS）、AWSデータ基盤の3つの要素から成る。

* クライアント：Java, Python。それぞれPublisher, Subscriberを実装。送受信するメッセージはProtocol Buffersで定義する。
* MQTTブローカー：クライアントのアプリ（Java/Python）を用いて通信するためのブローカー
  * mosquitto：ローカルでアプリ開発時に使用することを想定。docker composeで起動する。クライアント証明書で認証を行う。
  * AWS IoT Core：クライアント証明書で認証を行う。
* AWSデータ基盤：Client(Device)から配信されたTelemetry(protobuf)をデシリラライズし、Amazon Timestreamに格納するデータ基盤を構築。


## ディレクトリ構成
以下の通り。

```bash
.
├── README.md
├── ap
│   ├── compose.yaml # Mosquittoブローカーを起動するためのDocker Composeファイル
│   ├── iotcore
│   ├── java-mqtt # JavaでMQTTを使用するサンプル
│   ├── mosquitto # Mosquittoブローカーの設定ファイルを格納
│   ├── proto # .protoファイルを格納
│   └── python # PythonでMQTTを使用するサンプル
└── cdk # CDKのコードを格納
```

## mosquittoを立ち上げるための準備
ローカルでmosquittoによるMQTTブローカーを構築し、証明書認証を行うにあたり各種証明書や秘密鍵の作成が必要である。

1. CA証明書（自己署名証明書）の作成。
2. mosquitto（サーバー）のCSR、秘密鍵および証明書を作成。
3. クライアントのCSR、秘密鍵および証明書を作成。クライアント証明書を使わない場合は不要。
4. mosquittoの設定ファイルを作成してコンテナを起動。

以下流れを記載する。なおコマンドは全て`ap`配下で実施することを想定している。

### 1.CA証明書（自己証明書）の作成:

```bash
openssl req -new -x509 -days 365 -nodes -subj "/CN=MyRootCA" -keyout mosquitto/config/certs/ca.key -out mosquitto/config/certs/ca.crt
```
**説明:**
- `openssl req`: OpenSSLコマンドで証明書署名要求（CSR）や自己署名証明書を作成するために使用されるコマンド。
- `-new`: 新しい証明書署名要求を作成するオプション。
- `-x509`: 自己署名証明書（CA証明書）を作成するオプション。
- `-days 365`: 証明書の有効期限を365日に設定するオプション。
- `-nodes`: 秘密鍵を暗号化せずに作成するオプション。
- `-subj "/CN=MyRootCA"`: 証明書の主体名（Subject）を指定するオプション。ここでは、Common Name（CN）を"MyRootCA"として設定。
- `-keyout mosquitto/config/certs/ca.key`: 秘密鍵の出力先ファイルを指定。
- `-out mosquitto/config/certs/ca.crt`: 証明書の出力先ファイルを指定。
-

### 2-1.mosquitto（サーバー）の秘密鍵と証明書署名要求（CSR）の作成:

```bash
openssl req -new -nodes -subj "/CN=localhost" -out mosquitto/config/certs/broker.csr -keyout mosquitto/config/certs/broker.key
```

**説明:**
- `openssl req`: OpenSSLコマンドで証明書署名要求（CSR）や自己署名証明書を作成するために使用されるコマンド。
- `-new`: 新しい証明書署名要求を作成するオプション。
- `-nodes`: 秘密鍵を暗号化せずに作成するオプション。
- `-subj "/CN=mybroker"`: 証明書の主体名（Subject）を指定するオプション。ここでは、Common Name（CN）を"mybroker"として設定。
- `-out mosquitto/config/certs/broker.csr`: 証明書署名要求（CSR）の出力先ファイルを指定するオプション。
- `-keyout mosquitto/config/certs/broker.key`: 秘密鍵の出力先ファイルを指定するオプション。


### 2-2. CSRを使用して、CAによって署名されたmosquittoのサーバー証明書の作成:
```bash
openssl x509 -req -in mosquitto/config/certs/broker.csr -CA mosquitto/config/certs/ca.crt -CAkey mosquitto/config/certs/ca.key -CAcreateserial -out mosquitto/config/certs/broker.crt -days 365
```

**説明:**
- `openssl x509`: OpenSSLコマンドで証明書を作成および操作するために使用されるコマンド。
- `-req`: CSRを証明書に署名するオプション。
- `-in mosquitto/config/certs/broker.csr`: 入力として使用するCSRファイルを指定するオプション。
- `-CA mosquitto/config/certs/ca.crt`: 署名するためのCA証明書（自己署名証明書）を指定するオプション。
- `-CAkey mosquitto/config/certs/ca.key`: 署名に使用するCA証明書の秘密鍵を指定するオプション。
- `-CAcreateserial`: シリアル番号ファイルが存在しない場合に自動的に作成するオプション。
- `-out mosquitto/config/certs/broker.crt`: 作成された証明書を保存するファイルを指定するオプション。
- `-days 365`: 証明書の有効期限を365日に設定するオプション。



### 3-1. クライアント用の秘密鍵と証明書署名要求（CSR）の作成

```bash
openssl req -new -nodes -subj "/CN=client" -out mosquitto/config/certs/client.csr -keyout mosquitto/config/certs/client.key
```


**説明:**
- `openssl req`: OpenSSLコマンドで証明書署名要求（CSR）を作成および操作するために使用されるコマンド。
- `-new`: 新しいCSRを作成するオプション。
- `-nodes`: 秘密鍵を暗号化せずに生成するオプション。
- `-subj "/CN=client"`: クライアントのCommon Name（CN）を指定するオプション。ここでは"client"としている。
- `-out mosquitto/config/certs/client.csr`: 作成されたCSRを保存するファイルを指定するオプション。
- `-keyout mosquitto/config/certs/client.key`: 作成された秘密鍵を保存するファイルを指定するオプション。



### 3-2. CSRを使用して、CAによって署名されたクライアント証明書を生成

```bash
openssl x509 -req -in mosquitto/config/certs/client.csr -CA mosquitto/config/certs/ca.crt -CAkey mosquitto/config/certs/ca.key -CAcreateserial -out mosquitto/config/certs/client.crt -days 365
```

**説明:**
- `openssl x509`: OpenSSLコマンドで証明書を作成および操作するために使用されるコマンド。
- `-req`: CSRを証明書に署名するオプション。
- `-in mosquitto/config/certs/client.csr`: 入力として使用するCSRファイルを指定するオプション。
- `-CA mosquitto/config/certs/ca.crt`: 署名するためのCA証明書（自己署名証明書）を指定するオプション。
- `-CAkey mosquitto/config/certs/ca.key`: 署名に使用するCA証明書の秘密鍵を指定するオプション。
- `-CAcreateserial`: シリアル番号ファイルが存在しない場合に自動的に作成するオプション。
- `-out mosquitto/config/certs/client.crt`: 作成された証明書を保存するファイルを指定するオプション。
- `-days 365`: 証明書の有効期限を365日に設定するオプション。


---
### 3-3. クライアント秘密鍵をPKCS#8形式に変換
`openssl`で作成される秘密鍵はPKCS#1形式である。しかしJavaの標準クラスで読み込み可能なものはPKCS#8であるため変換したものも作成しておく。

```bash
openssl pkcs8 -topk8 -inform PEM -outform DER -nocrypt -in mosquitto/config/certs/client.key -out mosquitto/config/certs/client_pkcs8.key
```

**説明:**
- `openssl pkcs8`: OpenSSLコマンドでPKCS#8形式の秘密鍵を作成および操作するために使用されるコマンド。
- `-topk8`: PKCS#8形式の秘密鍵を生成するオプション。
- `-inform PEM`: 入力ファイルの形式をPEM形式で指定するオプション。
- `-outform DER`: 出力ファイルの形式をDER形式で指定するオプション。
- `-nocrypt`: 秘密鍵にパスワードを設定しないオプション。
- `-in mosquitto/config/certs/client.key`: 変換する元の秘密鍵ファイルを指定するオプション。
- `-out mosquitto/config/certs/client_pkcs8.key`: 変換されたPKCS#8形式の秘密鍵を保存するファイルを指定するオプション。

### 4.mosquittoの設定ファイルを作成
以下のようにMQTTSの設定および作成した証明書のパスを設定する。

その上で`docker compose up -d`で起動すればOK

```conf
# MQTTSのポートを設定
port 8883

# 証明書のパスを設定
cafile /mosquitto/config/certs/ca.crt
certfile /mosquitto/config/certs/broker.crt
keyfile /mosquitto/config/certs/broker.key

# 証明書を必須にする
require_certificate true
allow_anonymous true

```



## AWS IoT CoreにMQTTで通信する場合の準備
ここでは以下の3つを使用し、証明書認証を行うことを想定。

マネジメントコンソールでモノを作成し取得する。

* ルート証明書：`AmazonRootCA1.pem`
* クライアント証明書：`cert.crt`にリネームする
* 秘密鍵：`private.key`にリネームする

なお、Javaのサンプルアプリの実装では、クライアントの秘密鍵はPKCS#8であることが必須（IoT Coreで取得できるものはPKCS#1である）。そのため以下のコマンドを使用して、PKCS#8形式に変換する（以下は`/ap`ディレクトリで実行する場合）。

```bash
openssl pkcs8 -topk8 -inform PEM -outform DER -nocrypt -in iotcore/certs/private.key -out iotcore/certs/private_pkcs8.key
```