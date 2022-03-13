from flask import Flask
from config import Config
import boto3
managerapp = Flask(__name__)

global stats


stats = {}
stats['Workers'] = []       # Statistic of number of workers
stats['MissRate'] = []      # Statistic of aggregated Miss Rate
stats['HitRate'] = []       # Statistic of aggregated Hit Rate
stats['Items'] = []         # Statistic of aggregated Total Num of Items
stats['Size'] = []          # Statistic of aggregated Total Size of Contents
stats['Reqs'] = []          # Statistic of aggregated Total Requests


client = boto3.client(
        'cloudwatch',
        Config.ASW_CONFIG['REGION'],
        aws_access_key_id=Config.ASW_CONFIG['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=Config.ASW_CONFIG['SECRET_ACCESS_KEY']
    )

managerapp.config.from_object(Config)

from app import routes
