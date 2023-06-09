package helper;

import org.eclipse.paho.client.mqttv3.*;
import java.io.FileInputStream;
import java.security.KeyStore;
import java.security.cert.Certificate;
import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManagerFactory;
import java.security.cert.CertificateFactory;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.KeyManagerFactory;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.KeyFactory;
import java.security.PrivateKey;

import java.io.InputStream;
import java.util.Properties;

public class MqttHelper {

    private String brokerHost;
    private MqttClient client;
    private String username;
    private String password;
    private String caCertFilePath;
    private String clientCertFilePath;
    private String clientKeyFilePath;

    // MQTTクライアントの作成
    public MqttHelper(String clientId) throws MqttException {
        // プロパティから設定値を読み込み
        String configFile = "config.properties";
        Properties properties = new Properties();

        try (InputStream inputStream = MqttHelper.class.getClassLoader().getResourceAsStream(configFile)) {
            // プロパティファイルを読み込む
            properties.load(inputStream);

            // プロパティファイルからbrokerのホスト名を取得
            this.brokerHost = properties.getProperty("broker.host");

            // 設定値の取得
            this.username = properties.getProperty("broker.username");
            this.password = properties.getProperty("broker.password");

            // CA証明書のパス
            this.caCertFilePath = properties.getProperty("broker.caCertFilePath");
            this.clientCertFilePath = properties.getProperty("broker.clientCertFilePath");
            this.clientKeyFilePath = properties.getProperty("broker.clientKeyFilePath");

        } catch (Exception e) {
            // エラーハンドリング
            e.printStackTrace();
            throw new MqttException(e);
        }

        client = new MqttClient(this.brokerHost, clientId);
    }

    public void connect() throws MqttException {
        // 接続オプションの設定
        MqttConnectOptions connOpts = new MqttConnectOptions();
        connOpts.setCleanSession(false);

        // ユーザー名とパスワードがnullでなければ設定する
        if (this.username != null && this.password != null) {
            connOpts.setUserName(this.username);
            connOpts.setPassword(this.password.toCharArray());
        }

        try {
            // SSLContextの作成
            SSLSocketFactory sslSocketFactory = createSSLSocketFactory();
            connOpts.setSocketFactory(sslSocketFactory);
        } catch (Exception e) {
            // エラーハンドリング
            e.printStackTrace();
            throw new MqttException(e);
        }

        client.connect(connOpts);
        System.out.println("Connected to broker");
    }

    public void publish(String topic, byte[] serializedData) throws MqttException {
        MqttMessage mqttMessage = new MqttMessage(serializedData);
        client.publish(topic, mqttMessage);
        System.out.println("Published message: " + serializedData);
    }

    public void subscribe(String topic, MqttCallback callback) throws MqttException {
        client.setCallback(callback);
        client.subscribe(topic);
        System.out.println("Subscribed to topic: " + topic);
    }

    public void disconnect() throws MqttException {
        client.disconnect();
        System.out.println("Disconnected from broker");
    }

    private SSLSocketFactory createSSLSocketFactory() throws Exception {
        SSLContext sslContext = SSLContext.getInstance("TLSv1.2");

        // 自己証明書、クライアント証明書/秘密鍵の設定がある場合は、それらを使用してSSLContextを作成
        if (this.caCertFilePath != null && this.clientCertFilePath != null && this.clientKeyFilePath != null) {
            // CA証明書の読み込み
            FileInputStream caCertFile = new FileInputStream(this.caCertFilePath);
            Certificate caCert = CertificateFactory.getInstance("X.509").generateCertificate(caCertFile);
            caCertFile.close();

            // クライアント証明書の読み込み
            FileInputStream clientCertFile = new FileInputStream(this.clientCertFilePath);
            Certificate clientCert = CertificateFactory.getInstance("X.509").generateCertificate(clientCertFile);
            clientCertFile.close();

            // クライアント秘密鍵の読み込み
            FileInputStream clientKeyFile = new FileInputStream(this.clientKeyFilePath);
            byte[] keyBytes = clientKeyFile.readAllBytes();
            clientKeyFile.close();

            // PKCS#8形式に変換
            PKCS8EncodedKeySpec keySpec = new PKCS8EncodedKeySpec(keyBytes);
            KeyFactory keyFactory = KeyFactory.getInstance("RSA");
            PrivateKey privateKey = keyFactory.generatePrivate(keySpec);

            // KeyManagerFactoryの作成
            KeyStore keyStore = KeyStore.getInstance(KeyStore.getDefaultType());
            keyStore.load(null, null);
            keyStore.setCertificateEntry("clientCert", clientCert);
            keyStore.setKeyEntry("privateKey", privateKey, null, new Certificate[] { clientCert });
            KeyManagerFactory keyManagerFactory = KeyManagerFactory
                    .getInstance(KeyManagerFactory.getDefaultAlgorithm());
            keyManagerFactory.init(keyStore, null);

            // TrustManagerFactoryの作成
            KeyStore trustStore = KeyStore.getInstance(KeyStore.getDefaultType());
            trustStore.load(null, null);
            trustStore.setCertificateEntry("caCert", caCert);
            TrustManagerFactory trustManagerFactory = TrustManagerFactory
                    .getInstance(TrustManagerFactory.getDefaultAlgorithm());
            trustManagerFactory.init(trustStore);

            sslContext.init(keyManagerFactory.getKeyManagers(), trustManagerFactory.getTrustManagers(), null);
        } else {
            sslContext.init(null, null, null);
        }

        return sslContext.getSocketFactory();
    }
}
