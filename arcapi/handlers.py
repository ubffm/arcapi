import asyncio
import concurrent.futures
import functools
import json
import tornado.web

from arc import picaqueries
import arc.config
import deromanize
import string
from arc import solrtools
from arc.nlitools import solrmarc
from typing import List

nli_template = "https://www.nli.org.il/en/books/NNL_ALEPH{}/NLI"


def getquery(words):
    words = filter(None, [s.strip(string.punctuation) for s in words])
    return solrtools.join(words, fuzzy=True)


empty = object()


def getter(func):
    result = empty

    @functools.wraps(func)
    def wrapper():
        nonlocal result
        if result is empty:
            result = func()
        return result

    return wrapper


@getter
def getsession() -> arc.config.Session:
    session = arc.config.Session.fromconfig(asynchro=True)
    session.records.session.connection().engine.dispose()
    session.add_decoders(("new", "old"), fix_numerals=True)
    session.add_core("nlibooks")
    session.add_termdict()
    return session


@getter
def getpool() -> concurrent.futures.ProcessPoolExecutor:
    return concurrent.futures.ProcessPoolExecutor()


def parallel(func, *args):
    return asyncio.get_event_loop().run_in_executor(getpool(), func, *args)


jsondecode = json.JSONDecoder().decode
jsonencode = json.JSONEncoder(ensure_ascii=False).encode


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
    prep_record(record)
    return text_to_replists(record["title"][0])


def json_records2replists(
    json_records: str,
) -> List[deromanize.ReplacementList]:
    records = jsondecode(json_records)
    replists = map(record2replist, records)
    return list(zip(records, replists))


def words_of_replists(replists):
    return [w["reps"][0] for w in replists]


async def record_with_results(record, replists):
    results = await query_nli(words_of_replists(replists))
    results = await parallel(
        solrmarc.rank_results,
        record.get("creator"),
        record.get("date"),
        [x["reps"] for x in replists],
        results,
    )
    results = [r["doc"] for r in results]
    title = picaqueries.Title(*solrmarc.gettitle(results[0])).text
    record["title"].append(title.replace("<<", "{").replace(">>", "}"))
    for result in results:
        record.setdefault("relation", []).append(
            nli_template.format(result["controlfields"]["001"])
        )
    return record


class APIHandler(tornado.web.RequestHandler):
    async def get(self, json_records):
        records_n_replists = await parallel(
            json_records2replists, json_records
        )
        sep_sym = "["
        for record, replists in records_n_replists:
            self.write(sep_sym)
            self.write(jsonencode(await record_with_results(record, replists)))
            sep_sym = "\n,"
        self.write("\n]")


class PPNHandler(tornado.web.RequestHandler):
    async def get(self, ppn):
        try:
            result = await parallel(ppn2record_and_rlist, ppn)
        except KeyError:
            self.write(
                jsonencode({"Error": "No such PPN %s", "type": "PPNError"})
                % ppn
            )
            return

        self.write(jsonencode(result))


class TextHandler(tornado.web.RequestHandler):
    async def get(self, text):
        result = await parallel(text_to_replists, text)
        self.write(jsonencode(result))


class NLIQueryHandler(tornado.web.RequestHandler):
    async def get(self, data):
        out = await query_nli(jsondecode(data))
        self.write(jsonencode(out))


class TextAndQueryHandler(tornado.web.RequestHandler):
    async def get(self, text):
        text = await parallel(text_to_replists, text)
        words = words_of_replists(text)
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
