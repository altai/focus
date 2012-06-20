#!/usr/bin/python2
# coding=utf-8
if __name__ == "__main__":
    import C4GD_web
    port = C4GD_web.app.config['DEFAULT_APP_PORT']
    C4GD_web.app.run(host='0.0.0.0', port=port if port else 5000)
