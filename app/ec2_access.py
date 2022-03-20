from app import managerapp, ec2_client, DEBUG, stats, scaler_config
from botocore.exceptions import ClientError


def ec2_start_instance(inst_id):
    # Do a dryrun first to verify permissions
    try:
        res = ec2_client.start_instances(InstanceIds=[inst_id], DryRun=True)
    except ClientError as err:
        if 'DryRunOperation' not in str(err):
            raise

    # Dry run succeeded, run start_instances without dryrun
    try:
        res = ec2_client.start_instances(InstanceIds=[inst_id], DryRun=False)
    except ClientError as err:
        print(err)


def ec2_pause_instance(inst_id):
    # Do a dryrun first to verify permissions
    try:
        res = ec2_client.stop_instances(InstanceIds=[inst_id], DryRun=True)
    except ClientError as err:
        if 'DryRunOperation' not in str(err):
            raise

    # Dry run succeeded, run start_instances without dryrun
    try:
        res = ec2_client.stop_instances(InstanceIds=[inst_id], DryRun=False)
    except ClientError as err:
        print(err)
