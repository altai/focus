from C4GD_web import app

from flask import render_template, request, redirect, url_for, flash

from C4GD_web.utils import keystone_get

from .pagination import Pagination, per_page

from C4GD_web.views.forms import DeleteUserForm 


#  Roles available from the DB 'keystone' table 'roles'  
#+----+----------------------+------+------------+
#| id | name                 | desc | service_id |
#+----+----------------------+------+------------+
#|  1 | Admin                | NULL |       NULL |
#|  2 | Member               | NULL |       NULL |
#|  3 | KeystoneServiceAdmin | NULL |       NULL |
#|  4 | projectmanager       | NULL |       NULL |
#|  5 | cloudadmin           | NULL |       NULL |
#|  6 | itsec                | NULL |       NULL |
#|  7 | sysadmin             | NULL |       NULL |
#|  8 | netadmin             | NULL |       NULL |
#|  9 | developer            | NULL |       NULL |
#| 10 | DNS_Admin            | NULL |       NULL |
#+----+----------------------+------+------------+
#    IMPORTANT:
#    Should be taken through API from keystone.

USER_ROLES = {
    "1" :  'Admin',
    "2" : 'Member',
    "3" : 'KeystoneServiceAdmin',
    "4" : 'projectmanager',
    "5" : 'cloudadmin',
    "6" : 'itsec',
    "7" : 'sysadmin',
    "8" : 'netadmin',
    "9" : 'developer',
    "10": 'DNS_Admin'
}

@app.route('/users/', methods=['GET'])
def list_users():
    """
    List users.
    """
    PER_PAGE = 20
    page = int(request.args.get('page', 1))
    users_response = keystone_get('/users', 
                         {'marker': 1, 
                         'limit': 1000000},
                         is_admin=True)
    users_list = users_response['users']['values']
    pagination = Pagination(page, PER_PAGE, len(users_list))
    data = users_list[(page-1)*PER_PAGE:page*PER_PAGE]
    
    for user in data:
        form = DeleteUserForm()
        form.user_id.data = user['id']
        user['delete_form'] = form
    
    
    return render_template('project_views/list_users.haml', 
                           pagination=pagination,
                           data=data)
    
@app.route('/users/<user_id>/details/', methods=['GET'])
def user_details(user_id):
    user_request = keystone_get('/users/%s/' % user_id, is_admin=True)
    user = user_request['user']
    
    user_roles = keystone_get('/users/%s/roleRefs' % user['id'],
                          is_admin=True)['roles']['values']
                          
    tenants_request = keystone_get('/tenants', is_admin=True)
    tenants = tenants_request['tenants']['values']
    tenants_dict = {}
    for t in tenants:
        tenants_dict[t['id']] = t['name']
    
    for role in user_roles:
        role['role'] = USER_ROLES[role['roleId']]  
        if 'tenantId' in role:
            if role['tenantId'] in tenants_dict:
                role['tenantName'] = tenants_dict[role['tenantId']]
            else:
                role['tenantName'] = "Tenant: %s" % role['tenantId']
    return render_template('project_views/user_details.haml', 
                           user=user,
                           user_roles=user_roles)

    
@app.route('/users/delete/', methods=['POST'])
def delete_user():
    form = DeleteUserForm()
    if form.validate_on_submit():
        flash('User was deleted', 'success')
    else:
        flash('User was not deleted', 'error')
    return redirect(url_for('list_users'))