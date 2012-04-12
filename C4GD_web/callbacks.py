from flask import g, session
from storm.locals import Store, create_database
from C4GD_web import app
from models import User


@app.before_request
def create_storm_store():
    database = create_database(
        'mysql://%s:%s@%s:%s/%s' % (
            app.config['DB_USER'],
            app.config['DB_PASS'],
            app.config['DB_HOST'],
            app.config['DB_PORT'],
            app.config['DB_NAME']))
    g.store = Store(database) 

@app.after_request
def commit_storm_store(response):
    g.store.commit()
    return response

@app.teardown_request
def commit_storm_store_optionally(exception):
    if hasattr(g, 'store'):
        g.store.commit()

@app.before_request
def load_authenticated_user():
    if 'user_id' in session:
        g.user = g.store.find(
            User, id=session['user_id'], enabled=True).one()
