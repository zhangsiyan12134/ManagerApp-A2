import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    AUTOSCALAR_URL = "http://localhost:5003/"
    FRONTEND_URL = "http://localhost:5000/"
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "America/Toronto"
    JOB_INTERVAL = 60  # interval for jobs(in seconds)
    ASW_CONFIG = {
        'REGION': 'us-east-1',
        'AWS_ACCESS_KEY_ID': '',
        'SECRET_ACCESS_KEY': ''
    }
    RDS_CONFIG = {
        'host': 'ece1779.cxbccost2b0y.us-east-1.rds.amazonaws.com',
        'port': 3306,
        'user': '',
        'password': '',
        'database': 'ECE1779'
    }
    INSTANCE_LIST = {
        # a dictionary that contains AWS InstanceID and Private IP pairs
        "i-06ff465c20d0fb338": "172.31.19.26",
        "i-0b81ca5b750466ce5": "172.31.28.166",
        "i-04d4d716f1d677ddf": "172.31.21.22",
        "i-0499cf05aa1ca5ddb": "172.31.20.212",
        "i-08cf1f2da050d9e7c": "172.31.22.94",
        "i-03d068ae131c3fd83": "172.31.25.107",
        "i-0d700be59a58243d2": "172.31.21.0",
        "i-002db696c9c99d3f5": "172.31.30.224"
    }




