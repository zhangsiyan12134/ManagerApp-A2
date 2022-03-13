from flask import g
from app import managerapp

import mysql.connector


def connect_to_database():
    return mysql.connector.connect(user=managerapp.config['DB_CONFIG']['user'],
                                   password=managerapp.config['DB_CONFIG']['password'],
                                   host=managerapp.config['DB_CONFIG']['host'],
                                   database=managerapp.config['DB_CONFIG']['database'])


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db
