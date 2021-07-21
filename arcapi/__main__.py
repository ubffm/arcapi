import tornado.ioloop
import tornado.web

from arcapi import config
from arcapi import handlers


application = tornado.web.Application(
    [
        (r"/api/(.*)", handlers.APIHandler),
        (r"/", tornado.web.RedirectHandler, {"url": "/index.html"}),
        (
            r"/(.*)",
            tornado.web.StaticFileHandler,
            {"path": str(config.project_dir / "arcapi" / "static")},
        ),
    ]
)
port = 8888
print("now servering on", port)
application.listen(port)
tornado.ioloop.IOLoop.current().start()
