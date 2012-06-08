from flask import make_response

from C4GD_web import app

from C4GD_web.clients import clients

from C4GD_web.utils import neo4j_api_call, create_hashed_password

import MySQLdb

@app.route('/convert_keystone_2_odb/', methods=['GET'])
def convert_keystone_2_odb():
    users = clients.keystone.users.list()
    for user in users:
        params = {
            'username': user.name
        }
        if user.email is None:
            params.update({
                'email': user.name + "@griddynamics.com"
            })
        else:
            params.update({
                'email': user.email
            })
        neo4j_api_call('/users', params=params, method='POST')
    return "OK"

@app.route('/drop_odb_users/', methods=['GET'])
def drop_odb_users():
    pass

@app.route('/update_passwords_in_ODB/', methods=['GET'])
def update_passwords_in_ODB():
    db = MySQLdb.connect(host="172.18.36.11", user="nova", passwd="nova", db="keystone")
    c = db.cursor()
    ic = db.cursor()
    
    odb_users = neo4j_api_call('/users', {}, method='GET')
    for odb_user in odb_users:
        c.execute("select id from user where name='%s';" % odb_user['username'])
        keystone_id = c.fetchone()[0]
        ic.execute("select ec2_credential.access from ec2_credential where user_id = %s", [keystone_id])
        for password in ic.fetchall():
            if not ":" in password[0]:
                neo4j_api_call('/users', {
                    'username': odb_user['username'],
                    'login': odb_user['login'],
                    'email': odb_user['email'],
                    'id': odb_user['id'],
                    'passwordHash': create_hashed_password(password[0])}, 
                method='PUT')
                break
            

    return "OK"