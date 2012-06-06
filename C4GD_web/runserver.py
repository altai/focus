#!/usr/bin/python2
# coding=utf-8
from C4GD_web import app


if __name__ == "__main__":
    from C4GD_web import app
    port = app.config['DEFAULT_APP_PORT']
    app.run(host='0.0.0.0', port=port if port else 5000)