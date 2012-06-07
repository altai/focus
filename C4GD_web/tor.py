from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from C4GD_web import app

http_server = HTTPServer(WSGIContainer(app))
http_server.listen(app.config['DEFAULT_APP_PORT'])
IOLoop.instance().start()
