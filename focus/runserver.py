#!/usr/bin/python2
# coding=utf-8

if __name__ == "__main__":
    import focus
    port = focus.app.config['DEFAULT_APP_PORT']
    focus.app.run(host='0.0.0.0', port=port if port else 5000)
