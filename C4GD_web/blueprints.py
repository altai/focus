from flask import blueprints


class BlueprintWithOptions(blueprints.Blueprint):
    def register(self, app, options, first_registration):
        super(BlueprintWithOptions, self).register(app, options, first_registration)
        self._register_options = options
