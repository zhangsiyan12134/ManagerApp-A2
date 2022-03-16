from datetime import datetime, timedelta
from app import webapp
from flask import render_template,request, jsonify, redirect, url_for, json
from app.main import *
from app.config import s3_bucket_name
import sys
import boto3
import time
from botocore.exceptions import ClientError
from pebble import ThreadPool
from operator import itemgetter

global start 
start = False

global manager_active
manager_active = False

global thres_grow
thres_grow = 60

global thres_shrink
thres_shrink = 15

global grow_ratio
grow_ratio = 2.0

global shrink_ratio
shrink_ratio = 0.5

ec2 = boto3.client('ec2')
elb = boto3.client('elb')
cloudwatch = boto3.client('cloudwatch')

pool = ThreadPool(2)

def start_ec2_ins(ins_id):
    # DryRun for permission check
    try:
        res = ec2.start_instances(InstanceIds = [ins_id], DryRun = True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            raise

    # DryRun works
    try:
        res = ec2.start_instances(InstanceIds = [ins_id], DryRun = False)
    except ClientError as e:
        print(e)

def stop_ec2_ins(ins_id):
    # DryRun for permission check
    try:
        res = ec2.stop_instances(InstanceIds = [ins_id], DryRun = True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            raise

    # DryRun works
    try:
        res = ec2.stop_instances(InstanceIds = [ins_id], DryRun = False)
    except ClientError as e:
        print(e)

@webapp.route('/list_all_ins')
def list_all_instances():
    result = []
    
    ins_list = (elb.describe_load_balancers(LoadBalancerNames = ['ece1779a2lb']))['LoadBalancerDescriptions'][0]['Instances']

    for ins in ins_list:
        result.append(ins['InstanceId'])

    return jsonify(result)


@webapp.route('/list_active_ins')
def list_active_instances():
    result = []
    ins_list = (elb.describe_load_balancers(LoadBalancerNames = ['ece1779a2lb']))['LoadBalancerDescriptions'][0]['Instances']
    for ins in ins_list:
        res = (ec2.describe_instance_status(InstanceIds = [ins['InstanceId']], IncludeAllInstances = True)['InstanceStatuses'])
        if res and (res[0]['InstanceState']['Name'] == "running"):
            result.append(ins['InstanceId'])
    return  jsonify(result)

@webapp.route('/describe_all_ins')
def describe_all_instances():
    result = []
    ins_list = (elb.describe_load_balancers(LoadBalancerNames = ['ece1779a2lb']))['LoadBalancerDescriptions'][0]['Instances']
    for ins in ins_list:
        res = (ec2.describe_instance_status(InstanceIds = [ins['InstanceId']], IncludeAllInstances = True)['InstanceStatuses'])
        result.append(res)
    return  jsonify(result)

@webapp.route('/describe_active_ins')
def describe_active_instances():
    result = []
    ins_list = (elb.describe_load_balancers(LoadBalancerNames = ['ece1779a2lb']))['LoadBalancerDescriptions'][0]['Instances']
    for ins in ins_list:
        res = (ec2.describe_instance_status(InstanceIds = [ins['InstanceId']], IncludeAllInstances = True)['InstanceStatuses'])
        if res and (res[0]['InstanceState']['Name'] == "running"):
            result.append(res[0])
    return  jsonify(result)

@webapp.route('/stop_worker')
def stop_worker(policy = False):
    if not policy:
        print("Stopping a worker manually")
        stop_background_job()

    result = []
    value = 0
    message =''
    message1 = ''
    ins_list = (elb.describe_load_balancers(LoadBalancerNames = ['ece1779a2lb']))['LoadBalancerDescriptions'][0]['Instances']
    for ins in ins_list:
        res = (ec2.describe_instance_status(InstanceIds = [ins['InstanceId']], IncludeAllInstances = True)['InstanceStatuses'])
        if (res[0]['InstanceState']['Name'] == "pending") or (res[0]['InstanceState']['Name'] == "running"):
            result.append(ins['InstanceId'])
            value += 1
    if result:
        stop_ec2_ins(result[0])
        value -= 1
        message = "One worker has been stopped"
    else:
        message = "There is no worker running"
    message1 = 'Worker Pool Size: '+str(value)

    if policy:
        return
    return render_template('ec2/changeworker.html',worker = message1, message = message)

@webapp.route('/start_worker')
def start_worker(policy = False):
    if not policy:
        print("Starting a worker manually")
        stop_background_job()
        
    value = 0
    result = []
    message = ''
    message1 = ''
    ins_list = (elb.describe_load_balancers(LoadBalancerNames = ['ece1779a2lb']))['LoadBalancerDescriptions'][0]['Instances'] 
    for ins in ins_list:
        res = (ec2.describe_instance_status(InstanceIds = [ins['InstanceId']], IncludeAllInstances = True)['InstanceStatuses'])
        if (res[0]['InstanceState']['Name'] == "stopped"):
            result.append(ins['InstanceId'])
        if (res[0]['InstanceState']['Name'] == "pending" or res[0]['InstanceState']['Name'] == "running"):
            value += 1
    if result:
        start_ec2_ins(result[0])
        value += 1
        message = "Worker " + result[0] + " has been started"
    else:
        message = "No worker can be started now. If current pool size < 6, please try again later."
    message1 = 'Worker Pool Size: '+str(value)
    if policy:
        return
    return render_template('ec2/changeworker.html',worker = message1, message = message)


@webapp.route('/stop_background')
def stop_background_job():
    global start 
    start = False
    global manager_active
    manager_active = False
    Message = ("Auto-scaling has stopped")
    return render_template('m_main.html',Stop_message = json.dumps(Message))


@webapp.route('/stop_manager')
def stop_manager():
    global start 
    start = False
    global manager_active
    manager_active = False
    print("Background job stopped by 'stopping manager'")

    result = []
    ins_list = (elb.describe_load_balancers(LoadBalancerNames = ['ece1779a2lb']))['LoadBalancerDescriptions'][0]['Instances']
    for ins in ins_list:
        res = (ec2.describe_instance_status(InstanceIds = [ins['InstanceId']], IncludeAllInstances = True)['InstanceStatuses'])
        if (res[0]['InstanceState']['Name'] == "pending") or (res[0]['InstanceState']['Name'] == "running"):
            result.append(ins['InstanceId'])
    if result:
        for i in result:
            stop_ec2_ins(i)
    Message = "Manager-app Has Stopped"
    return render_template('m_main.html',Stop_message = json.dumps(Message))

def num_running_workers():
    result = []
    ins_list = (elb.describe_load_balancers(LoadBalancerNames = ['ece1779a2lb']))['LoadBalancerDescriptions'][0]['Instances']
    for ins in ins_list:
        res = (ec2.describe_instance_status(InstanceIds = [ins['InstanceId']], IncludeAllInstances = True)['InstanceStatuses'])
        if res and (res[0]['InstanceState']['Name'] == "running" or res[0]['InstanceState']['Name'] == "pending"):
            result.append(ins['InstanceId'])
    return  len(result)

def avg_cpu_utils():
    active_ins = []
    ins_list = (elb.describe_load_balancers(LoadBalancerNames = ['ece1779a2lb']))['LoadBalancerDescriptions'][0]['Instances']
    for ins in ins_list:
        res = (ec2.describe_instance_status(InstanceIds = [ins['InstanceId']], IncludeAllInstances = True)['InstanceStatuses'])
        if res and (res[0]['InstanceState']['Name'] == "running"):
            active_ins.append(ins['InstanceId'])
    
    # past 2 minutes, add 5 hours to convert from EST to UTC
    start_time = datetime.now() - timedelta(minutes = 2) 
    end_time = datetime.now()

    result = 0
    for ins in active_ins:
        response = get_cpu_util(ins, start_time, end_time)

        data_pts = response['Datapoints']
        print("length of data_pts: ", len(data_pts))
        print(data_pts)
        if len(data_pts) == 0:
            # error message 
            print("no cpu usage data found")
        elif len(data_pts) == 1:
            result += response['Datapoints'][0]['Average']
        else:
            result += (response['Datapoints'][0]['Average']+ response['Datapoints'][1]['Average'])/2
    
    result = result/len(active_ins)
    print(result)
    return result


@webapp.route('/display_utils/<id>')
def display_cpu_utils(id):
    instanceid = id
    print('id '+instanceid)
    # past 30 minutes, add 5 hours to convert from EST to UTC
    start_time = datetime.now() - timedelta(minutes = 30)
    end_time = datetime.now()

    response = get_cpu_util(id, start_time, end_time)
    response2 = get_http_req_rate(id, start_time, end_time)

    message = ""
    message2 = ""

    data_pts = response['Datapoints']
    data_pts2 = response2['Datapoints']

    # handle cpu util data
    cpu_utils = []
    for item in data_pts:
        cpu_utils.append(item)
    
    # sorted in chronical order
    cpu_utils = sorted(cpu_utils, key=itemgetter('Timestamp'))

    if len(cpu_utils) == 0:
        # error message 
        message = "no cpu usage data found"
        cpu_utils = [0 for i in range(30)]
    

    # handle http request rate data
    req_rate = [0 for i in range(30)]

    if len(data_pts2) == 0:
        # return empty list
        message2 = "no request data found"
    
    for item in data_pts2:
        timestamp = item['Timestamp'].replace(tzinfo=None) 

        # match data points in the result list
        index = int((timestamp - start_time).total_seconds()/60)
        if index < 0 or index > 29:
            continue      
        req_rate[index] = int(item['SampleCount'])


    # render template here, showing raw results now
    return render_template('ec2/worker.html',info = json.dumps(cpu_utils), http = json.dumps(req_rate), message = message, message2 = message2, id = json.dumps(instanceid))


# display HTTP Request rate for a instance
@webapp.route('/display_http_req_rate/<id>')
def display_http_req_rate(id):
    # past 30 minutes, add 5 hours to convert from EST to UTC
    start_time = datetime.now() - timedelta(minutes = 30) 
    end_time = datetime.now()

    response = get_http_req_rate(id, start_time, end_time)

    # initialize result array with 0
    req_rate = [0 for i in range(30)]

    data_pts = response['Datapoints']

    message = ""
    if len(data_pts) == 0:
        # return empty list
        message = "no request data found"
        return str(req_rate)
    
    for item in data_pts:
        timestamp = item['Timestamp'].replace(tzinfo=None) 

        # match data points in the result list
        index = int((timestamp - start_time).total_seconds()/60)
        if index < 0 or index > 29:
            continue
        
        req_rate[index] = int(item['SampleCount'])
    
    return str(req_rate)


# display number of workers for the past 30 minutes
@webapp.route('/display_worker_count')
def display_worker_count():
    # past 30 minutes, add 5 hours to convert from EST to UTC
    start_time = datetime.now() - timedelta(minutes = 30) 
    end_time = datetime.now()

    # USE THESE VALUES TO TEST IT OUT
    # start_time = datetime(2021,11,22,5,30)
    # end_time = datetime(2021,11,22,6)

    response = get_healthy_worker_count("ece1779a2lb", start_time, end_time)
    data_pts = response["Datapoints"]

    data_pts = sorted(data_pts, key=itemgetter('Timestamp'))

    worker_count = []
    for item in data_pts:
        worker_count.append(int(item['Maximum']))

    return str(worker_count)
    


@webapp.route('/changeWorker')
def changeWorker():
    value = 0
    message1 = ''
    message2 = ''
    ins_list = (elb.describe_load_balancers(LoadBalancerNames = ['ece1779a2lb']))['LoadBalancerDescriptions'][0]['Instances']
    for ins in ins_list:
        res = (ec2.describe_instance_status(InstanceIds = [ins['InstanceId']], IncludeAllInstances = True)['InstanceStatuses'])
        if res and (res[0]['InstanceState']['Name'] == "running" or res[0]['InstanceState']['Name'] == "pending"):
            value += 1
    if (value == 0):
        message2 = 'No Worker Now'
    elif value == 6:
        message2 = 'All Workers are working'
    message1 = 'Worker Pool Size: '+str(value)
    print('message'+message2)
    print(message1)
    return render_template('ec2/changeworker.html',worker = message1, message = message2)

@webapp.route('/configAuto')
def configAuto():
    
    return render_template('ec2/config.html')

@webapp.route('/showTable')
def showTable():
    runingInstance = 0
    pendingInstance = 0
    stopedInstance = 6
    #print('show Table')
    result = []

    start_time = datetime.now() - timedelta(minutes = 30) 
    end_time = datetime.now()
    # get the worker instance history in past 30 minuts
    response = get_healthy_worker_count("ece1779a2lb", start_time, end_time)
    data_pts = response["Datapoints"]
    data_pts = sorted(data_pts, key=itemgetter('Timestamp'))
    worker_count = []
    for item in data_pts:
        worker_count.append(int(item['Maximum']))

    ins_list = (elb.describe_load_balancers(LoadBalancerNames = ['ece1779a2lb']))['LoadBalancerDescriptions'][0]['Instances']
    for ins in ins_list:
        res = (ec2.describe_instance_status(InstanceIds = [ins['InstanceId']], IncludeAllInstances = True)['InstanceStatuses'])
        if res and (res[0]['InstanceState']['Name'] == "running"):
            result.append(res[0])
            runingInstance += 1
            stopedInstance -= 1
        elif res and (res[0]['InstanceState']['Name'] == "pending"):
            pendingInstance += 1
            stopedInstance -= 1
    Message = "Runing Instances: "+ str(runingInstance)+" Pending Instance: "+str(pendingInstance)+ " Stopped Instance: "+ str(stopedInstance)+" Worker Pool Size: "+str(runingInstance+pendingInstance)
    return render_template('table.html', instances = json.dumps(result),printMessage = Message,historyData = json.dumps(worker_count))


# deletes all application data in database and s3
@webapp.route('/delete_app_data')
def delete_app_data():

    cnx = get_db()
    cursor = cnx.cursor()
    try:
        cnx.start_transaction()

        # delete all user except admin
        query_user = "DELETE FROM user WHERE username <> %s"
        cursor.execute(query_user, ('admin',))

        query_image = "DELETE FROM image"
        cursor.execute(query_image)

        query_img_transform = "DELETE FROM image_transform"
        cursor.execute(query_img_transform)

        query_img_thumbnail = "DELETE FROM image_thumbnail"
        cursor.execute(query_img_thumbnail)

        # delete all images stored in s3
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(s3_bucket_name)
        bucket.objects.all().delete()

        cnx.commit()
    except:
        cnx.rollback()
        # error message here
        return render_template('m_main.html',Stop_message = json.dumps("Erase Data Failed"))

    # render template here
    return render_template('m_main.html',Stop_message = json.dumps("Erase Data Success"))

#############################
##### CloudWatch helper #####

# return response or data points for CPUUtilization of the past 30 minutes for a instance given id
def get_cpu_util(id, start_time, end_time):

    # response will be a dict
    response = ""

    try:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[
            { 
                'Name': 'InstanceId',
                'Value': id
            },
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,
            Statistics=['Average']
        )
    except Exception as e:
        return str(e)

    return response


def get_http_req_rate(id, start_time, end_time):
    # response will be a dict
    response = ""
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace='ECE1779A2',
            MetricName='httpReqCount',
            Dimensions=[
            {
                'Name': 'InstanceId',
                'Value': id
            },
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,
            Statistics=['SampleCount']
        )
    except Exception as e:
        print(str(e))
        return 
    
    return response

def get_healthy_worker_count(load_balancer, start_time, end_time):
    
    response = ""
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/ELB',
            MetricName='HealthyHostCount',
            Dimensions=[
            {
                'Name': 'LoadBalancerName',
                'Value': load_balancer
            },
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,
            Statistics=['Maximum']
        )
    except Exception as e:
        print(str(e))
        return
    
    return response

def configure_autoscaling_policy(threshold_grow, threshold_shrink, ratio_grow, ratio_shrink):
    print("policy")
    # If currently there is no worker
    cur_workers_num = num_running_workers()
    if cur_workers_num == 0:
        start_worker(policy = True)
        cur_workers_num = 1
        return
    
    avg_utils = avg_cpu_utils()
    print("avg utils is: ", avg_utils)
    

    # Need more workers
    if avg_utils > float(threshold_grow):
        new_num_workers = cur_workers_num * float(ratio_grow) 
        if new_num_workers > 6:
            new_num_workers = 6
        add_workers_num = int(new_num_workers) - int(cur_workers_num)
        for _ in range(int(add_workers_num)):
            start_worker(policy = True)

    # Need less workers
    if avg_utils < float(threshold_shrink):
        if cur_workers_num == 1:
            return
        else:
            new_num_workers = cur_workers_num * float(ratio_shrink)
            print("new worker ", new_num_workers)
            if new_num_workers < 1:
                new_num_workers = 1
            stop_workers_num = int(cur_workers_num) - int(new_num_workers)
            for _ in range(int(stop_workers_num)):
                stop_worker(policy = True)

def background_job():
    global manager_active
    manager_active = True
    print("back ground job started")
    print("start")
    while(start):
        while(1):
            print("Scaling begin")
            print(thres_grow, thres_shrink, grow_ratio, shrink_ratio)
            configure_autoscaling_policy(thres_grow, thres_shrink, grow_ratio, shrink_ratio)
            print("Scaling done")
            time.sleep(120)

@webapp.route('/start_background')
def start_background_job():
    if manager_active:
        return render_template('m_main.html', Stop_message = json.dumps("Background autoscaler already running!"))
    pool = ThreadPool(2)
    global start 
    start = True
    pool.schedule(background_job)
    Message = ("Auto-Scaling has started")
    return render_template('m_main.html',Stop_message = json.dumps(Message))

@webapp.route('/configure_background', methods = ['POST'])
def configure_background():
    threshold_grow = request.form.get('threshold_grow', "")
    threshold_shrink = request.form.get('threshold_shrink', "")
    ratio_grow = request.form.get('ratio_grow', "")
    ratio_shrink = request.form.get('ratio_shrink', "")
    
    print(type(threshold_grow))

    if not (threshold_grow.replace('.', '', 1).isdigit() 
            and threshold_shrink.replace('.', '', 1).isdigit()
            and ratio_grow.replace('.', '', 1).isdigit() 
            and ratio_shrink.replace('.', '', 1).isdigit()):
        return render_template('ec2/config.html', invalid = True)

    global thres_grow
    thres_grow = threshold_grow

    global thres_shrink
    thres_shrink = threshold_shrink

    global grow_ratio
    grow_ratio = ratio_grow

    global shrink_ratio
    shrink_ratio = ratio_shrink

    start_background_job()
    print(thres_grow, thres_shrink, grow_ratio, shrink_ratio)
    setting = 'Curent Setting is Grow_ratio:'+str(grow_ratio)+" Shrink Ratio: "+str(shrink_ratio) +" Upper Limit: "+str(thres_grow)+" Lower Threadhold: "+ str(thres_shrink)
    return render_template('ec2/config.html', running = True, setting = setting)
