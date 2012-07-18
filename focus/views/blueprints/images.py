# -*- coding: utf-8 -*-

# Focus
# Copyright (C) 2010-2012 Grid Dynamics Consulting Services, Inc
# All Rights Reserved
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program. If not, see
# <http://www.gnu.org/licenses/>.


"""Provides factory of blueprints for image management.

Currently we have only one blueprint for image management - for admins.
Later on we'll need image management for members of tenants, Essex allows it.
"""

import datetime
import json
import os
import time

import flask
from flask import blueprints
from flaskext import principal

import focus
from focus import clients
from focus import utils
from focus.views import environments
from focus.views import forms
from focus.views import pagination


class ProgressRecorder(object):
    """
    This is used to measure progress of a process.

    Instance works as a callback for a process to call.
    It records progress and ETA to application cache under given key.
    """
    def __init__(self, http_client, key, total):
        self.http_client = http_client
        self.key = key
        self.total = total

    def __enter__(self):
        self.start = time.time()
        self.counter = 0
        self.http_client.callback = self
        return self

    def __exit__(self, type, value, traceback):
        flask.current_app.cache.delete(self.key)
        self.http_client.callback = None

    def __call__(self, progress):
        self.counter += progress
        now = time.time()
        seconds_spent = now - self.start
        percent = self.counter * 100.0 / self.total
        if seconds_spent:
            speed = self.counter / seconds_spent
            remainder = self.total - self.counter
            eta = now + remainder / speed
            eta = (datetime.datetime.utcfromtimestamp(eta).
                   isoformat().split('.')[0].replace('T', ' '))
        else:
            speed = 0.0
            eta = u'∞'
            seconds_spent = 0.0

        flask.current_app.cache.set(
            self.key, {
                'transferred': self.counter,
                'total': self.total,
                'time_spent': '%0.2f' % seconds_spent,
                'percent': percent,
                'speed': '%0.2f' % speed,
                'eta': eta,
            })


def get_images_list():
    """Return list of images visible for given condigions.

    If g.tenant_id is not set it is admin blueprint.
    We have to show only images owned by systenant, which are also
    public (can be protected as well (we set it so, but other tools can
    change this attribute or set it to a wrong value from the beginning).

    If g.tenant_id is set it is project blueprint.
    We have to show the same images as for admin blueprint _and_
    images owned by current project (attribute "owner" must be equal to
    g.tenant_id) no matter if image is public/protected.
    NOTE(apugachev):
    Currently for some reason Glance does not return list of images owned
    by tenant with id '1' even if they are public - if they are requested
    through token issued for some other project then '1'.

    That's why we combine image lists here in case if list is for project.
    """
    admin_id = clients.get_systenant_id()
    is_global = lambda x: x.owner == admin_id and x.is_public
    result = filter(
        is_global,
        clients.admin_clients().glance.images.list())
    if getattr(flask.g, 'tenant_id', None):
        result.extend(filter(
            lambda x: x.owner == flask.g.tenant_id and x not in result,
            clients.user_clients(flask.g.tenant_id).glance.images.list()))
    result = sorted(result, key=lambda x: x.name)
    return result

@focus.app.route('/fast-upload-response/', methods=['POST'])
def fast_upload_response():
    """Respond to request from nginx-upload.

    Move image from nginx-upload temp location to another temp location
    to avoid cleanup. Return path temp location.
    """
    src = os.path.abspath(flask.request.form['file.path'])
    if src.startswith(flask.current_app.config['UPLOADS_DEFAULT_DEST']):
        return flask.make_response(name)
    else:
        flask.current_app.logger.error('Tried to trigger upload finish for %s',
                                       str(flask.request.form))
        return flask.jsonify({
                'status': 'error',
                'message': 'Invalid path of upload.'
                })



