import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { aws_lambda as lambda } from 'aws-cdk-lib';
import { aws_logs as logs } from 'aws-cdk-lib';
import * as iot from '@aws-cdk/aws-iot-alpha'
import * as actions from '@aws-cdk/aws-iot-actions-alpha'
import { aws_iam as iam } from 'aws-cdk-lib';
import { aws_kinesis as kinesis } from 'aws-cdk-lib';
import { aws_lambda_event_sources as event_sources } from 'aws-cdk-lib';
import { aws_timestream as timestream } from 'aws-cdk-lib';

export class IotStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const timestreamDatabaseName = 'TelemetryDatabase'
    const timestreamTableName = 'TelemetryTable'


    // Lambda(Protobuf Deserializer)
    const protobufLayer = new lambda.LayerVersion(this, 'ProtobufLayer', {
      code: lambda.AssetCode.fromAsset('lambda/layer/protobuf'),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_9],
    });

    const protobufFunction = new lambda.Function(this, 'ProtobufFunction', {
      functionName: 'proto-function',
      runtime: lambda.Runtime.PYTHON_3_9,
      code: lambda.Code.fromAsset('lambda/function'),
      handler: 'protobuf.handler',
      layers: [protobufLayer],
      logRetention: logs.RetentionDays.ONE_DAY
    });


    // Kinesis Data Streams
    const stream = new kinesis.Stream(this, 'Streams', {})

    // IoT Topic Rule
    const topicRule = new iot.TopicRule(this, 'TopicRule', {
      topicRuleName: 'MqttTopicRule',
      description: 'invokes the lambda function',
      sql: iot.IotSql.fromStringAsVer20160323(`SELECT aws_lambda('${protobufFunction.functionArn}',{'data': encode(*, 'base64')}) as payload FROM 'python/messages/#'`),
      actions: [
        new actions.KinesisPutRecordAction(stream, {
          partitionKey: '${newuuid()}',
        })
      ]
    });

    // IoT Topic RuleからLambdaを呼び出す権限を付与
    protobufFunction.addPermission(
      'IoT Topic Rule Invocation', {
      principal: new iam.ServicePrincipal('iot.amazonaws.com'),
      action: 'lambda:InvokeFunction',
      sourceArn: topicRule.topicRuleArn
    }
    )

    // Lambda(Kinesis Data Streamsから呼び出されるConsumer)
    const consumerFunction = new lambda.Function(this, 'ConsumerFunction', {
      functionName: 'consumer-function',
      runtime: lambda.Runtime.PYTHON_3_9,
      code: lambda.Code.fromAsset('lambda/function'),
      handler: 'consumer.handler',
      logRetention: logs.RetentionDays.ONE_DAY,
      environment: {
        'DATABASE_NAME': timestreamDatabaseName,
        'TABLE_NAME': timestreamTableName
      }
    });

    consumerFunction.addEventSource(new event_sources.KinesisEventSource(stream, {
      batchSize: 100,
      startingPosition: lambda.StartingPosition.TRIM_HORIZON,
      retryAttempts: 0
    }))


    // Timestream
    const timestreamDatabase = new timestream.CfnDatabase(this, 'Database', {
      databaseName: timestreamDatabaseName
    })

    const timestreamTable = new timestream.CfnTable(this, 'Table', {
      databaseName: timestreamDatabaseName,
      tableName: timestreamTableName
    })

    timestreamTable.addDependency(timestreamDatabase)


    // Lambda(consumer)からTimestreamに書き込みを行うための権限を付与
    const timestreamPolicy = new iam.PolicyStatement({
      actions: [
        'timestream:WriteRecords',
      ],
      resources: [
        timestreamTable.attrArn
      ],
    })

    const describeEndpointsPolicy = new iam.PolicyStatement({
      actions: [
        'timestream:DescribeEndpoints',
      ],
      resources: ['*'],
    })

    // ポリシードキュメントをLambda関数のロールに追加
    consumerFunction.addToRolePolicy(timestreamPolicy);
    consumerFunction.addToRolePolicy(describeEndpointsPolicy);

  }
}
