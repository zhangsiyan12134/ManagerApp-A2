import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    AUTOSCALAR_URL = "http://localhost:5004"
    FRONTEND_URL = "http://localhost:5000"
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
        "i-07e8cb89884703402": "54.164.28.184"
    }




