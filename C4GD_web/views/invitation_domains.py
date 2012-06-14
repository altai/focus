import flask
from flask import blueprints
from flaskext import principal
from C4GD_web.models import orm
from C4GD_web.views import pagination
from C4GD_web.views import forms


bp = blueprints.Blueprint(
    'invitation_domains', __name__, url_prefix='/global/invitation-domains/')


@bp.before_request
def prepare():
    principal.Permission(('role', 'admin')).test()
    flask.g.store = orm.get_store('INVITATIONS')


@bp.route('')
def index():
    total_count = flask.g.store.execute(
        'SELECT count(*) from email_masks').get_one()[0]
    p = pagination.Pagination(total_count)
    rows = flask.g.store.execute(
        'SELECT * from email_masks ORDER BY email_mask LIMIT ?, ?',
        p.limit_offset()).get_all()
    objects = map(lambda row: dict(zip(('id', 'email_mask'), row)), rows)
    return {
        'pagination': p,
        'objects': objects,
        'delete_form': forms.DeleteForm()}


@bp.route('delete/<object_id>/', methods=['POST'])
def delete(object_id):
    import pdb; pdb.set_trace()
    form = forms.DeleteForm()
    if form.validate_on_submit():
        flask.g.store.execute(
            'DELETE FROM email_masks WHERE id = ? LIMIT 1', (object_id,))
        flask.g.store.commit()
        flask.flash('Email mask removed.', 'success')
        return flask.redirect(flask.url_for('.index'))
    return {'form': form}


@bp.route('new/', methods=['GET', 'POST'])
def new():
    form = forms.CreateEmailMask()
    if form.validate_on_submit():
        flask.g.store.execute(
            'INSERT INTO email_masks (email_mask) VALUES (?)',
            (form.email_mask.data, ))
        flask.g.store.commit()
        flask.flash('Email mask created.', 'success')
        return flask.redirect(flask.url_for('.index'))
    return {'form': form}
