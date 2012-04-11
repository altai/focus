from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template
from werkzeug import ImmutableDict

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

# config app
app.config.from_object('C4GD_web.default_settings')
app.config.from_envvar('C4GD_WEB_CONFIG', silent=True)

# import flesh
import C4GD_web.callbacks
import C4GD_web.context_processors
import C4GD_web.views
