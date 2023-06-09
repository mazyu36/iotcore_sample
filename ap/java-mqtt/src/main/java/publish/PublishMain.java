package publish;

import org.eclipse.paho.client.mqttv3.*;
import helper.MqttHelper;

import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.Random;

import com.example.DummyCommandProto.DummyCommand;
import com.example.DummyCommandProto;

import com.google.protobuf.Timestamp;

public class PublishMain {

    private static final String clientId = "java-publisher";
    private static final String topic = "java/messages";

    public static void main(String[] args) {

        MqttHelper mqttHelper = null;
        try {
            mqttHelper = new MqttHelper(clientId);
            mqttHelper.connect();

            // メッセージの作成とpublishのループ
            while (true) {
                DummyCommand dummyCommand = createDummyCommand();
                byte[] serializedData = dummyCommand.toByteArray();
                mqttHelper.publish(topic, serializedData);
                Thread.sleep(5000); // 1秒待機
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

    // ダミーのメッセージを作成
    private static DummyCommand createDummyCommand() {
        DummyCommand.Builder builder = DummyCommandProto.DummyCommand.newBuilder();

        // commandTypeはランダムに選択
        DummyCommandProto.CommandType[] commandTypes = DummyCommandProto.CommandType.values();
        Random random = new Random();
        int index = random.nextInt(commandTypes.length - 2);

        // CommandTypeを設定
        builder.setCommandType(commandTypes[index]);

        // timestampを設定
        ZonedDateTime now = ZonedDateTime.now(ZoneId.of("Asia/Tokyo"));
        long timestampSeconds = now.toEpochSecond();
        long timestampMillis = System.currentTimeMillis();
        Timestamp timestamp = Timestamp.newBuilder()
                .setSeconds(timestampSeconds)
                .setNanos((int) ((timestampMillis % 1000) * 1000000))
                .build();
        builder.setTimestamp(timestamp);

        return builder.build();
    }

}
