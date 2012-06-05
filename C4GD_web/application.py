import sys

import flask
import werkzeug


class FatFlask(flask.Flask):
    jinja_options = werkzeug.ImmutableDict(
        extensions=[
            'jinja2.ext.autoescape',
            'jinja2.ext.with_',
            'hamlish_jinja.HamlishExtension']
    )

    def make_response(self, rv):
        if type(rv) is dict:
            template_name = "/".join(flask.request.endpoint.split('.'))
            result = flask.render_template(
                template_name + self.config['TEMPLATE_EXTENSION'], **rv)
        elif type(rv) in (list, tuple) and len(rv) == 2:
            result = flask.render_template(rv[0], **rv[1])
        else:
            result = rv
        return super(FatFlask, self).make_response(result)

    def full_dispatch_request(self):
        if self.debug:
            return super(FatFlask, self).full_dispatch_request()
        else:
            try:
                return super(FatFlask, self).full_dispatch_request()
            except Exception, error:
                flask.flash(error.message, 'error')
                exc_type, exc_value, tb = sys.exc_info()
                self.log_exception((exc_type, exc_value, tb))
                return flask.render_template('blank.haml')
