import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    AUTOSCALAR_URL = "http://localhost:5004"
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "America/Toronto"
    JOB_INTERVAL = 60  # interval for jobs(in seconds)
    DB_CONFIG = {
        'user': 'siyan',
        'password': 'zhangsiyan123456',
        'host': 'localhost',
        'database': 'Assignment_1'
    }
    ASW_CONFIG = {
        'REGION': 'us-east-1',
        'AWS_ACCESS_KEY_ID': '',
        'SECRET_ACCESS_KEY': ''
    }