def get_bp(name):
    """Return blueprint for Image management."""
    bp = blueprints.Blueprint(name, __name__)

    @bp.route('<image_id>/', methods=['GET'])
    def show(image_id):
        """Present details page for single image object.

        Tries using both Glance and Nova services because they provide
        different info set about an image.
        """
        glance_image = clients.admin_clients().glance.images.get(image_id)
        nova_image = clients.admin_clients().nova.images.get(image_id)
        return {'glance_image': glance_image,
                'nova_image': nova_image}

    def get_tenant_id():
        return getattr(flask.g, 'tenant_id', clients.get_systenant_id())

    @bp.route('')
    def index():
        """List images.

        Admin (global visibility level) should see only images from
        systenant. Project members should see images for projects only.
        """
        images = get_images_list()
        if not hasattr(flask.g, 'tenant_id'):
            images = filter(
                lambda x: getattr(x, 'is_public', False),
                images)
        p = pagination.Pagination(images)
        data = p.slice(images)
        return {
            'images': data,
            'pagination': p,
            'delete_form': forms.DeleteForm()
        }

    @bp.route('new/', methods=['GET'])
    def new():
        """Present image upload form.

        TODO(apugachev): remove from templ location images older then X hours
        """
        images = get_images_list()
        check = lambda f: lambda x: getattr(x, 'container_format') == f
        kernels = filter(check('aki'), images)
        initrds = filter(check('ari'), images)
        dump = lambda d: json.dumps([x.properties for x in d])
        return {
            'kernel_list': dump(kernels),
            'initrd_list': dump(initrds)
        }

    @bp.route('upload/', methods=['POST'])
    def upload():
        """Save uploaded file.

        Handles AJAX call, saves file in temp location, returns filename.

        TODO(apugachev): remove from templ location images older then X hours
        """
        storage = flask.request.files['file']
        filename = focus.files_uploads.save(storage)
        flask.current_app.cache.set(
            os.path.basename(filename),
            {'transferred': -1})
        return filename

    @bp.route('create/', methods=['POST'])
    def create():
        """Create image via Glance API.

        - validates form
        - creates image via API
        - cleans up tmp file
        - returns successful message

        New image uploaded in tenant systenant publicly if blueprint is in
        admin context. Otherwise image uploaded in the tenant used for the
        project and is not public. With default Glance settings (owner means
        tenant) this would restrict access to the image for members of the
        project.

        During the process of upload ongoing progress is memcached.

        TODO(apugachev): remove from templ location images older then X hours
        """
        # TODO(apugachev): validate thoroughly, do not rely on js to do it
        uploaded_filename = focus.files_uploads.path(
            flask.request.form['uploaded_filename'])
        tenant_id = get_tenant_id()
        properties = {
            'image_state': 'available',
            'project_id': tenant_id,
            'architecture': 'x86_64',
            'image_location': 'local'}
        if flask.request.form['upload_type'] == 'rootfs':
            properties['kernel_id'] = flask.request.form['kernel']
            properties['ramdisk_id'] = flask.request.form['initrd']
        try:
            kwargs = {
                'name': flask.request.form['name'],
                'container_format': flask.request.form['container'],
                'disk_format': flask.request.form['disk'],
                'data': open(uploaded_filename),
                'is_public': not hasattr(flask.g, 'tenant_id'),
                'properties': properties,
            }
        except IOError, e:
            e.public_message = 'Uploaded file is missing'
            flask.current_app.logger.error(str(e))
            raise
        try:
            user_clients = clients.user_clients(tenant_id)
            callback = ProgressRecorder(
                user_clients.http_client,
                os.path.basename(uploaded_filename),
                os.fstat(kwargs['data'].fileno()).st_size)
            with callback:
                img = user_clients.image.images.create(**kwargs)
        except RuntimeError as e:
            flask.flash(e.message, 'error')
        else:
            flask.flash(
                'Image with ID %s was registered.' % img.id,
                'success')
        finally:
            try:
                kwargs['data'].close()
                os.unlink(uploaded_filename)
            except OSError:
                # nothing to do, temporal file was removed by something
                pass
        # NOTE(apugachev) for big this will fail to load and BrokenPipe
        # will be raised inside Flask
        return flask.make_response('')

    @bp.route('progress/<uploaded_filename>/')
    def progress(uploaded_filename):
        r = flask.current_app.cache.get(uploaded_filename)
        return flask.jsonify(r or {})

    @bp.route('<image_id>/delete/', methods=['POST'])
    def delete(image_id):
        image = clients.admin_clients().glance.images.get(image_id)
        owner = getattr(image, 'owner')
        if owner == clients.get_systenant_id():
            principal.Permission(('role', 'admin')).test()
        else:
            principal.Permission(('role', 'member', owner)).test()
        form = forms.DeleteForm()
        if form.validate_on_submit():
            image.delete()
            flask.flash('Image successfully deleted', 'success')
        else:
            flask.flash('Invalid form', 'error')
        return flask.redirect(flask.url_for('.index'))

    return bp


ABP = environments.admin(get_bp('global_images'))
PBP = environments.project(get_bp('project_images'))
