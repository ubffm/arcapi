import tornado.ioloop
import tornado.web

from arcapi import config
from arcapi import handlers

static_path = config.project_dir / "arcapi" / "static"
audit_path = static_path / "audit"


application = tornado.web.Application(
    [
        (r"/api/(.*)", handlers.APIHandler),
        (r"/with-replacements/(.*)", handlers.RecordsAndRepsHandler),
        (r"/text/(.*)", handlers.TextHandler),
        (r"/", tornado.web.RedirectHandler, {"url": "/static/index.html"}),
        (r"/audit/(.*)", tornado.web.RedirectHandler, {"url": r"/static/audit/{1}"}),
        (r"/js/(.*)", tornado.web.RedirectHandler, {"url": "/static/audit/js/{1}"}),
        (r"/css/(.*)", tornado.web.RedirectHandler, {"url": "/static/audit/css/{1}"}),
        # ( r"/(.*)", tornado.web.StaticFileHandler, {"path": str(static_path)}),
        # (r"/audit/(.*)",
        #     tornado.web.StaticFileHandler,
        #     {"path": str(audit_path)},
        # ),
        # (
        #     r"/audit/css/(.*)",
        #     tornado.web.StaticFileHandler,
        #     {"path": str(audit_path / "css")},
        # ),
        # (
        #     r"/audit/js/(.*)",
        #     tornado.web.StaticFileHandler,
        #     {"path": str(audit_path / "js")},
        # ),
        # (
        #     r"/audit/img/(.*)",
        #     tornado.web.StaticFileHandler,
        #     {"path": str(audit_path / "img")},
        # ),
    ],
    static_path=static_path,
)
port = 8888
print("now servering on", port)
application.listen(port)
tornado.ioloop.IOLoop.current().start()
