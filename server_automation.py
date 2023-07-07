import boto3 
from datetime import datetime, timedelta

region = ['us-east-1','eu-central-1','ap-southeast-1']
dev_instances_apac = []
dev_instances_eu = ['i-04efe43d2936c95c1', 'i-0eb47f69fd02de6ab']
dev_instances_us = ['i-0a63a340009c77492','i-0e4bf52795975afb9']

qa_instances_apac = ['i-0c80e1126500dfb55', 'i-0f83b002740a77044']
qa_instances_eu = ['i-005bf8cbc08ec382c','i-0dff796afd9853a5b']
qa_instances_us = []
load = 1

sts_connection_dev = boto3.client('sts')
dev_account = sts_connection_dev.assume_role(
    RoleArn="arn:aws:iam::441153016065:role/ec2_access_role_dev",
    RoleSessionName="cross_acct_lambda_dev"
)

DEV_ACCESS_KEY = dev_account['Credentials']['AccessKeyId']
DEV_SECRET_KEY = dev_account['Credentials']['SecretAccessKey']
DEV_SESSION_TOKEN = dev_account['Credentials']['SessionToken']

sts_connection_qa = boto3.client('sts')
qa_account = sts_connection_qa.assume_role(
    RoleArn="arn:aws:iam::528102736060:role/ec2_access_role_qa",
    RoleSessionName="cross_acct_lambda_qa"
)

QA_ACCESS_KEY = qa_account['Credentials']['AccessKeyId']
QA_SECRET_KEY = qa_account['Credentials']['SecretAccessKey']
QA_SESSION_TOKEN = qa_account['Credentials']['SessionToken']

now = datetime.utcnow()
past = now - timedelta(days=1)

def cpu_load_dev(region_value,instances):
    idle_instances = []
    cw_client_dev = boto3.client('cloudwatch', region_name=region_value,aws_access_key_id=DEV_ACCESS_KEY,
        aws_secret_access_key=DEV_SECRET_KEY,
        aws_session_token=DEV_SESSION_TOKEN,)

    ec2_client_dev = boto3.client('ec2', region_name=region_value,aws_access_key_id=DEV_ACCESS_KEY,
        aws_secret_access_key=DEV_SECRET_KEY,
        aws_session_token=DEV_SESSION_TOKEN,)
    
    for id in instances:
        response = cw_client_dev.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[
                {
                'Name': 'InstanceId',
                'Value': id
                },
            ],
            StartTime=past,
            EndTime=now,
            Period=86400,
            Statistics=['Maximum'],
            Unit='Percent'
        )
        for k, v in response.items():
            if k == 'Datapoints':
                for y in v:
                    load = y['Maximum']
                    print('Maximum load on CPU with in 24 hours in {0} in DEV for instance id : {1} is {2}'.format(region_value,id,load))
                    if load < 2:
                        idle_instances.append(id)
    if idle_instances:                 
        print("DEV instances need to be stopped are ", idle_instances )
        ec2_client_dev.stop_instances(InstanceIds=idle_instances)
        print('stopped your instances: ' + str(idle_instances))
    else:
        print('There is no instances in ' + region_value + ' which is having less than 2% cpu load')

def cpu_load_qa(region_value,instances):
    idle_instances = []
    cw_client_qa = boto3.client('cloudwatch', region_name=region_value,aws_access_key_id=QA_ACCESS_KEY,
        aws_secret_access_key=QA_SECRET_KEY,
        aws_session_token=QA_SESSION_TOKEN,)

    ec2_client_qa = boto3.client('ec2', region_name=region_value,aws_access_key_id=QA_ACCESS_KEY,
        aws_secret_access_key=QA_SECRET_KEY,
        aws_session_token=QA_SESSION_TOKEN,)
    
    for id in instances:
        response = cw_client_qa.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[
                {
                'Name': 'InstanceId',
                'Value': id
                },
            ],
            StartTime=past,
            EndTime=now,
            Period=86400,
            Statistics=['Maximum'],
            Unit='Percent'
        )
        for k, v in response.items():
            if k == 'Datapoints':
                for y in v:
                    load = y['Maximum']
                    print('Maximum load on CPU with in 24 hours in {0} in QA for instance id : {1} is {2}'.format(region_value,id,load))
                    if load < 2:
                        idle_instances.append(id)
    if idle_instances:                   
        print("QA instances need to be stopped are ", idle_instances )
        ec2_client_qa.stop_instances(InstanceIds=idle_instances)
        print('stopped your instances: ' + str(idle_instances))
    else:
        print('There is no instances in ' + region_value + ' which is having less than 2% cpu load')

def lambda_handler(event, context):
    for region_value in region:
        if region_value == 'us-east-1':
            cpu_load_dev(region_value, dev_instances_us)
            cpu_load_qa(region_value, qa_instances_us)
        elif region_value == 'eu-central-1':
            cpu_load_dev(region_value, dev_instances_eu)
            cpu_load_qa(region_value, qa_instances_eu)
        elif region_value == 'ap-southeast-1':
            cpu_load_dev(region_value, dev_instances_apac)
            cpu_load_qa(region_value, qa_instances_apac)
        else:
            print('invalid input')
