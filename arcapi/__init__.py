__version__ = "0.1.0"

import asyncio
import concurrent.futures
import json
from arc import picaqueries
from arc import config
import deromanize
import tornado.ioloop
import tornado.web
import string
from arc import solrtools
import compose
import dbm


class PpnDB(compose.Struct):
    db = ...
    curkey = None

    @classmethod
    def frompath(cls, dbpath):
        return cls(dbm.open(str(dbpath), "c"))

    def __getitem__(self, key):
        return self.db[key].decode()

    def __setitem__(self, key, value):
        self.db[key] = value

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __next__(self):
        while True:
            if not self.curkey:
                ppn = self.db.firstkey()
            else:
                ppn = self.db.nextkey(self.curkey)
            self.curkey = ppn
            if not ppn:
                return next(self)
            if not self[ppn]:
                return ppn.decode()

    def __iter__(self):
        return self


ppns = PpnDB.frompath("ppns.dbm")


def run(func, *args):
    return asyncio.get_event_loop().run_in_executor(func, *args)


def getquery(words):
    words = filter(None, [s.strip(string.punctuation) for s in words])
    return solrtools.join(words, fuzzy=True)


def getsession() -> config.Session:
    try:
        return getsession._session
    except AttributeError:
        pass

    session = config.Session.fromconfig(asynchro=True)
    session.records.session.connection().engine.dispose()
    session.add_decoders(("new", "old"), fix_numerals=True)
    session.add_core("nlibooks")
    # print(type(session.cores.nlibooks))
    session.add_termdict()
    getsession._session = session
    return session


jsondecode = json.JSONDecoder().decode
jsonencode = json.JSONEncoder(ensure_ascii=False).encode
executor = concurrent.futures.ProcessPoolExecutor(2)


def mk_rlist_serializable(rlist: deromanize.ReplacementList):
    reps = [str(rep) for rep in rlist]
    key = rlist.key if isinstance(rlist, deromanize.ReplacementList) else rlist
    return dict(key=key, reps=reps)


def text_to_replists(text):
    chunks = getsession().getchunks(text)
    rlists = picaqueries.prerank(chunks, getsession())
    return [mk_rlist_serializable(rl) for rl in rlists]


def ppn2record_and_rlist(ppn):
    record = getsession().records[ppn]
    title = picaqueries.gettranstitle(record)
    serializable_rlists = text_to_replists(title.joined)
    return dict(record=record.to_dict(), replists=serializable_rlists)


class PPNHandler(tornado.web.RequestHandler):
    async def get(self, ppn):
        try:
            result = await run(executor, ppn2record_and_rlist, ppn)
        except KeyError:
            self.write('{"Error": "No such PPN %s", "type": "PPNError"}' % ppn)
            return

        self.write(jsonencode(result))


class TextHandler(tornado.web.RequestHandler):
    async def get(self, text):
        result = await run(executor, text_to_replists, text)
        self.write(jsonencode(result))


class NLIQueryHandler(tornado.web.RequestHandler):
    async def get(self, data):
        words = jsondecode(data)
        query = getquery(words)
        out = await getsession().cores.nlibooks.run_query(
            "alltitles:" + query, fl=["originalData"]
        )
        self.write("[%s]" % ",".join(d["originalData"] for d in out["docs"]))


class NextHandler(tornado.web.RequestHandler):
    async def get(self):
        self.write(next(ppns))


class PassHandler(tornado.web.RequestHandler):
    async def get(self, ppn):
        ppns[ppn] = "null"
        self.write(next(ppns))


class SubmitHandler(tornado.web.RequestHandler):
    async def get(self, hairball):
        print(hairball)
        data = jsondecode(hairball)
        ppns[data["ppn"]] = hairball
        self.write(next(ppns))


def main():
    application = tornado.web.Application(
        [
            (r"/ppn/(.*)", PPNHandler),
            (r"/text/(.*)", TextHandler),
            (r"/nli/(.*)", NLIQueryHandler),
            (r"/next/", NextHandler),
            (r"/pass/(.*)", PassHandler),
            (r"/submit/(.*)", SubmitHandler),
            # (r"/(.*)", tornado.web.StaticFileHandler),
        ]
    )
    port = 8888
    print("now servering on", port)
    application.listen(port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
