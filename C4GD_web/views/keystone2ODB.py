from flask import make_response

from C4GD_web import app

from C4GD_web.clients import clients

from C4GD_web.utils import neo4j_api_call

@app.route('/convert_keystone_2_odb/', methods=['GET'])
def convert_keystone_2_odb():
    users = clients.keystone.users.list()
    import pdb;pdb.set_trace()
    for user in users:
        
        neo4j_api_call('/users', params={}, method='POST')
    return "OK"

@app.route('/drop_odb_users/', methods=['GET'])
def drop_odb_users():
    pass