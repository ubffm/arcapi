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
        (r"/audit", handlers.GUIHandler),
        (r"/(.*)",
            tornado.web.StaticFileHandler,
            {"path": str(audit_path)},
        ),
        # (r"/audit/(.*)", tornado.web.RedirectHandler, {"url": r"/static/audit/{0}"}),
        # (r"/js/(.*)", tornado.web.RedirectHandler, {"url": "/static/audit/js/{0}"}),
        # (r"/css/(.*)", tornado.web.RedirectHandler, {"url": "/static/audit/css/{0}"}),
        # (r"/img/(.*)", tornado.web.RedirectHandler, {"url": "/static/audit/img/{0}"}),
        # ( r"/(.*)", tornado.web.StaticFileHandler, {"path": str(static_path)}),
        # (r"/audit/(.*)",
        #     tornado.web.StaticFileHandler,
        #     {"path": str(audit_path)},
        # ),
        # (
        #     r"/css/(.*)",
        #     tornado.web.StaticFileHandler,
        #     {"path": str(audit_path / "css")},
        # ),
        # (
        #     r"/js/(.*)",
        #     tornado.web.StaticFileHandler,
        #     {"path": str(audit_path / "js")},
        # ),
        # (
        #     r"/img/(.*)",
        #     tornado.web.StaticFileHandler,
        #     {"path": str(audit_path / "img")},
        # ),
    ],
    static_path=audit_path,
    autoreload=True,
)
port = 8888
print("now servering on", port)
application.listen(port)
tornado.ioloop.IOLoop.current().start()
