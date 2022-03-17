from flask import g
from app import managerapp, DEBUG, stat_data
import mysql.connector
from mysql.connector import errorcode


def connect_to_database():
    try:
        return mysql.connector.connect(
            host=managerapp.config['RDS_CONFIG']['host'],
            port=managerapp.config['RDS_CONFIG']['port'],
            user=managerapp.config['RDS_CONFIG']['user'],
            password=managerapp.config['RDS_CONFIG']['password'],
            database=managerapp.config['RDS_CONFIG']['database']
        )
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

def update_rds_worker_count(worker_cnt):
    """
    This function get the number of running workers from RDS. If the count is different
    to the actual running count, update the count in RDS, then notify the FrontEnd about
    the changes
    This function will be called by stats_get_worker_list that executed by scheduler
    :return:
    """
    cnx = connect_to_database()  # Create connection to db
    cursor = cnx.cursor()
    query = "SELECT num_instances FROM ECE1779.cachepool_stats;"
    cursor.execute(query)
    row = cursor.fetchone()  # Retrieve the first row that contains the count
    # Check if database has the count
    if row is None:
        query = "INSERT INTO ECE1779.cachepool_stats (num_instances) VALUE (%s);"
        cursor.execute(query, (worker_cnt,))
        cnx.commit()
        if DEBUG is True:
            print('No valid count exist on RDS. New value', worker_cnt, 'is added.')
    elif row[0] != worker_cnt:
        query = "UPDATE ECE1779.cachepool_stats SET num_instances = %s;"
        cursor.execute(query, (worker_cnt,))
        cnx.commit()
        # TODO: send request to FrontendApp to notify the changes
        if DEBUG is True:
            print('Count on RDS is outdated. Value', worker_cnt, 'is updated.')
    elif DEBUG is True:
        print('Count on RDS is update, no need to update.')

