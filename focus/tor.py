from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

import focus


http_server = HTTPServer(WSGIContainer(focus.app))
http_server.listen(focus.app.config['DEFAULT_APP_PORT'])
IOLoop.instance().start()
