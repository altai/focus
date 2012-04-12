from flask import render_template
from flask.views import View
from C4GD_web.decorators import login_required


class BaseView(View):
    methods = ['GET', 'POST']
    decorators = [login_required]

    def render(self, result):
        if type(result) is tuple:
            return render_template(result[0], **result[1])
        return result
