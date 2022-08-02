import asyncio
import concurrent.futures
import functools
import json
import tornado.web
import re
import libaaron

from arc import picaqueries, filters, solrtools
from arc.decode import debracket
from arcapi import config
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
punctuation_and_spaces = string.punctuation + string.whitespace


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
    # return concurrent.futures.ProcessPoolExecutor(max_workers=1)
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


class NotLatin(Exception):
    pass


def mk_rlist_serializable(rlist: deromanize.ReplacementList) -> RepList:
    reps = [str(rep) for rep in rlist[:20]]
    key = rlist.key if isinstance(rlist, deromanize.ReplacementList) else rlist
    return {"key": key, "reps": reps}


def text_to_replists(text):
    session = getsession()
    if not text:
        return [], None, None
    text = text.replace("s̆", "š")
    chunks, input_info = session.getchunks(text)
    rlists, conversion_info = session.usecache(
        chunks,
        dictionary=session.termdict,
        spelling_fallback=True,
    )
    return (
        [mk_rlist_serializable(rl) for rl in rlists],
        input_info,
        conversion_info,
    )


def _merge_d(d1, d2):
    if d1 is None:
        return None
    else:
        return {**d1, **d2}


def format_diagnostic_info(field_infos):
    input_infos = []
    conversion_infos = []
    for ii, ci in field_infos:
        if ii:
            ii = ii._asdict()
            ci = ci._asdict()
            ii["standard"] = ii["standard"].value
        input_infos.append(ii)
        conversion_infos.append(ci)
    m1, s1, r1 = input_infos
    m2, s2, r2 = conversion_infos
    return {
        "main_title": _merge_d(m1, m2),
        "subtitle": _merge_d(s1, s2),
        "responsibility": _merge_d(r1, r2),
    }


def title_to_replist_subfields(title: str):
    non_filing_article = False
    non_filing_match = NON_FILING.match(title)
    if non_filing_match:
        title = non_filing_match.group(1) + title[non_filing_match.end() :]
        non_filing_article = non_filing_match
    fields = []
    infos = []
    for t in split_title(title):
        if t == ([], None):
            fields.append(None)
            infos.append(None)
        else:
            replists, input_info, conversion_info = text_to_replists(t)
            fields.append([r["reps"] for r in replists])
            infos.append((input_info, conversion_info))
    return solrmarc.RepTitle(*fields), infos, non_filing_article


def has_heb(string: str):
    line = filters.Line(debracket(string))
    if not (line.has("only_old") or line.has("only_new")):
        return False
    if line.has("foreign", "yiddish_ending", "arabic_article", "english_y"):
        return False
    return True


def person_to_replists(person: str):
    if not has_heb(person):
        return None, None
    replists, input_info, conversion_info = text_to_replists(person)
    for i, rlist in enumerate(replists):
        replists[i] = rlist["reps"][:5]
    return replists, input_info


def ppn2record_and_rlist(ppn):
    record = getsession().records[ppn]
    title = picaqueries.gettranstitle(record)
    serializable_rlists, input_info, conversion_info = text_to_replists(
        title.joined
    )
    return dict(
        record=record.to_dict(),
        replists=serializable_rlists,
        input_info=input_info,
    )


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
        if isinstance(v, (str, int)):
            record[k] = [v]
        elif not isinstance(v, list):
            raise MalformedRecord(record)
    return cast(Dict[str, Union[List[str], List[int]]], record)


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


InfoPair = Tuple[arc.config.InputInfo, arc.config.ConversionInfo]


class TitleReplists(NamedTuple):
    type: str
    replists: dict
    field_infos: List[InfoPair]
    non_filing_article: bool


NON_FILING = re.compile(r"^\{([Hh]\w*-)(\s*)\}(\s*)")


def islatin(infos: List[InfoPair]):
    input_info, _ = infos[0]
    if input_info is None:
        return True
    return not (input_info.standard == arc.config.Standard.not_latin)


def record2replist(record: Dict[str, Union[str, List[str]]]):
    non_filing_article = False

    record_ = prep_record(record)
    title_type, title = gettitle(record_)
    non_filing_match = NON_FILING.match(title)
    if non_filing_match:
        title = non_filing_match.group(1) + title[non_filing_match.end() :]
        non_filing_article = True
    title_replists, infos, non_filing_article = title_to_replist_subfields(title)
    if not islatin(infos):
        raise NotLatin("the input is not latin script")
    creator_replists = (
        person_to_replists(c)[0] for c in record.get("creator", [])
    )
    return (
        TitleReplists(title_type, title_replists, infos, non_filing_article),
        list(creator_replists),
    )


class InputNotArray(Exception):
    pass


def json_records2replists(json_records: str):
    try:
        records = jsondecode(json_records)
    except json.JSONDecodeError as e:
        return [(json_records, e)]
    out = []
    if not isinstance(records, list):
        e = InputNotArray("api input should be an array of record objects")
        return [(records, e)]
    for record in records:
        try:
            out.append((record, record2replist(record)))
        except (NoTitleGiven, CombinatorialExplosion, NotLatin) as e:
            out.append((record, e))
        except Exception:
            print(record)
            raise
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
    return {"type": "error", "message": msg, "record": record, **kwargs}


def join_title(main, sub, resp):
    out = [main]
    if sub:
        out.extend((":", sub))
    if resp:
        out.extend(("/", resp))
    return " ".join(out)


