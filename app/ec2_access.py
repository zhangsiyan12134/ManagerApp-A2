from app import managerapp, ec2_client, DEBUG, stats, scalar_config
from botocore.exceptions import ClientError


def ec2_start_instance(inst_id):
    # DryRun for permission check
    try:
        res = ec2_client.start_instances(InstanceIds=[inst_id], DryRun=True)
    except ClientError as err:
        if 'DryRunOperation' not in str(err):
            raise

    # DryRun works
    try:
        res = ec2_client.start_instances(InstanceIds=[inst_id], DryRun=False)
    except ClientError as err:
        print(err)


def ec2_pause_instance(inst_id):
    # DryRun for permission check
    try:
        res = ec2_client.stop_instances(InstanceIds=[inst_id], DryRun=True)
    except ClientError as err:
        if 'DryRunOperation' not in str(err):
            raise

    # DryRun works
    try:
        res = ec2_client.stop_instances(InstanceIds=[inst_id], DryRun=False)
    except ClientError as err:
        print(err)
