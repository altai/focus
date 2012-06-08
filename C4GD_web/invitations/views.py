# coding=utf-8
import hashlib
import datetime

from C4GD_web import app, mail
from C4GD_web.exceptions import GentleException
from forms import InviteForm, InviteRegisterForm

from flask import g, render_template, flash, render_template, url_for, redirect, \
    request, session
    
from flaskext.mail import Message
from flaskext import principal
from flaskext.wtf import TextField, Required

from row_mysql_queries import save_invitation, get_invitation_by_hash, \
    update_invitation, get_masks
    
from C4GD_web.utils import neo4j_api_call, create_hash_from_data
from C4GD_web.views.authentication import authenticate_user, register_user



@app.route('/invite/finish/<invitation_hash>/', methods=['GET', 'POST'])
def invite_finish(invitation_hash):
    id, email, hash, complete, role = get_invitation_by_hash(invitation_hash)
    if complete == 1:
        flash('Invitation token is already used', 'error')
        return redirect('/')
    form = InviteRegisterForm()
    username = email.split("@")[0]
    form.email.data = email
    username_is_taken = False
    try:
        user = neo4j_api_call('/users',{
            "email": email 
        }, 'GET')[0]
        flash('This username is already taken. Please, choose another one', 'warning')
        username_field = TextField('Username', [Required()]).bind(form, 'username') 
        form.username = username_field 
        form._fields['username'] = username_field
        username_is_taken = True
    except Exception, e:
        if form.validate_on_submit():
            new_odb_user = register_user(form.username.data, form.email.data, form.password.data, role)
            if new_odb_user is not None:
                authenticate_user(form.email.data, form.password.data)
                update_invitation(id, email, hash, 1)
                return redirect('/')
    form.username.data = username
    return render_template('invite_registration.haml', 
                           form=form, 
                           email=email,
                           username=username,
                           username_is_taken=username_is_taken)

@app.route('/invite/', methods=['GET', 'POST'])
def invite():
    masks = get_masks()
    form = InviteForm()
    if form.validate_on_submit():
        user_email = form.email.data
        try:
            user = neo4j_api_call('/users',{
                "email": user_email 
            }, 'GET')[0]
            flash('User with email "%s" is already registered' % user_email, 'error')
            return render_template('invite.haml', form=form, masks=masks)
        except KeyError, GentleException:
            pass
        hash = create_hash_from_data(user_email)
        domain = user_email.split('@')[-1]
        if (domain,) not in masks:
            flash('Not allowed email mask')
            return render_template('invite.haml', form=form, masks=masks)
        save_invitation(user_email, hash, 0, form.role.data)
        invite_link = "http://%s%s" % (request.host, url_for('invite_finish', invitation_hash=hash))
        msg = Message('Invitation', recipients=[user_email])
        msg.body = render_template('InviteEmail/body.txt', invite_link=invite_link)
        try:
            mail.send(msg)
            flash('Invitation sent successfully', 'info')  
        except Exception, e:
            raise GentleException(e.message)
    return render_template('invite.haml', 
                           form=form, 
                           masks=masks,
                           )
