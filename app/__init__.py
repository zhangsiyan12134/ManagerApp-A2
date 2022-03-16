from flask import Flask
from flask_apscheduler import APScheduler
from config import Config
import boto3

managerapp = Flask(__name__)

global stats
global scalar_config
global DEBUG

DEBUG = True

scalar_config = {}
scalar_config['op_mode'] = 'Manual'
scalar_config['worker'] = 1
scalar_config['miss_max'] = 0.8
scalar_config['miss_min'] = 0.2
scalar_config['exp_ratio'] = 2.0
scalar_config['shr_ratio'] = 0.5

stats = {}
stats['Workers'] = [1]       # Statistic of number of workers
stats['MissRate'] = [0.0]      # Statistic of aggregated Miss Rate
stats['HitRate'] = [0.0]       # Statistic of aggregated Hit Rate
stats['Items'] = [0]         # Statistic of aggregated Total Num of Items
stats['Size'] = [0.0]          # Statistic of aggregated Total Size of Contents
stats['Reqs'] = [0]          # Statistic of aggregated Total Requests

ec2_client = boto3.resource(
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

managerapp.config.from_object(Config)

scheduler = APScheduler()
scheduler.init_app(managerapp)
scheduler.start()

from app import routes
