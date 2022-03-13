from app import managerapp, stats
from flask import render_template,request, jsonify, redirect, url_for, json


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
        print("New MemCache Setting are: ", capacity, "MB, with ", rep_policy)
    return render_template('memcache_config.html')

@managerapp.route('/autoscalar_config')
def autoscalar_config():
    """
    The configuration page of the AutoScalar rendered here
    - Included the reset button that delete image data in database and AWS S3
    :return:
    """
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



