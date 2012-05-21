from flask.blueprints import Blueprint
from flask import session, render_template, abort, flash, request, current_app

from C4GD_web.utils import nova_get


class BlueprintWithOptions(Blueprint):
    def register(self, app, options, first_registration):
        super(BlueprintWithOptions, self).register(app, options, first_registration)
        self._register_options = options


def get_one(name):

    bp = BlueprintWithOptions(name, __name__)

    @bp.route('<obj_id>/')
    def show(obj_id):
        blueprint = current_app.blueprints[request.blueprint]
        model = blueprint._register_options['model']
        try:
            result = model.get(obj_id)
        except model.NotFound:
            abort(404)
        else:
            template_name = 'blueprints/show_one/%s.haml' % blueprint.name
            return render_template(template_name, **result)
    return bp


