from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import C4GD_web

http_server = HTTPServer(WSGIContainer(C4GD_web.app))
http_server.listen(C4GD_web.app.config['DEFAULT_APP_PORT'])
IOLoop.instance().start()
