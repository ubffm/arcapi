_reVrit_, the Retroconversion system developed by the Goethe
University Library for the reconstruction of Hebrew script from
metadata stored in transcription, will soon be available for public
use over JSON API. At launch, the API will deal exclusively
transliteration in library records.

This is a simple GET request where the last element in the URL is a
JSON array of records to be converted. Retroconversion is a
time-consuming process, and this array should not be too long, so as
to avoid timeouts. Probably less than one hundred would be ideal. The
user is encouraged to multiple requests concurrently if a large amount
of records needs to be processed.

Each client request shall contain an array of records for which the
titles will be converted.

## Standard record fields

```json
{
  "title": ["{ha-} Zemer ha-ʿivri : poʾeṭiḳah, musiḳah, hisṭoriyah, tarbut / ʿorekhet ha-ḳovets Tamar Ṿolf-Monzon"],
  "isPartOf": ["Biḳoret u-parshanut"],
  "creator": ["Ṿolf-Monzon, Tamar"],
  "date": [2012],
  "publisher": ["Universiṭat Bar-Ilan, Ramat-Gan"],
  "identifier": ["728971356"]
}
```

This is an example of what a record might look like. The record _must_
have either a `title` key or a `isPartOf` key. `isPartOf` is for the
name of the series. If a no title is given, the series will be
converted instead. In the future, we will also provide conversions for
names of people and publishers.

These are the only required fields. However, it is _recommended_ to
include `creator`, `date`, and `publisher` keys. `creator` and `date`
are used to help verify our converted title with existing Hebrew
metadata. Because the Hebrew transcription systems we support have
some ambiguity (not to mention that transcribed metadata usually
contains a high rate of error), the best way to be sure that the
conversion is correct to match it to existing Hebrew metadata, which
we currently take from our own catalog and the National Library of
Israel.

All top-level values may be a scalar value (normally a string, but a
number in the case of `date`) or an array of scalars.

Title values (i.e. `title` and `isPartOf`) should have the following
format:

