# coding=utf-8
from flask import g, session, request
from storm.locals import *
from C4GD_web import app

import requests
import urllib, urlparse

@app.context_processor
def debug_processor():
    return {
        'DEBUG': app.config['DEBUG'],
        'DEV': app.config['DEV']}


@app.context_processor
def frequent_data():
    if getattr(g, 'is_authenticated', False):
        tenants_with_roles = []
        for tenant in session['tenants']['tenants']['values']:
            tenants_with_roles.append(
                (tenant, session['keystone_scoped'][tenant['id']]['access']['user']['roles']))
        return {'tenants_with_roles': tenants_with_roles}
    return {}

def url_for_other_page(page):
    args = request.args.copy()
    args['page'] = page
    result = '%s?%s' % (
        request.path,
        urllib.urlencode(
            tuple(args.iterlists()), 
            doseq=1))
    return result
app.jinja_env.globals['url_for_other_page'] = url_for_other_page
