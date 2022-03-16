from app import managerapp, scheduler, DEBUG, stats, scalar_config, worker_list
from flask import render_template, request, flash, jsonify, redirect, url_for, json
from app.stat_data import stats_get_worker_list, stats_aws_get_stat
from random import seed, uniform, randint
import requests


def dummy_data():
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

# refreshConfiguration function required by frontend
@managerapp.before_first_request
def get_stats_tasks():
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
        # update the latest memcache configuration in database here
        url = managerapp.config['AUTOSCALAR_URL'] + "/refreshconfiguration"
        requests.post(url)  # send request to autoscalar
        if DEBUG is True:
            print("New MemCache Setting are: ", capacity, "MB, with ", rep_policy)
    return render_template('memcache_config.html')


@managerapp.route('/clear')
def clear_memcache():
    """
    The clear commend that clears all the MemCache
    :return:
    """
    for instance_id in worker_list.keys():
        req_addr = 'http://' + managerapp.config['INSTANCE_LIST'][instance_id] + ':5000/clear'
        requests.post(req_addr)
    if DEBUG is True:
        print('Clear Requests are sent to workers')
    flash("All MemCache Cleared!")
    return render_template('memcache_config.html')


@managerapp.route('/autoscalar_config', methods=['GET', 'POST'])
def autoscalar_config():
    """
    The configuration page of the AutoScalar rendered here
    - Included the reset button that delete image data in database and AWS S3
    :return:
    """
    if request.method == 'POST':
        op_mode_str = request.form.get('op_mode')
        if op_mode_str == 'Manual':
            scalar_config['op_mode'] = op_mode_str
            # TODO: send request to autoscalar here
            if DEBUG is True:
                print('Switching to Manual Mode, Pool Size: ', scalar_config['worker'])
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
                scalar_config['op_mode'] = op_mode_str
                scalar_config['miss_max'] = miss_max
                scalar_config['miss_min'] = miss_min
                scalar_config['exp_ratio'] = exp_ratio
                scalar_config['shr_ratio'] = shr_ratio
                # TODO: send request to autoscalar here
                flash("Switched to Auto Mode! Applying settings to the AutoScalar")
        elif DEBUG is True:
            print('Error: Unknown AutoScalar Operation Mode')
    return render_template('autoscalar_config.html', config=scalar_config)


@managerapp.route('/reset')
def reset_system():
    """
    The reset commend that delete image data in database and AWS S3
    :return:
    """
    req_addr = 'http://' + managerapp.config['FRONTEND_URL'] + '/reset'
    # TODO: add reset request here
    if DEBUG is True:
        print('Reset Requests are sent to FrontEndApp')
    flash("All Application Data are Deleted!")
    return render_template('autoscalar_config.html', config=scalar_config)


@managerapp.route('/start_worker', methods=['GET', 'POST'])
def start_worker():
    """
    Start a worker in manual mode
    :return:
    """
    if scalar_config['op_mode'] is not 'Manual':
        scalar_config['op_mode'] = 'Manual'
    if scalar_config['worker'] < 8:
        scalar_config['worker'] += 1
        # TODO: add request to AutoScalar here
        # TODO: add start instance here if necessary
        flash("Switched to Manual Mode. Pool size increased.")
    else:
        flash("Maximum Worker is Running!")

    if DEBUG is True:
        print('Switching to Manual Mode, Pool Size: ', scalar_config['worker'])
    return render_template('autoscalar_config.html', config=scalar_config)


@managerapp.route('/pause_worker', methods=['GET', 'POST'])
def pause_worker():
    """
    Pause a worker in manual mode
    :return:
    """
    if scalar_config['op_mode'] is not 'Manual':
        scalar_config['op_mode'] = 'Manual'
    if scalar_config['worker'] > 1:
        scalar_config['worker'] -= 1
        # TODO: add request to AutoScalar here
        # TODO: add start instance here if necessary
        flash("Switched to Manual Mode. Pool size decreased.")
    else:
        flash("At least one worker is required to running.")

    if DEBUG is True:
        print('Switching to Manual Mode, Pool Size: ', scalar_config['worker'])
    return render_template('autoscalar_config.html', config=scalar_config)