async def record_with_results_and_replists(record, replists_or_error):
    if isinstance(replists_or_error, Exception):
        return error(repr(replists_or_error), record), None
    title_reps, creator_replists = replists_or_error
    words = words_of_title_replists(title_reps.replists)
    try:
        generated_title = join_title(
            *(
                " ".join(w[0] for w in r) if r else None
                for r in title_reps.replists
            )
        )
    except TypeError:
        return error("NoMainTitle", record), None
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
        title_reps.replists,
        results,
    )
    if title_reps.non_filing_article:
        generated_title = "{ה}" + generated_title[1:]
    generated_title = generated_title.replace(" - ", "-")
    if not ranked_results:

        if results:
            for result in results:
                result["title"] = [t.joined for t in result["title"]]
            top = results[0]
            title = top["title"][0]
            link = nli_template.format(top["identifier"])
        else:
            title, link = None, None
        out = dict(
            type="unverified",
            record=record,
            converted=generated_title,
            top_query_result={"text": title, "link": link},
            diagnostic_info=format_diagnostic_info(title_reps.field_infos),
            # creator_replists=creator_replists,
        )
        recommendation = get_recommendation(out)
        out["recommendation"] = recommendation

        return out, title_reps.replists
    top = ranked_results[0]
    title = top["title"]
    heb_title = (
        title.replace("<<", "{", 1).replace(">>", "}", 1).strip(" ;.:,")
    )
    out = dict(
        type="verified",
        record=record,
        converted=generated_title,
        # creator_replists=creator_replists,
        matched_title={
            "text": heb_title,
            "link": nli_template.format(top["doc"]["identifier"]),
            "diff": top["diff"],
            # "criteria": top["criteria"],
        },
        diagnostic_info=format_diagnostic_info(title_reps.field_infos),
    )
    recommendation = get_recommendation(out)
    out["recommendation"] = recommendation
    return out, title_reps.replists


async def record_with_results(record, replists_or_error):
    result, _ = await record_with_results_and_replists(
        record, replists_or_error
    )
    return result


def set_json(handler: tornado.web.RequestHandler):
    handler.set_header(name="Content-Type", value="application/json")


def dd_or_empty(input):
    if isinstance(input, dict):
        return libaaron.DotDict(input)
    return input


def good_for_search(subfield_info):
    return (
        subfield_info is not None
        and subfield_info.all_recognized
        and subfield_info.transliteration_tokens
        and not subfield_info.foreign_tokens
        and subfield_info.standard != "unknown"
    )


def can_display(subfield_info):
    return (
        subfield_info is not None
        and subfield_info.all_cached
        and not subfield_info.foreign_tokens
        and subfield_info.standard != "unknown"
    )


def get_recommendation(result):
    if result["type"] == "verified":
        return {"display": ["matched_title"], "search": []}

    di = result["diagnostic_info"]
    main_title, subtitle, responsibility = (
        dd_or_empty(di[x])
        for x in ("main_title", "subtitle", "responsibility")
    )
    for_search = []
    if good_for_search(responsibility):
        for_search.append("responsibility")
    if can_display(main_title):
        if can_display(subtitle):
            return {
                "display": ["main_title", "subtitle"],
                "search": for_search,
            }
        elif subtitle is None:
            return {"display": ["main_title"], "search": for_search}
    if good_for_search(main_title):
        for_search.append("main_title")
        if good_for_search(subtitle):
            for_search.append("subtitle")
    return {"display": [], "search": for_search}


class APIHandler(tornado.web.RequestHandler):
    async def do_task(self, json_records):
        set_json(self)
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

    async def get(self, json_records):
        await self.do_task(json_records)

    async def post(self):
        await self.do_task(self.request.body.decode('utf8'))


class RecordsAndRepsHandler(tornado.web.RequestHandler):
    async def get(self, json_records):
        set_json(self)
        records_n_replists = await delegate(
            json_records2replists, json_records
        )
        sep_sym = "["
        for record, replists_or_error in records_n_replists:
            self.write(sep_sym)
            result, reps = await record_with_results_and_replists(
                record, replists_or_error
            )
            result["replists"] = reps
            self.write(jsonencode(result))
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


def mk_error(exception, input):
    return jsonencode(
        {
            "type": "error",
            "message": repr(exception),
            "input": input,
        }
    )


class TextHandler(tornado.web.RequestHandler):
    async def get(self, text):
        set_json(self)
        try:
            result, input_info, conversion_info = await delegate(
                text_to_replists, text
            )
        except CombinatorialExplosion as e:
            self.write(mk_error(e, text))
            return
        diagnostic_info = _merge_d(
            input_info._asdict(), conversion_info._asdict()
        )
        diagnostic_info["standard"] = diagnostic_info["standard"].value
        self.write(
            jsonencode(
                {
                    "type": "text",
                    "output": result,
                    "diagnostic_info": diagnostic_info,
                }
            )
        )


class TitleHandler(tornado.web.RequestHandler):
    async def get(self, title):
        # incomplete
        set_json(self)
        title_to_replist_subfields(title)


class NLIQueryHandler(tornado.web.RequestHandler):
    async def get(self, data):
        out = await query_nli(jsondecode(data))
        self.write(jsonencode(out))


class TextAndQueryHandler(tornado.web.RequestHandler):
    async def get(self, text):
        text, input_info, conversion_info = await delegate(
            text_to_replists, text
        )
        words = words_of_replists(text)
        results = await query_nli(words)
        self.write(
            jsonencode(
                {
                    "conversion": text,
                    "matches": results,
                    "diagnostic_info": _merge_d(input_info, conversion_info),
                }
            )
        )


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


with open(
        config.project_dir / "arcapi" / "static" / "audit" / "index.html"
) as fh:
    gui = fh.read()


class GUIHandler(tornado.web.RequestHandler):
    async def get(self):
        self.write(gui)


with open(
        config.project_dir / "arcapi" / "static" / "index.html"
) as fh:
    startpage = fh.read()


class StarpageHandler(tornado.web.RequestHandler):
    async def get(self):
        self.write(startpage)
