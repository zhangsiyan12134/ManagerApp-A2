from app import managerapp, scheduler, DEBUG, stats, scalar_config
from flask import render_template, request, flash, jsonify, redirect, url_for, json
from app.stat_data import stats_aws_get_workers, stats_aws_get_stat
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
    stats['MissRate'].append(miss_rate)      # Statistic of aggregated Miss Rate
    stats['HitRate'].append(hit_rate)       # Statistic of aggregated Hit Rate
    stats['Items'].append(total_item )        # Statistic of aggregated Total Num of Items
    stats['Size'].append(total_size)         # Statistic of aggregated Total Size of Contents
    stats['Reqs'].append(total_req)         # Statistic of aggregated Total Requests


# refreshConfiguration function required by frontend
@managerapp.before_first_request
def get_stats_tasks():
    # add the task to scheduler for workers and memcache statistic data updates
    scheduler.add_job(id='insert_dummy_data', func=dummy_data, trigger='interval',
                      seconds=5)
"""scheduler.add_job(id='update_worker_count', func=stats_aws_get_workers, trigger='interval',
                      seconds=managerapp.config['JOB_INTERVAL'])
    scheduler.add_job(id='update_cloudwatch_stats', func=stats_aws_get_stats, trigger='interval',
                      seconds=managerapp.config['JOB_INTERVAL'])
"""


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


@managerapp.route('/autoscalar_config', methods=['GET', 'POST'])
def autoscalar_config():
    """
    The configuration page of the AutoScalar rendered here
    - Included the reset button that delete image data in database and AWS S3
    :return:
    """
    if request.method == 'POST':
        op_mode_str = request.form.get('op_mode')
        pool_size_str = request.form.get('pool_size')
        miss_max_str = request.form.get('miss_max')
        miss_min_str = request.form.get('miss_min')
        exp_ratio_str = request.form.get('exp_ratio')
        shr_ratio_str = request.form.get('shr_ratio')
        if op_mode_str == 'Manual':
            pool_size = int(pool_size_str)
            if 0 < int(pool_size) < 9:
                if DEBUG is True:
                    print('Mode: ', op_mode_str, ', Pool Size: ', pool_size)
                scalar_config['op_mode'] = op_mode_str
                scalar_config['worker'] = pool_size
                flash("Switched to Manual Mode! Applying changes to worker pool...")
            elif DEBUG is True:
                print('Error: Invalid Number of Instance is given')
        elif op_mode_str == 'Automatic':
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
    flash("All Application Data are Deleted!")
    return render_template('autoscalar_config.html', config=scalar_config)


@managerapp.route('/clear')
def clear_memcache():
    """
    The clear commend that clears all the MemCache
    :return:
    """
    flash("All MemCache Cleared!")
    return render_template('memcache_config.html')



