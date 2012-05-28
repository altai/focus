import sys

from flask import Flask, flash, redirect, url_for, render_template, request
from werkzeug import ImmutableDict

from .exceptions import  KeystoneExpiresException, GentleException


class FatFlask(Flask):
    jinja_options = ImmutableDict(
        extensions=[
            'jinja2.ext.autoescape',
            'jinja2.ext.with_',
            'hamlish_jinja.HamlishExtension']
    )

    def make_response(self, rv):
        if type(rv) is dict:
            template_name = "/".join(request.endpoint.split('.'))
            result = render_template(
                template_name + self.config['TEMPLATE_EXTENSION'], **rv)
        elif type(rv) in (list, tuple) and len(rv) == 2:
            result = render_template(rv[0], **rv[1])
        else:
            result = rv
        return super(FatFlask, self).make_response(result)
