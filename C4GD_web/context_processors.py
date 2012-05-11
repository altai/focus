# coding=utf-8
from flask import g, session
from storm.locals import *
from C4GD_web import app
from models import *
import requests


@app.context_processor
def debug_processor():
    return {
        'DEBUG': app.config['DEBUG'],
        'DEV': app.config['DEV']}


@app.context_processor
def frequent_data():
    if g.is_authenticated:
        tenants_with_roles = []
        for tenant in session['tenants']['tenants']['values']:
            tenants_with_roles.append(
                (tenant, session['keystone_scoped'][tenant['id']]['access']['user']['roles']))
        return {'tenants_with_roles': tenants_with_roles}
    return {}
