import asyncio
import concurrent.futures
import json
import tornado.web

from arc import picaqueries
import arc.config
import deromanize
import string
from arc import solrtools
from typing import List

from libaaron import pipe, pmap


def parallel(pool, func, *args):
    return asyncio.get_event_loop().run_in_executor(pool, func, *args)


def getquery(words):
    words = filter(None, [s.strip(string.punctuation) for s in words])
    return solrtools.join(words, fuzzy=True)


def getsession() -> arc.config.Session:
    try:
        return getsession._session
    except AttributeError:
        pass

    session = arc.config.Session.fromconfig(asynchro=True)
    session.records.session.connection().engine.dispose()
    session.add_decoders(("new", "old"), fix_numerals=True)
    session.add_core("nlibooks")
    session.add_termdict()
    getsession._session = session
    return session


jsondecode = json.JSONDecoder().decode
jsonencode = json.JSONEncoder(ensure_ascii=False).encode
pool = concurrent.futures.ProcessPoolExecutor()


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


async def query_nli(words):
    out = await getsession().cores.nlibooks.run_query(
        "alltitles:" + getquery(words), fl=["originalData"]
    )
    return [jsondecode(d["originalData"]) for d in out["docs"]]


class MalformedRecord(Exception):
    pass


def prep_record(record: dict):
    # mutation
    for k, v in record.items():
        if isinstance(v, str):
            record[k] = [v]
        elif not isinstance(v, list):
            raise MalformedRecord(record)


def record2replist(record):
    session = getsession()
    prep_record(record)


def json_records2replists(
    json_records: str,
) -> List[deromanize.ReplacementList]:
    records = jsondecode(json_records)
    replists = map(record2replist, records)
    return list(zip(records, replists))


class APIHandler(tornado.web.RequestHandler):
    async def get(self, json_records):
        result = await parallel(pool, json_records2replists, json_records)
        self.write(jsonencode(result))


class PPNHandler(tornado.web.RequestHandler):
    async def get(self, ppn):
        try:
            result = await parallel(pool, ppn2record_and_rlist, ppn)
        except KeyError:
            self.write(
                jsonencode({"Error": "No such PPN %s", "type": "PPNError"})
                % ppn
            )
            return

        self.write(jsonencode(result))


class TextHandler(tornado.web.RequestHandler):
    async def get(self, text):
        result = await parallel(pool, text_to_replists, text)
        self.write(jsonencode(result))


class NLIQueryHandler(tornado.web.RequestHandler):
    async def get(self, data):
        out = await query_nli(jsondecode(data))
        self.write("[%s]" % ",".join(out))


class TextAndQueryHandler(tornado.web.RequestHandler):
    async def get(self, text):
        text = await parallel(pool, text_to_replists, text)
        words = [w["reps"][0] for w in text]
        results = await query_nli(words)
        self.write(jsonencode({"conversion": text, "matches": results}))


class NextHandler(tornado.web.RequestHandler):
    async def get(self):
        from arcapi.ppns import ppns

        self.write(next(ppns))


class PassHandler(tornado.web.RequestHandler):
    async def get(self, ppn):
        from arcapi.ppns import ppns

        ppns[ppn] = "null"
        self.write(next(ppns))


class SubmitHandler(tornado.web.RequestHandler):
    async def get(self, hairball):
        from arcapi.ppns import ppns

        data = jsondecode(hairball)
        ppns[data["ppn"]] = hairball
        self.write(next(ppns))
