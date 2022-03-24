from app import managerapp, scheduler, DEBUG, stats, scaler_config, worker_list
from flask import render_template, request, flash, jsonify, redirect, url_for, json
from app.stat_data import stats_get_worker_list, stats_aws_get_worker_list
from app.db_access import update_rds_memcache_config
from app.ec2_access import ec2_start_instance, ec2_pause_instance
from random import seed, uniform, randint
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder


def send_post_request(addr, data):
    """
    Helper function to send POSt request that doesn't require a
    full hreaders
    :param addr: srt: request receiver url
    :param data: dict
    :return:
    """
    try:
        r = requests.post(addr, data=data)
    except requests.exceptions.RequestException as e:
        print("Warning: Exception happened when sending the request")
        if DEBUG is True:
            print(e)


def send_post_request_with_body(addr, params):
    """
    Helper function to send POSt request that require a full
    hreaders
    :param addr: srt: request receiver url
    :param params: dict
    :return:
    """
    data = MultipartEncoder(fields=params)
    headers = {
        'Content-type': data.content_type
    }
    try:
        r = requests.post(addr, data=data, headers=headers)
    except requests.exceptions.RequestException as e:
        print("Warning: Exception happened when sending the request")
        if DEBUG is True:
            print(e)


def worker_auto_start():
    """
    This function will be trigger on the first request to start
    a EC2 instance.
    :return:
    """
    req_addr = managerapp.config['AUTOSCALER_URL']
    response = {
            'mode': 'Manual',
            'add_drop': '1'
        }
    send_post_request_with_body(req_addr, response)
    if DEBUG is True:
        print("Request sent, worker is booting, please wait.")


def dummy_data():
    """
    Function that generate dummy data to test graphs
    :return:
    """
    new_req = randint(0, 2)
    new_put = randint(0, 2)

    total_item = randint(0, 50)
    total_size = uniform(5.0, 25.0)
    total_req = total_item + randint(0, 2)
    hit_rate = new_req / total_req
    miss_rate = new_put / total_req
    print(total_item, total_size, total_req, hit_rate, miss_rate)
    stats['Workers'].append(randint(1, 8))       # Statistic of number of workers
    stats['Workers'].pop(0)
    stats['MissRate'].append(miss_rate)      # Statistic of aggregated Miss Rate
    stats['MissRate'].pop(0)
    stats['HitRate'].append(hit_rate)       # Statistic of aggregated Hit Rate
    stats['HitRate'].pop(0)
    stats['Items'].append(total_item )        # Statistic of aggregated Total Num of Items
    stats['Items'].pop(0)
    stats['Size'].append(total_size)         # Statistic of aggregated Total Size of Contents
    stats['Size'].pop(0)
    stats['Reqs'].append(total_req)         # Statistic of aggregated Total Requests
    stats['Reqs'].pop(0)


@managerapp.before_first_request
def get_stats_tasks():
    # start the very first worker here
    worker_auto_start()
    # add the task to scheduler for workers and memcache statistic data updates
    """scheduler.add_job(id='insert_dummy_data', func=dummy_data, trigger='interval',
                      seconds=5)"""
    # add the task to collect worker data, when worker count is greater than 0, another task
    # that collect the cloudwatch metrics will be added by this function
    stats_get_worker_list()  # run once at the beginning
    scheduler.add_job(id='update_worker_count', func=stats_get_worker_list, trigger='interval',
                      seconds=managerapp.config['JOB_INTERVAL'])


@managerapp.route('/')
@managerapp.route('/stats')
def stats_display():
    """
    The status display of all instances happened here
    :return:
    """
    return render_template('stats_display.html', stats=stats)


@managerapp.route('/memcache_config', methods=['GET', 'POST'])
def memcache_config():
    """
    The configuration page of the MemCache rendered here
    - Included the clear button that clears all the MemCache
    :return:
    """
    if request.method == 'POST':
        capacity = request.form.get('capacity')
        rep_policy = request.form.get('rep_policy')
        if capacity and rep_policy:
            # update the latest memcache configuration in database
            update_rds_memcache_config(int(capacity), rep_policy)
            for instance_id in worker_list.keys():
                req_addr = 'http://' + managerapp.config['INSTANCE_LIST'][instance_id] + ':5001/refreshconfiguration'
                send_post_request(req_addr, None)
            if DEBUG is True:
                print("New MemCache Setting are: ", capacity, "MB, with ", rep_policy)
            flash("Configuration Applied!")
        else:
            flash("Required Parameter(s) are missing!")
    return render_template('memcache_config.html')


@managerapp.route('/clear')
def clear_memcache():
    """
    The clear commend that clears all the MemCache
    :return:
    """
    for instance_id in worker_list.keys():
        req_addr = 'http://' + managerapp.config['INSTANCE_LIST'][instance_id] + ':5001/clear'
        send_post_request(req_addr, None)
    if DEBUG is True:
        print('Clear Requests are sent to workers')
    flash("All MemCache Cleared!")
    return render_template('memcache_config.html')


