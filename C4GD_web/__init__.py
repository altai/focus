# coding=utf-8
from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, session
from werkzeug import ImmutableDict
from flask_memcache_session import Session
from werkzeug.contrib.cache import MemcachedCache


# initialize app
class FlaskWithHamlish(Flask):
    jinja_options = ImmutableDict(
        extensions=[
            'jinja2.ext.autoescape',
            'jinja2.ext.with_',
            'hamlish_jinja.HamlishExtension']
    )

app = FlaskWithHamlish(__name__)

app.jinja_env.hamlish_mode = 'indented' # if you want to set hamlish settings

app.cache = MemcachedCache(
    ['127.0.0.1:11211'],
    default_timeout=100000,
    key_prefix='focus')
app.session_interface = Session()

# config app
app.config.from_object('C4GD_web.default_settings')
app.config.from_object('C4GD_web.local_settings')

if not app.debug:
    import logging, sys
    logging.basicConfig(stream=sys.stderr)

# import flesh
import C4GD_web.callbacks
import C4GD_web.context_processors
import C4GD_web.views
