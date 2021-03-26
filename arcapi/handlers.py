import asyncio
import concurrent.futures
import functools
import json
import tornado.web
import re

from arc import picaqueries, filters, solrtools
from arc.decode import debracket
import arc.config
import deromanize
from deromanize.keygenerator import CombinatorialExplosion
import string
from arc.nlitools import solrmarc
from typing import (
    Sequence,
    NamedTuple,
    Tuple,
    TypedDict,
    Union,
    Dict,
    List,
    cast,
)


nli_template = "https://www.nli.org.il/en/books/NNL_ALEPH{}/NLI"


def getquery(words):
    words = filter(None, [s.strip(string.punctuation) for s in words])
    return solrtools.join(words, fuzzy=True)


empty = object()


def execute_once(func):
    result = empty

    @functools.wraps(func)
    def wrapper():
        nonlocal result
        if result is empty:
            result = func()
        return result

    return wrapper


@execute_once
def getsession() -> arc.config.Session:
    session = arc.config.Session.fromconfig(asynchro=True)
    session.records.session.connection().engine.dispose()
    session.add_decoders(("new", "old", "pi"), fix_numerals=True)
    session.add_core("nlibooks")
    session.add_termdict()
    return session


@execute_once
def getpool() -> concurrent.futures.ProcessPoolExecutor:
    return concurrent.futures.ProcessPoolExecutor()


def delegate(func, *args):
    return asyncio.get_event_loop().run_in_executor(getpool(), func, *args)


jsondecode = json.JSONDecoder().decode
jsonencode = json.JSONEncoder(ensure_ascii=False).encode


def split_title(text: str) -> Tuple[str, str, str]:
    remainder, _, resp = text.partition(" / ")
    main, _, sub = remainder.partition(" : ")
    return main, sub, resp


Reps = Sequence[str]


class RepList(TypedDict):
    key: str
    reps: Reps


def mk_rlist_serializable(rlist: deromanize.ReplacementList) -> RepList:
    reps = [str(rep) for rep in rlist[:20]]
    key = rlist.key if isinstance(rlist, deromanize.ReplacementList) else rlist
    return {"key": key, "reps": reps}


def text_to_replists(text):
    if not text:
        return []
    chunks = getsession().getchunks(text)
    rlists = picaqueries.prerank(chunks, getsession())
    return [mk_rlist_serializable(rl) for rl in rlists]


def title_to_replist_subfields(title: str):
    return solrmarc.RepTitle(
        *(
            [r["reps"] for r in text_to_replists(t)] if t else None
            for t in split_title(title)
        )
    )


def has_heb(string: str):
    line = filters.Line(debracket(string))
    if not (line.has("only_old") or line.has("only_new")):
        return False
    if line.has("foreign", "yiddish_ending", "arabic_article", "english_y"):
        return False
    return True


def person_to_replists(person: str):
    if not has_heb(person):
        return None
    replists = text_to_replists(person)
    for i, rlist in enumerate(replists):
        replists[i] = rlist["reps"][:5]
    return replists


def ppn2record_and_rlist(ppn):
    record = getsession().records[ppn]
    title = picaqueries.gettranstitle(record)
    serializable_rlists = text_to_replists(title.joined)
    return dict(record=record.to_dict(), replists=serializable_rlists)


def prepare_doc(solr_nli_doc):
    doc = jsondecode(solr_nli_doc["originalData"])
    doc["allnames"] = solr_nli_doc.get("allnames", [])
    return doc


async def query_nli(words):
    try:
        query = getquery(words)
    except solrtools.EmptyQuery:
        return []
    out = await getsession().cores.nlibooks.run_query("alltitles:" + query)

    return [prepare_doc(d) for d in out["docs"]]


class MalformedRecord(Exception):
    pass


class NoTitleGiven(Exception):
    pass


def prep_record(record: Dict[str, Union[str, List[str]]]):
    # mutation
    for k, v in record.items():
        if isinstance(v, str):
            record[k] = [v]
        elif not isinstance(v, list):
            raise MalformedRecord(record)
    return cast(Dict[str, List[str]], record)


title_t = "title"
isPartOf_t = "isPartOf"