> {_non-filing_} _main title_ *:* _subtitle_ */* responsibility statement

*Non-filing* words or characters should be surrounded by curly braces,
`{}`.

*Main title* comes next. A main title is required.

*Subtitle* optionally comes next, and is preceded by a colon, `:`. The
colon should have spaces on either side.

*Responsibility statement* optionally comes last, and is preceded by a
slash, `/`. The slash should have spaces on either side.

A title value may be a single string or an array of titles, but only
the first in the array will be converted. Additional titles may be
used for matching in the future, but they are not currently.

The `creator` value contains the names of people involved with the
creation of the work, usually authors or editors. If an array of names
is given, all names will be used for matching. `creator` fields will
ideally have the format _last-name, first-name_

`publisher` values should have the format _name, location_.

`date` is a number or array of numbers which corresponds to the year
of publication. These numbers will be used for matching.

The `identifier` field is not required, but it is highly recommended
so data can be entered back into the catalog. The API itself does
nothing with this field.

## Additional input fields

Any other fields can be added to the record and will be ignored by the
API. This may be useful for the output back to the catalog. Our
internal Pica+ mappings generate records with the following format:

```json
{
  "title": ["{ha-} Zemer ha-ʿivri : poʾeṭiḳah, musiḳah, hisṭoriyah, tarbut / ʿorekhet ha-ḳovets Tamar Ṿolf-Monzon"],
  "isPartOf": ["Biḳoret u-parshanut"],
  "_seriesFields": ["036E/00"],
  "creator": ["Ṿolf-Monzon, Tamar"],
  "_creatorFields": ["028C"],
  "date": [2012],
  "publisher": ["Universiṭat Bar-Ilan, Ramat-Gan"],
  "_publisherFields": ["033A"],
  "identifier": ["728971356"]
}
```

We use `_seriesFields`, `_creatorFields` and `_publisherFields` to see
exactly which Pica+ field the input data was taken from so it can be
restored to the catalog appropriately.

# API output

For the given array of records as input, a corresponding array of
results will be returned as output. All input has a `type` key and a
`record` key. The `record` is exactly the record given as input. The
only possible change is that any top-level scalar values will be
converted to arrays. It is recommended to use arrays for everything
for the sake of uniformity.

`type` may have three different values: `verified`, `unverified` or
`error`.

## Error results
An `error` type will contain a very short `message` describing the
nature of the error:

```json
{
  "type": "error",
  "message": "CombinatorialExplosion",
  "record": {
    "title": ["Ṣēdā lā-derek / verf. von Paul laskar u. S. N. Margulies, hrsg. vom ʿCentralbureau für jüd. Auswanderungsangelegenheitenʾ"],
    "creator": ["Laskar, Paul", "Margulies, S. N."],
    "_creatorFields": ["028A", "028C"],
    "date": [1905],
    "publisher": ["Centralbureau, Berlin"],
    "_publisherFields": ["033A"],
    "identifier": ["78824745X"]
  }
}
```

In this case, there was combinatorial explosion. The first step of
retroconversion is generating all possible Hebrew forms of a given
input, which is a Cartesian product of all possible conversion forms
for each transcription token. For long words this can become a huge
number. Rather than crash the server, we stop when more than 10,000
forms are generated for a word. This is almost certainly the case for
_Auswanderungsangelegenheitenʾ_ in the above example. In practice we
have never seen this happen with a Hebrew word, only long words
from other languages.

We may note here that the API will attempt to convert anything it
receives as input. There are many works which are cataloged as Hebrew
but may have titles in other languages, or titles in multiple
languages, as the above example. Our system does use heuristics to
determine weather the input appears to be Hebrew transcription, but
these heuristics are not 100% accurate and sometimes a conversion can
still be verified even if our system thought it didn't look like
Hebrew transcription.

## Verified results

In addition to the `type` and `record` fields, records of the type
`verified` and `unverified` will contain a `converted` field and a
`diagnostic_info` field. In addition, a `verified` record will contain
a `matched_title` field.


```json
{
  "type": "verified",
  "record": {
    "title": ["{ha-} Zemer ha-ʿivri : poʾeṭiḳah, musiḳah, hisṭoriyah, tarbut / ʿorekhet ha-ḳovets Tamar Ṿolf-Monzon"],
    "isPartOf": ["Biḳoret u-parshanut"],
    "_seriesFields": ["036E/00"],
    "creator": ["Ṿolf-Monzon, Tamar"],
    "_creatorFields": ["028C"],
    "date": [2012],
    "publisher": ["Universiṭat Bar-Ilan, Ramat-Gan"],
    "_publisherFields": ["033A"],
    "identifier": ["728971356"]
  },
  "converted": "{ה}זמר העברי : פואטיקה, מוסיקה, היסטוריה, תרבות / עורכת הקובץ תמר וולף - מונזון",
  "matched_title": {
    "text": "{ה}זמר העברי : פואטיקה, מוסיקה, היסטוריה, תרבות / עורכת הקובץ: תמר וולף-מונזון",
    "link": "https://www.nli.org.il/en/books/NNL_ALEPH003454760/NLI",
    "diff": 0.0
  },
  "diagnostic_info": {
    "input_info": {
      "main_title": {"standard": "ALA/LOC", "foreign_tokens": false},
      "subtitle": {"standard": "ALA/LOC", "foreign_tokens": false},
      "responsibility": {"standard": "ALA/LOC", "foreign_tokens": false}
    },
    "conversion_info": {
      "main_title": {"fully_converted": true, "all_cached": true, "all_recognized": true},
      "subtitle": {"fully_converted": true, "all_cached": true, "all_recognized": true},
      "responsibility": {"fully_converted": true, "all_cached": false, "all_recognized": false}
    }
  }
}
```

The `matched_title` value is an object with `text`, `link` and `diff`
keys. The `text` value is the text of the matched title, the `link` is
a URL to this resource in an online catalog, and the `diff` shows how
different the title the conversion algorithm generated is from the
matched title.

They are usually quite similar, but they can be different for a
variety of reason. The most obvious reason for differences is that the
retroconversion process failed to produce the right form. However, it
is also very common for the titles to actually be somewhat different,
based on different cataloging rules or differing interpretations by
individual catalogers of the title page. This is especially the case
in very long titles, were large sections may be replaced with
ellipses. In general, we are quite strict about ensuring the main
title is very similar to what was converted. However, if the main
title is almost identical and other metadata fields are matched, we
are more relaxed about the subtitle and the responsibility statement.

*When a match is found, it is always recommended to use the form of
the title found in the matched data for automated entry into the
catalog.* This title may have more or less information than the title
given as input, but we feel it is more valuable to have the correct
spellings of personal names (a weak point for retroconversion, at
present) and words with non-standard spellings. Generally the Hebrew
title will be added _in addition_ to the existing transliterated
title, so none of the original data will be lost, so none of the
original data will be lost.

At Frankfurt, we have found that titles matched in this way are
correct more than 99% of the time. In our formal audit of more than
200 titles, no mismatches were found. However, a few mismatches have
been found outside of the formal audit. Still, the error rate is so
low that we titles verified in this way back into the catalog without
manually checking them.

The `diagnostic_info` is less important for verified conversions than
for unverified conversions, so it will be covered in the following
section.

## Unverified results

```json
{
  "type": "unverified",
  "record": {
    "title": ["Mivḥar. Liriḳa u-reshimot / Ya'akov Shteinberg"],
    "isPartOf": ["Sifriyat Devir le-ʿam"],
    "_seriesFields": ["036E/00"],
    "creator": ["Shṭeinberg, Yaʿaḳov"],
    "_creatorFields": ["028A"],
    "publisher": ["Dvir, Tel-Aviv"],
    "_publisherFields": ["033A"],
    "identifier": ["419745025"]
  },
  "converted": "מבחר. ליריקה ורשימות / יעקב שתאינברג",
  "top_query_result": ["מבחר ליריקה ורשימות / יעקב שטיינברג."],
  "diagnostic_info": {
    "input_info": {
      "main_title": {"standard": "ALA/LOC", "foreign_tokens": false},
      "subtitle": null,
      "responsibility": {"standard": "ALA/LOC", "foreign_tokens": false}
    },
    "conversion_info": {
      "main_title": {"fully_converted": true, "all_cached": true, "all_recognized": true},
      "subtitle": null,
      "responsibility": {"fully_converted": true, "all_cached": false, "all_recognized": false}
    }
  }
}
```

Many times, a title
