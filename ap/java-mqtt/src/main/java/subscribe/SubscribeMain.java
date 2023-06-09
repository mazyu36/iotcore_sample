package subscribe;

import org.eclipse.paho.client.mqttv3.*;
import helper.MqttHelper;

import com.google.protobuf.Timestamp;
import com.example.DummyTelemetryProto.DummyTelemetry;
import java.util.Date;
import java.util.TimeZone;
import java.text.SimpleDateFormat;

public class SubscribeMain {
    private static final String clientId = "java-subscriber";
    private static final String topic = "python/messages/#";

    // タイムゾーンを設定
    private static final TimeZone timeZone = TimeZone.getTimeZone("Asia/Tokyo");

    public static void main(String[] args) {
        MqttHelper mqttHelper = null;

        try {
            mqttHelper = new MqttHelper(clientId);
            mqttHelper.connect();

            // Subscribeする
            mqttHelper.subscribe(topic, createTelemetryCallback());

            // 無限ループで待機し続ける
            while (true) {
                Thread.sleep(1000);
            }
        } catch (MqttException | InterruptedException e) {
            e.printStackTrace();
        } finally {
            if (mqttHelper != null) {
                try {
                    mqttHelper.disconnect();
                } catch (MqttException e) {
                    e.printStackTrace();
                }
            }
        }
    }

    // Subscribeした際に呼ばれるコールバックを作成
    private static MqttCallback createTelemetryCallback() {
        return new MqttCallback() {
            // 接続が切断された際に呼ばれるコールバック
            @Override
            public void connectionLost(Throwable cause) {
                System.out.println("Connection lost: " + cause.getMessage());
            }

            // メッセージが届いた際に呼ばれるコールバック
            @Override
            public void messageArrived(String topic, MqttMessage message) throws Exception {

                // トピック名にwillが含まれている場合はメッセージをログに出して終了する
                if (topic.contains("will")) {
                    System.out.println("##### Will Message Delivered!:");
                    System.out.println("Topic: " + topic);
                    System.out.println("Message: " + message.toString());
                    System.out.println("\n");
                    return;
                }

                System.out.println("##### Message Delivered!:");
                System.out.println("Topic: " + topic);

                // message.getPayload()はDummyTelemetryのバイナリデータなのでデシリアライズする
                DummyTelemetry dummyTelemetry = DummyTelemetry.parseFrom(message.getPayload());
                System.out.println("##### Deserialized message:");
                System.out.println("id: " + dummyTelemetry.getId());
                System.out.println("latitude: " + dummyTelemetry.getLatitude());
                System.out.println("longitude: " + dummyTelemetry.getLongitude());

                // タイムスタンプを取得してDateに変換
                Timestamp timestamp = dummyTelemetry.getTimestamp();
                long seconds = timestamp.getSeconds();
                long nanos = timestamp.getNanos();
                Date date = new Date(seconds * 1000 + nanos / 1000000); // ミリ秒単位に変換

                // タイムゾーンを適用
                SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS");
                sdf.setTimeZone(timeZone);
                String formattedDate = sdf.format(date);

                System.out.println("timestamp: " + formattedDate);
                System.out.println("\n");
            }

            // メッセージが送信された際に呼ばれるコールバック
            @Override
            public void deliveryComplete(IMqttDeliveryToken token) {
                // Not used in this example
            }
        };
    }

}
