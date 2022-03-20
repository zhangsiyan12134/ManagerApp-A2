from flask import Flask
from flask_apscheduler import APScheduler
from config import Config
import boto3

managerapp = Flask(__name__)

global stats
global scaler_config
global worker_list
global DEBUG

DEBUG = True

worker_list = {}    # {instance_id: 0|1}: 0=stopped; 1=running

scaler_config = {}
scaler_config['op_mode'] = 'Manual'
scaler_config['worker'] = 1
scaler_config['miss_max'] = 0.8
scaler_config['miss_min'] = 0.2
scaler_config['exp_ratio'] = 2.0
scaler_config['shr_ratio'] = 0.5

stats = {}
stats['Workers'] = [1] * 30     # Statistic of number of workers
stats['MissRate'] = [0.0] * 30  # Statistic of aggregated Miss Rate
stats['HitRate'] = [0.0] * 30   # Statistic of aggregated Hit Rate
stats['Items'] = [0] * 30       # Statistic of aggregated Total Num of Items
stats['Size'] = [0.0] * 30      # Statistic of aggregated Total Size of Contents
stats['Reqs'] = [0] * 30        # Statistic of aggregated Total Requests

ec2_resource = boto3.resource(
        'ec2',
        region_name=Config.ASW_CONFIG['REGION'],
        aws_access_key_id=Config.ASW_CONFIG['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=Config.ASW_CONFIG['SECRET_ACCESS_KEY']
    )

cloudwatch_client = boto3.client(
        'cloudwatch',
        region_name=Config.ASW_CONFIG['REGION'],
        aws_access_key_id=Config.ASW_CONFIG['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=Config.ASW_CONFIG['SECRET_ACCESS_KEY']
    )

ec2_client = boto3.client(
        'ec2',
        region_name=Config.ASW_CONFIG['REGION'],
        aws_access_key_id=Config.ASW_CONFIG['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=Config.ASW_CONFIG['SECRET_ACCESS_KEY']
    )

managerapp.config.from_object(Config)

scheduler = APScheduler()
scheduler.init_app(managerapp)
scheduler.start()

from app import routes
