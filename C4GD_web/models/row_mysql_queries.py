# TODO(apugachev) consider converting this staff to storm models
import functools

import flask

from C4GD_web.models import orm


def prepare_database_connection(func):
    """Create Storm ORM Store if it does not exist yet."""
    @functools.wraps(func)
    def _wrapped(*args, **kwargs):
        if not hasattr(flask.g, 'inv_store'):
            flask.g.inv_store = orm.get_store('INVITATIONS')
        return func(*args, **kwargs)
    return _wrapped


@prepare_database_connection
def save_invitation(email, hash_code, role):
    flask.g.inv_store.execute(
        'INSERT INTO invitations.invitations SET '
        'email = ?, hash = ?, complete = ?, role = ?',
        (email, hash_code, 0, role))
    flask.g.inv_store.commit()


@prepare_database_connection
def get_invitation_by_hash(invitation_hash):
    return flask.g.inv_store.execute(
        'SELECT * FROM invitations.invitations '
        'WHERE invitations.hash = ?',
        (invitation_hash, )).get_one()


@prepare_database_connection
def update_invitation(invitation_id, email, hash_code):
    flask.g.inv_store.execute(
        'UPDATE invitations.invitations SET '
        'email = ?, hash = ?, complete = ? '
        'WHERE id = ?',
        (email, hash_code, 1, invitation_id))
    flask.g.inv_store.commit()


@prepare_database_connection
def get_masks():
    return flask.g.inv_store.execute(
        'SELECT email_mask FROM invitations.email_masks').get_all()


@prepare_database_connection
def save_recovery(email, hash_code, complete):
    flask.g.inv_store.execute(
        'INSERT INTO invitations.recovery_requests SET '
        'email = ?, hash = ?, complete = ?',
        (email, hash_code, complete))
    flask.g.inv_store.commit()


@prepare_database_connection
def get_recovery_request_by_hash(recovery_hash):
    return flask.g.inv_store.execute(
        'SELECT * FROM invitations.recovery_requests '
        'WHERE recovery_requests.hash = ?', (recovery_hash,)).get_one()
