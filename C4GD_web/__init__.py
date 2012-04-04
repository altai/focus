from flask import Flask, g
from storm.locals import Store, create_database
             


# app initialization
app = Flask(__name__)
# config
app.config.from_object('C4GD_web.default_settings')
app.config.from_envvar('TOOLZA_CONFIG', silent=True)

# db connection
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

import C4GD_web.views