def gettitle(record):
    try:
        title = record["title"][0]
        if not title:
            raise NoTitleGiven(record)
        return (title_t, title)
    except (KeyError, IndexError):
        try:
            title = record["isPartOf"][0]
            if not title:
                raise NoTitleGiven(record)
            return (isPartOf_t, title)
        except (KeyError, IndexError):
            raise NoTitleGiven(record)


class TitleReplists(NamedTuple):
    type: str
    replists: dict


def record2replist(record: Dict[str, Union[str, List[str]]]):
    record_ = prep_record(record)
    title_type, title = gettitle(record_)
    title = re.sub(r"^\{([Hh]\w*-)\}\s*", r"\1", title)
    title_replists = title_to_replist_subfields(title)
    creator_replists = map(person_to_replists, record.get("creator", []))
    return (TitleReplists(title_type, title_replists), list(creator_replists))


def json_records2replists(json_records: str):
    records = jsondecode(json_records)
    out = []
    for record in records:
        try:
            out.append((record, record2replist(record)))
        except (NoTitleGiven, CombinatorialExplosion) as e:
            out.append((record, e))
    return out


def words_of_replists(replists):
    return [w["reps"][0] for w in replists]


def words_of_title_replists(title: solrmarc.RepTitle):
    out = []
    for field in title:
        if field:
            out.extend(word[0] for word in field)
    return out


def error(msg, record, **kwargs):
    return {
        "type": "error",
        "message": msg,
        "record": record,
        **kwargs
    }


def join_title(main, sub, resp):
    out = [main]
    if sub:
        out.extend((":", sub))
    if resp:
        out.extend(("/", resp))
    return " ".join(out)


async def record_with_results(record, replists_or_error):
    if isinstance(replists_or_error, Exception):
        return error(replists_or_error.__class__.__name__, record)
    (title_type, title_reps), creator_replists = replists_or_error
    words = words_of_title_replists(title_reps)
    try:
        generated_title = join_title(*(" ".join(w[0] for w in r) if r else None for r in title_reps))
    except TypeError:
        return error("NoMainTitle", record)
    results = []
    for doc in await query_nli(words):
        try:
            results.append(solrmarc.mk_api_doc(doc))
        except solrmarc.NoIdentifier:
            pass
        except picaqueries.NoMainTitle:
            pass
    ranked_results = await delegate(
        solrmarc.rank_results2,
        record.get("creator", []),
        creator_replists,
        None,  # publisher
        None,  # publisher_reps
        record.get("date", []),
        title_reps,
        results,
    )

    if not ranked_results:
        for result in results:
            result["title"] = [t.joined for t in result["title"]]
        return dict(
            type="unverified",
            record=record,
            converted=generated_title,
            top_query_result=results[0]["title"] if results else None,
            creator_replists=creator_replists,
        )

    top = ranked_results[0]
    title = top["title"]
    heb_title = title.replace("<<", "{", 1).replace(">>", "}", 1)
    return dict(
        type="verified",
        record=record,
        converted=generated_title,
        creator_replists=creator_replists,
        matched_title={
            "text": heb_title,
            "link": nli_template.format(top["doc"]["identifier"]),
            "diff": top["diff"],
            "criteria": top["criteria"],
        }
    )


class APIHandler(tornado.web.RequestHandler):
    async def get(self, json_records):
        records_n_replists = await delegate(
            json_records2replists, json_records
        )
        sep_sym = "["
        for record, replists_or_error in records_n_replists:
            self.write(sep_sym)
            self.write(
                jsonencode(
                    await record_with_results(record, replists_or_error)
                )
            )
            sep_sym = "\n,"
        self.write("\n]")


class PPNHandler(tornado.web.RequestHandler):
    async def get(self, ppn):
        try:
            result = await delegate(ppn2record_and_rlist, ppn)
        except KeyError:
            self.write(
                jsonencode({"Error": "No such PPN %s", "type": "PPNError"})
                % ppn
            )
            return

        self.write(jsonencode(result))


class TextHandler(tornado.web.RequestHandler):
    async def get(self, text):
        result = await delegate(text_to_replists, text)
        self.write(jsonencode(result))


class NLIQueryHandler(tornado.web.RequestHandler):
    async def get(self, data):
        out = await query_nli(jsondecode(data))
        self.write(jsonencode(out))


class TextAndQueryHandler(tornado.web.RequestHandler):
    async def get(self, text):
        text = await delegate(text_to_replists, text)
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
