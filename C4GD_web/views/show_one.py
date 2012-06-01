from flask import abort, request, current_app

from C4GD_web import blueprints


def get_one(name):
    bp = blueprints.BlueprintWithOptions(name, __name__)

    @bp.route('<obj_id>/')
    def show(obj_id):
        blueprint = current_app.blueprints[request.blueprint]
        model = blueprint._register_options['model']
        try:
            result = model.get(obj_id)
        except model.NotFound:
            abort(404)
        else:
            if result is None:
                abort(404)
            template_name = 'blueprints/show_one/%s.haml' % blueprint.name
            return template_name, result

    return bp
