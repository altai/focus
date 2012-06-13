"""Provides factory of blueprints for image management.

Currently we have only one blueprint for image management - for admins.
Later on we'll need image management for members of tenants, Essex allows it.
"""

import json
import os

import flask
from flask import blueprints
from flaskext import principal

import C4GD_web
from C4GD_web.models import abstract
from C4GD_web.clients import clients
from C4GD_web.views import forms
from C4GD_web.views import pagination


def get_bp(name):
    """Return blueprint for Image management.

    index (list images), create image(upload), delete image.
    Each view function of the blueprint gets protected by Principal.
    User must have permission ('role', 'admin') to access global management
    of images and ('project', <unicode:project_id>) to access a project image
    management.
    
    Now this works for global admins only. Later we'll find out how to 
    implelement this for project memebers as well.
    """
    bp = blueprints.Blueprint(name, __name__)
    
    @bp.url_value_preprocessor
    def global_or_project(endpoint, values):
        """Binds project id to g if project od exists.

        The blueprint can be used in a project or in admin context.
        """
        flask.g.project_id = values.pop('project_id', None)

    @bp.url_defaults
    def put_project_id(endpoint, values):
        """Substitute project_id arg with default"""
        if 'project_id' in values or not hasattr(flask.g, 'project_id'):
            return
        if flask.current_app.url_map.is_endpoint_expecting(
            endpoint, 'project_id'):
            values['project_id'] = flask.g.project_id

    @bp.before_request
    def authorize():
        """Check user permissions.

        Depends on project id existing.
        """
        if flask.g.project_id:
            need = ('role', 'member', flask.g.project_id)
        else:
            need = ('role', 'admin')
        principal.Permission(need).test()

    @bp.route('<image_id>/', methods=['GET'])
    def show(image_id):
        """Present details page for single image object.

        Tries using both Glance and Nova services because they provide
        different info set about an image.
        """
        glance_image = clients.glance.images.get(image_id)
        nova_image = clients.nova.images.get(image_id)
        return {'glance_image': glance_image,
                'nova_image': nova_image}

    def get_tenant_id():
        return flask.g.project_id or \
            flask.current_app.config['KEYSTONE_CONF']['admin_tenant_id']

    def get_images_list():
        ids = [flask.current_app.config['KEYSTONE_CONF']['admin_tenant_id']]
        if flask.g.project_id:
            ids.append(flask.g.project_id)
        images = [x for x in clients.glance.images.list() if x.owner in ids]
        return images

    @bp.route('')
    def index():
        """List images.
        
        Admin (global visibility level) should see only images from 
        systenant. Project members should see images for projects only.
        """
        images = get_images_list()
        p = pagination.Pagination(images)
        data = p.slice(images)
        return {
            'images': data,
            'pagination': p,
            'delete_form': forms.DeleteForm()
            }

    @bp.route('new/', methods=['GET', 'POST'])
    def new():
        """Upload image.

        New image uploaded in tenant systenant publicly if blueprint is in
        admin context. Otherwise image uploaded in the tenant used for the
        project and is not public. With default Glance settigns this would
        restrict access to the image for members of the project.

        POST:
        - validate
        - create image
        - cleanup tmp file
        - return successful message
        """
        if flask.request.method == 'POST':
            # TODO(apugachev): validate thoroughly, do not rely on js to do it
            
            kw = {}
            if flask.request.form['upload_type'] == 'rootfs':
                kw['kernel_id'] = flask.request.form['kernel']
                kw['ramdisk_id'] = flask.request.form['initrd']
                kw['is_public'] = not bool(flask.g.project_id)
                kw['protected'] = True
            path = C4GD_web.files_uploads.path(
                    flask.request.form['uploaded_filename'])
            try:
                response = abstract.Image.create(
                    get_tenant_id(),
                    flask.request.form['name'],
                    flask.request.form['container'],
                    flask.request.form['disk'],
                    path,
                    **kw
                    )
            except RuntimeError, e:
                flask.flash(e.message, 'error')
            else:
                if flask.current_app.debug:
                    flask.current_app.logger.info(response)
                flask.flash(
                    'Image with ID %s was registered.' % response['id'],
                    'success')
                return flask.redirect(flask.url_for('.new'))
            finally:
                try:
                    os.unlink(path)
                except OSError:
                    # nothing to do, temporal file was removed by something
                    pass
        images = get_images_list()
        kernels = filter(lambda x: getattr(x, 'container_format') == 'aki', images)
        initrds = filter(lambda x: getattr(x, 'container_format') == 'ari', images)
        # rootfss = filter(
        #     lambda x: x.get('container_format') not in ['aki', 'ari'], images)

        return {
            'kernel_list': json.dumps([x.properties for x in kernels]),
            'initrd_list': json.dumps([x.properties for x in initrds])
            }

    @bp.route('new/upload/', methods=['POST'])
    def upload():
        """
        Saves uploaded filed.

        save, return filename.
        """
        storage = flask.request.files['file']
        filename = C4GD_web.files_uploads.save(storage)
        return filename

    @bp.route('<image_id>/delete/', methods=['POST'])
    def delete(image_id):
        image = clients.glance.images.get(image_id)
        owner = getattr(image, 'owner')
        if owner == flask.current_app.config['KEYSTONE_CONF']\
                ['admin_tenant_id']:
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
