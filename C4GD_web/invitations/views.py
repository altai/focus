# coding=utf-8
import hashlib
import datetime

from C4GD_web import app, mail
from C4GD_web.exceptions import GentleException
from forms import InviteForm, InviteRegisterForm

from flask import g, render_template, flash, render_template, url_for, redirect, request
from flaskext.mail import Message

from neo4j_orm import save_invitation, get_invitation_by_hash, \
    update_invitation, create_new_user, get_masks


@app.route('/invite/finish/<invitation_hash>/', methods=['GET', 'POST'])
def invite_finish(invitation_hash):
    id, email, hash, complete = get_invitation_by_hash(invitation_hash)
    if complete == 1:
        flash('Invitation token is already used', 'error')
        return redirect('/')
    form = InviteRegisterForm()
    form.data['email'] = email
    if form.validate_on_submit():
        create_new_user(form.email.data, form.password.data)
        #login new user
        flash('New user was registered successfully', 'info')
        update_invitation(id, email, hash, 1)
        return redirect('/')
    return render_template('invite_registration.haml', form=form, email=email)

@app.route('/invite/', methods=['GET', 'POST'])
def invite():
    def create_invitation_hash(email):
        """ unique hash for invite confirmation link """
        h = hashlib.new('ripemd160')
        h.update(email)
        h.update(str(datetime.datetime.now()))
        return h.hexdigest()       
        
    masks = get_masks()
    form = InviteForm()
    if form.validate_on_submit():
        user_email = form.email.data
        hash = create_invitation_hash(user_email)
        domain = user_email.split('@')[-1]
        if (domain,) not in masks:
            flash('Not allowed mail mask')
            return render_template('invite.haml', form=form, masks=masks)
        save_invitation(user_email, hash, 0)
        invite_link = "http://%s%s" % (request.host, url_for('invite_finish', invitation_hash=hash))
        msg = Message('Invitation', recipients=[user_email])
        msg.body = render_template('InviteEmail/body.txt', invite_link=invite_link)
        try:
            mail.send(msg)
            flash('Invitation sent successfully', 'info')  
        except Exception, e:
            raise GentleException(e.message)
    return render_template('invite.haml', form=form, masks=masks)