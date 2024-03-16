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
import { aws_s3_deployment as s3deploy } from 'aws-cdk-lib';
import { aws_s3 as s3 } from 'aws-cdk-lib';

export class IotStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const timestreamDatabaseName = 'TelemetryDatabase'
    const timestreamTableName = 'TelemetryTable'


    // S3 Bucket
    const fileDescriptorBucket = new s3.Bucket(this, 'FileDescriptorBucket', {
      autoDeleteObjects: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      eventBridgeEnabled: true,
    })

    new s3deploy.BucketDeployment(this, 'FileDescriptorDeploy', {
      sources: [s3deploy.Source.asset("filedescriptor/")],
      destinationBucket: fileDescriptorBucket,
      destinationKeyPrefix: "msg/"
    })


    // Kinesis Data Streams
    const stream = new kinesis.Stream(this, 'Streams', {})

    const logGroup = new logs.LogGroup(this, 'Log Group', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      retention: logs.RetentionDays.ONE_DAY
    })

    // IoT Topic Rule
    const topicRule = new iot.TopicRule(this, 'TopicRule', {
      topicRuleName: 'MqttTopicRule',
      description: 'invokes the lambda function',
      sql: iot.IotSql.fromStringAsVer20160323(`SELECT VALUE decode(*, 'proto', '${fileDescriptorBucket.bucketName}', 'msg/filedescriptor.desc', 'dummy_telemetry', 'DummyTelemetry') FROM 'python/messages/#'`),
      actions: [
        new actions.KinesisPutRecordAction(stream, {
          partitionKey: '${newuuid()}',
        })
      ],
      errorAction: new actions.CloudWatchLogsAction(logGroup)
    });


    fileDescriptorBucket.addToResourcePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['s3:Get*'],
        resources: [
          `${fileDescriptorBucket.bucketArn}/*`,
          `${fileDescriptorBucket.bucketArn}`],
        principals: [new iam.ServicePrincipal('iot.amazonaws.com')]
      })
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
