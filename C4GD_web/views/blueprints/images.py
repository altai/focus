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
from C4GD_web import clients
from C4GD_web import utils
from C4GD_web.models import abstract
from C4GD_web.views import environments
from C4GD_web.views import forms
from C4GD_web.views import pagination


def get_images_list():
    """Return list of images visible for given condigions.

    If g.tenant_id is not set it is admin blueprint.
    We have to show only images owned by DEFAULT_TENANT_ID, which are also
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
    admin_id = flask.current_app.config['DEFAULT_TENANT_ID']
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
        return getattr(flask.g, 'tenant_id', None) or \
            flask.current_app.config['DEFAULT_TENANT_ID']

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
                kw['is_public'] = not hasattr(flask.g, 'tenant_id')
                kw['protected'] = True
            path = C4GD_web.files_uploads.path(
                flask.request.form['uploaded_filename'])
            try:
                if get_tenant_id() not in flask.session['keystone_scoped']:
                    utils.obtain_scoped(get_tenant_id())
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
                return flask.redirect(flask.url_for('.index'))
            finally:
                try:
                    os.unlink(path)
                except OSError:
                    # nothing to do, temporal file was removed by something
                    pass
        images = get_images_list()
        kernels = filter(
            lambda x: getattr(x, 'container_format') == 'aki',
            images)
        initrds = filter(
            lambda x: getattr(x, 'container_format') == 'ari',
            images)

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
        image = clients.admin_clients().glance.images.get(image_id)
        owner = getattr(image, 'owner')
        if owner == flask.current_app.config['DEFAULT_TENANT_ID']:
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
