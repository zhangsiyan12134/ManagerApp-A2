from app import stats, DEBUG, ec2_client, cloudwatch_client
from app.ec2_access import ec2_start_instance, ec2_pause_instance
from datetime import datetime, timedelta

def stats_latest(datatype):
    """
    return the latest data from stat Dictionary of the given type
    :param datatype: Worker, MissRate, HitRate, Items, Size, or Reqs
    :return: value of the given type
    """
    return stats[datatype][-1]


def stats_aws_get_workers(status):
    """
    Retrieve a list of running instances from AWS
    :param status: str
    :return: ec2.Instances Obj
    """
    instances = ec2_client.instances.filter(
        Filters=[
            {
                'Name': 'instance-state-name',
                'Values': [
                    status
                ]
            },
            {
                'Name': 'instance-type',
                'Values': [
                    't2.micro'
                ]
            }
        ]
    )
    return instances


def stats_worker_cnt():
    """
    Count how many worker is running
    :return: int
    """
    instances = stats_aws_get_workers("running")
    workers = []
    if DEBUG is True:
        print('Starting CloudWatch data collection: ', datetime.utcnow())
        print('Getting Working Count...')
    for instance in instances:
        if DEBUG is True:
            print('Available Worker: ', instance.id)
        workers.append(instance.id)
    if (DEBUG is True) and (not workers):
        print('Error No Available Worker')
    if DEBUG is True:
        print('CloudWatch data collection completed: ')

    return len(workers)


def stats_aws_get_stat(worker_cnt, metric_type):
    """
    Calculate the average metric from all running instances for last minute
    :param worker_cnt: int
    :param metric_type: str
    :return: the average metric of all running instances in last minute
    """
    ts = datetime.utcnow()
    total = 0
    if DEBUG is True:
        print('Starting CloudWatch data collection: ', ts)
    for inst in range(0, worker_cnt):
        value = cloudwatch_client.get_metric_statistics(
                    Period=60,      # Set the average interval to 1 minute
                    Namespace='MemCache',
                    MetricName=metric_type,
                    Dimensions=[{'Name': 'InstanceId', 'Value': str(inst+1)}],
                    StartTime=ts - timedelta(seconds=1 * 60),
                    EndTime=ts,
                    Statistics=['Average']
                )
        if DEBUG is True:
            print('The response from AWS is: ', value['Datapoints'])
        if not value['Datapoints']:
            print('Warning: No data for instance ', inst + 1, 'at the moment')
        else:
            total += value['Datapoints'][0]['Average']
    if DEBUG is True:
        print('CloudWatch data collection completed: ')
    return total / worker_cnt


def stats_aws_get_stats():
    """
    Get the latest CloudWatch statistics, if there is no ec2 running, start one immediately
    :return:
    """
    metric_types = ['ItemCount', 'TotalCountentSize', 'TotalRequestCount', 'HitRate', 'MissRate']
    worker_cnt = stats_worker_cnt()  # Get the number of running workers first
    stopped_workers = []
    if worker_cnt >= 1:
        stats['Workers'].append()
        for metric in metric_types:
            stats_aws_get_stat(stats['Workers'][-1], metric)
    else:
        if DEBUG is True:
            print('Error: no worker is running')
        instances = stats_aws_get_workers("stopped")
        for instance in instances:
            stopped_workers.append(instance.id)
        ec2_start_instance(stopped_workers[0])  # pick one stopped ec2 instance and start it.