@managerapp.route('/autoscaler_config', methods=['GET', 'POST'])
def autoscaler_config():
    """
    The configuration page of the AutoScaler rendered here
    - Included the reset button that delete image data in database and AWS S3
    :return:
    """
    if request.method == 'POST':
        op_mode_str = request.form.get('op_mode')
        if op_mode_str == 'Manual':
            scaler_config['op_mode'] = op_mode_str
            # Send the mode change to AutoScaler
            req_addr = managerapp.config['AUTOSCALER_URL']
            response = {
                'mode': 'Manual',
                'add_drop': '0'
            }
            send_post_request_with_body(req_addr, response)
            if DEBUG is True:
                print('Switching to Manual Mode, Pool Size: ', scaler_config['worker'])
            flash("Switched to Manual Mode!")
        elif op_mode_str == 'Automatic':
            miss_max_str = request.form.get('miss_max')
            miss_min_str = request.form.get('miss_min')
            exp_ratio_str = request.form.get('exp_ratio')
            shr_ratio_str = request.form.get('shr_ratio')
            if (not miss_max_str) or (not miss_min_str) or (not exp_ratio_str) or (not shr_ratio_str):
                flash("Required Parameter(s) are missing!")
            else:
                miss_max = float(miss_max_str)
                miss_min = float(miss_min_str)
                exp_ratio = float(exp_ratio_str)
                shr_ratio = float(shr_ratio_str)
                if DEBUG is True:
                    print('Mode: ', op_mode_str)
                    print('Miss Rate Max: ', miss_max, 'Miss Rate Min: ', miss_min)
                    print('Expan Ratio: ', exp_ratio, 'Shrink Ratio ', shr_ratio)
                scaler_config['op_mode'] = op_mode_str
                scaler_config['miss_max'] = miss_max
                scaler_config['miss_min'] = miss_min
                scaler_config['exp_ratio'] = exp_ratio
                scaler_config['shr_ratio'] = shr_ratio
                req_addr = managerapp.config['AUTOSCALER_URL']
                response = {
                    'mode': 'Automatic',
                    'max_miss': miss_max_str,
                    'min_miss': miss_min_str,
                    'expand_ratio': exp_ratio_str,
                    'shrink_ratio': shr_ratio_str
                }
                send_post_request_with_body(req_addr, response)
                flash("Switched to Auto Mode! Applying settings to the AutoScaler")
        elif DEBUG is True:
            print('Error: Unknown AutoScaler Operation Mode')
    return render_template('autoscaler_config.html', config=scaler_config)


@managerapp.route('/reset')
def reset_system():
    """
    The reset commend that delete image data in database and AWS S3
    :return:
    """
    req_addr = managerapp.config['FRONTEND_URL'] + 'api/manager/clear'
    send_post_request(req_addr, None)
    if DEBUG is True:
        print('Reset Requests are sent to FrontEndApp')
    flash("All Application Data are Deleted!")
    return render_template('autoscaler_config.html', config=scaler_config)


@managerapp.route('/start_worker', methods=['GET', 'POST'])
def start_worker():
    """
    Start a worker in manual mode
    :return:
    """
    if scaler_config['op_mode'] != 'Manual':
        scaler_config['op_mode'] = 'Manual'
    # get the current worker lists
    stopped_worker = stats_aws_get_worker_list('stopped')
    pending_worker = stats_aws_get_worker_list('pending')
    if DEBUG is True:
        print('There are', len(stopped_worker), 'running workers, and ', len(pending_worker))

    if pending_worker:
        flash("A worker status is pending, please try again later")
    elif not stopped_worker:
        flash("No free worker is available at the moment.")
    else:
        if scaler_config['worker'] < 8:
            scaler_config['worker'] += 1
            # Send the new configuration to AutoScaler
            req_addr = managerapp.config['AUTOSCALER_URL']
            response = {
                'mode': 'Manual',
                'add_drop': '1'
            }
            send_post_request_with_body(req_addr, response)
            # NOTE: Manual start a EC2 instance is handled by AutoScaler now
            # ec2_start_instance(stopped_worker[0])
            flash("Switched to Manual Mode. Please waiting for worker to boot up.")
        else:
            flash("Maximum Worker is Running!")

        if DEBUG is True:
            print('Switching to Manual Mode, Pool Size: ', scaler_config['worker'])
    return render_template('autoscaler_config.html', config=scaler_config)


@managerapp.route('/pause_worker', methods=['GET', 'POST'])
def pause_worker():
    """
    Pause a worker in manual mode
    :return:
    """
    # get the current worker lists
    running_worker = stats_aws_get_worker_list('running')
    pending_worker = stats_aws_get_worker_list('pending | starting | stopping | shutting-down')
    if DEBUG is True:
        print('There are', len(running_worker), 'running workers, and ', len(pending_worker))

    if pending_worker:
        flash("A worker status is pending, please try again later")
    elif not running_worker:
        flash("All worker is stopped at the moment.")
    else:
        if scaler_config['op_mode'] != 'Manual':
            scaler_config['op_mode'] = 'Manual'
        if scaler_config['worker'] > 1:
            scaler_config['worker'] -= 1
            # Send the new configuration to AutoScaler
            req_addr = managerapp.config['AUTOSCALER_URL']
            response = {
                'mode': 'Manual',
                'add_drop': '-1'
            }
            send_post_request_with_body(req_addr, response)
            # NOTE: Manual start a EC2 instance is handled by AutoScaler now
            # ec2_pause_instance(running_worker[-1])
            flash("Switched to Manual Mode. Please waiting for worker to stop.")
        else:
            flash("At least one worker is required to running.")
        if DEBUG is True:
            print('Switching to Manual Mode, Pool Size: ', scaler_config['worker'])

    return render_template('autoscaler_config.html', config=scaler_config)

