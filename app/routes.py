from app import managerapp, stats
from flask import render_template,request, jsonify, redirect, url_for, json
import requests

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
        op_mode = request.form.get('op_mode')
        pool_size = request.form.get('pool_size')
        miss_max = request.form.get('miss_max')
        miss_min = request.form.get('miss_min')
        exp_ratio = request.form.get('exp_ratio')
        shr_ratio = request.form.get('shr_ratio')
        if op_mode == 'Manual':
            print('Mode: ', op_mode, ', Pool Size: ', pool_size)
        elif op_mode == 'Automatic':
            print('Mode: ', op_mode)
            print('Miss Rate Max: ', miss_max, 'Miss Rate Min: ', miss_min)
            print('Expan Ratio: ', exp_ratio, 'Shrink Ratio ', shr_ratio)
        else:
            print('Error: Unknown AutoScalar Operation Mode')
    return render_template('autoscalar_config.html')


@managerapp.route('/reset')
def reset_system():
    """
    The reset commend that delete image data in database and AWS S3
    :return:
    """
    return None

@managerapp.route('/clear')
def clear_memcache():
    """
    The clear commend that clears all the MemCache
    :return:
    """
    return None



