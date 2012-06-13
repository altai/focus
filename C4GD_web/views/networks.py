import flask
from flask import blueprints
from flaskext import principal
from C4GD_web.models import orm

bp = blueprints.Blueprint('networks', __name__, url_prefix='/global/networks/')


@bp.before_request
def authorize():
    principal.Permission(('role', 'admin')).test()


@bp.route('')
def index():
    store = orm.get_store('RO')
    # read from database
    return {'objects': objects}


@bp.route('new/')
def new():
    pass
