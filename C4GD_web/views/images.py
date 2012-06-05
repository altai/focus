import json
import os

import flask
from flask import blueprints
from flaskext import principal
from C4GD_web.models import abstract

import forms
import C4GD_web


def get_bp(name):
    '''
    Return blueprint for Image management.

    index (list images), create image(upload), delete image.
    Each view function of the blueprint gets protected by Principal.
    User must have permission ('role', 'admin') to access global management
    of images and ('project', <unicode:project_id>) to access a project image
    management.
    
    Now this works for global admins only. Later we'll find out how to 
    implelement this for project memebers as well.
    '''
    bp = blueprints.Blueprint(name, __name__)
    
    @bp.url_value_preprocessor
    def global_or_project(endpoint, values):
        flask.g.project_id = values.pop('project_id', None)


    @bp.route('')
    def index():
        '''
        Present images of global or project visibility level
        
        '''
        images = abstract.Image.list()
        return {'images': images}

    @bp.route('new/', methods=['GET', 'POST'])
    def new():
        '''
        Present add image form, save add image form.

        POST:
        - validate
        - create image
        - cleanup tmp file
        - return successful message
        '''
        if flask.request.method == 'POST':
            # TODO(apugachev): validate thoroughly, do not rely on js to do it
            
            kw = {}
            if flask.request.form['upload_type'] == 'rootfs':
                kw['kernel_id'] = flask.request.form['kernel']
                kw['ramdisk_id'] = flask.request.form['initrd']
            path = C4GD_web.files_uploads.path(
                    flask.request.form['uploaded_filename'])
            try:
                response = abstract.Image.create(
                    flask.current_app.config['DEFAULT_TENANT_ID'],
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
                    pass

        images = abstract.Image.list(limit=1000000)
        kernels = filter(lambda x: x['container_format'] == 'aki', images)
        initrds = filter(lambda x: x['container_format'] == 'ari', images)
        rootfss = filter(
            lambda x: x['container_format'] not in ['aki', 'ari'], images)

        return {
            'kernel_list': json.dumps(kernels),
            'initrd_list': json.dumps(initrds)
            }

    @bp.route('new/upload/', methods=['POST'])
    def upload():
        '''
        Saves uploaded filed.

        save, return filename.
        '''
        storage = flask.request.files['file']
        filename = C4GD_web.files_uploads.save(storage)
        return filename

    return bp

