#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { IotStack } from '../lib/iotStack';

const app = new cdk.App();
new IotStack(app, 'IotStack')