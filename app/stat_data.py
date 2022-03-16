from app import managerapp, scheduler, stats, worker_list, DEBUG, ec2_resource, cloudwatch_client
from app.ec2_access import ec2_start_instance, ec2_pause_instance
from datetime import datetime, timedelta

def stats_append(datatype, data):
    """
    Add a new data point into local statistic table while maintains 30
    data points in total
    :param datatype: str
    :param data: int or float
    :return: bool
    """
    if (datatype is not None) and (data is not None):
        stats[datatype].append(data)
        stats[datatype].pop(0)
        return True
    else:
        return False


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
    instances = ec2_resource.instances.filter(
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
    Get the latest CloudWatch statistics of all tyoe
    Will be called by scheduler
    :return:
    """
    metric_types = ['Items', 'Size', 'Reqs', 'HitRate', 'MissRate']
    worker_cnt = stats['Workers'][-1]  # Get the number of running workers first
    if worker_cnt >= 1:
        for metric in metric_types:
            value = stats_aws_get_stat(worker_cnt, metric)
            stats_append(metric, value)  # Add to the local statistic array
    else:
        print('Error: no worker is running')


def stats_get_worker_list():
    """
    Return a list that contains all running instances
    Will be called by scheduler
    :return:
    """
    worker_cnt = 0
    instances = stats_aws_get_workers("running")
    if DEBUG is True:
        print('Starting CloudWatch data collection: ', datetime.utcnow())
        print('Getting Working Count...')

    # The following section update the instance list with their status
    for inst_id in worker_list.keys():
        worker_list[inst_id] = 0    # set all instance as paused
    for instance in instances:
        if DEBUG is True:
            print('Available Worker: ', instance.id)
        worker_list[instance.id] = 1    # update the instance status one by one
        worker_cnt += 1

    # The following section update the running worker counter
    if (DEBUG is True) and (worker_cnt == 0):
        print('Error No Available Worker')
    stats_append('Workers', worker_cnt)
    if DEBUG is True:
        print('Worker data collection completed')

    '''
    The following section resume/add the job to collect CloudWatch Metrics
      - if no worker is running the task will be paused to avoid dividing by
        zero error while calculating the average value
      - if there is at least on running worker, the task will be added/resumed
    '''
    if worker_cnt >= 1:
        if scheduler.get_job('update_aws_stats'):   # test is task is existing
            scheduler.resume_job('update_aws_stats')
            if DEBUG is True:
                print('CloudWatch Task is resumed!')
        else:
            scheduler.add_job(id='update_aws_stats', func=stats_aws_get_stats,
                              trigger='interval', seconds=managerapp.config['JOB_INTERVAL'])
            if DEBUG is True:
                print('CloudWatch Task doesn\'t existed, but now added!')
    else:
        if scheduler.get_job('update_aws_stats'):
            scheduler.pause_job('update_aws_stats')
            if DEBUG is True:
                print('CloudWatch Task is paused!')





