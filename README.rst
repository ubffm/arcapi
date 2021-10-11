Revrit API Documentation
========================
*Revrit*, the Retroconversion system developed by the Goethe University
Library for the reconstruction of Hebrew script from metadata stored in
transcription, will soon be available for public use over JSON API. At
launch, the API will deal exclusively transliteration in library
records.

.. contents::

This is a simple GET request where the last element in the URL is a JSON
array of records to be converted. e.g. ``https://api.jewishstudies.de/api/YOUR_ARRAY_HERE``
Retroconversion is a time-consuming process, and this
array should not be too long, so as to avoid timeouts. Probably less
than one hundred records per-request would be ideal. The user is
encouraged to send multiple requests concurrently if a large amount of
records needs to be processed. (Of course, if you are using an
asynchronous client, please don’t accidentally DoS us.)

Each client request shall contain an array of records for which the
titles will be converted.

    Note:
      At the moment, there is an SSL issue affecting some clients
      (``curl``, for example) which causes the client not to recognize
      the certificate. We are working to resolve this issue, but for now
      it is recommended to disable SSL validation if this problem affects
      your client, since the API is not intended to transport private data.

API Input
---------

Standard record fields
~~~~~~~~~~~~~~~~~~~~~~

.. code:: json

   {
     "title": ["{ha-} Zemer ha-ʿivri : poʾeṭiḳah, musiḳah, hisṭoriyah, tarbut / ʿorekhet ha-ḳovets Tamar Ṿolf-Monzon"],
     "isPartOf": ["Biḳoret u-parshanut"],
     "creator": ["Ṿolf-Monzon, Tamar"],
     "date": [2012],
     "publisher": ["Universiṭat Bar-Ilan, Ramat-Gan"],
     "identifier": ["728971356"]
   }

This is an example of what a record might look like. The record *must*
have either a ``title`` key or a ``isPartOf`` key. ``isPartOf`` is for
the name of the series. If a no title is given, the series will be
converted instead. In the future, we will also provide conversions for
names of people and publishers.

These are the only required fields. However, it is *recommended* to
include ``creator``, ``date``, and ``publisher`` keys. ``creator`` and
``date`` are used to help verify our converted title with existing
Hebrew metadata. Because the Hebrew transcription systems we support
have some ambiguity (not to mention that transcribed metadata usually
contains a high rate of error), the best way to be sure that the
conversion is correct to match it to existing Hebrew metadata, which we
currently take from our own catalog and the National Library of Israel.

All top-level values may be a scalar value (normally a string, but a
number in the case of ``date``) or an array of scalars.

Title values (i.e. ``title`` and ``isPartOf``) should have the following
format:

   ``{``\ *non-filing*\ ``}`` *main title* ``:`` *subtitle* ``/`` *responsibility statement*

**Non-filing** words or characters should be surrounded by curly braces,
``{}``.

**Main title** comes next. A main title is required.

**Subtitle** optionally comes next, and is preceded by a colon, ``:``.
The colon should have spaces on either side.

**Responsibility statement** optionally comes last, and is preceded by a
slash, ``/``. The slash should have spaces on either side.

A title value may be a single string or an array of titles, but only the
first in the array will be converted. Additional titles may be used for
matching in the future, but they are not currently.

The ``creator`` value contains the names of people involved with the
creation of the work, usually authors or editors. If an array of names
is given, all names will be used for matching. ``creator`` fields will
ideally have the format *last-name, first-name*

``publisher`` values should have the format *name, location*.

``date`` is a number or array of numbers which corresponds to the year
of publication. These numbers will be used for matching.

The ``identifier`` field is not required, but it is highly recommended
so data can be entered back into the catalog. The API itself does
nothing with this field.

Additional input fields
~~~~~~~~~~~~~~~~~~~~~~~

Any other fields can be added to the record and will be ignored by the
API. This may be useful for transfering the output back to the catalog.
Our internal Pica+ mappings generate records with the following format:

.. code:: json

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

We use ``_seriesFields``, ``_creatorFields`` and ``_publisherFields`` to
see exactly which Pica+ field the input data was taken from so it can be
restored to the catalog appropriately.

API output
----------

For the given array of records as input, a corresponding array of
results will be returned as output. All input has a ``type`` key and a
``record`` key. The ``record`` is exactly the record given as input. The
only possible change is that any top-level scalar values will be
converted to arrays. It is recommended to use arrays for everything for
the sake of uniformity.

.. _type:

``type`` may have three different values: verified_, unverified_ or error_.

.. _verified:

Verified results
~~~~~~~~~~~~~~~~

In addition to the ``type`` and ``record`` fields, records of the type
``verified`` and ``unverified`` will contain a ``converted`` field and a
``diagnostic_info`` field. In addition, a ``verified`` record will
contain a ``matched_title`` field.

.. code:: json

   {
     "type": "verified",
     "record": {"title": ["{ha-} Zemer ha-ʿivri : poʾeṭiḳah, musiḳah, hisṭoriyah, tarbut / ʿorekhet ha-ḳovets Tamar Ṿolf-Monzon"],
       "isPartOf": ["Biḳoret u-parshanut"],
       "creator": ["Ṿolf-Monzon, Tamar"],
       "date": [2012],
       "publisher": ["Universiṭat Bar-Ilan, Ramat-Gan"],
       "identifier": ["728971356"]
     },
     "converted": "{ה}זמר העברי : פואטיקה, מוסיקה, היסטוריה, תרבות / עורכת הקובץ תמר וולף-מונזון",
     "matched_title": {
       "text": "{ה}זמר העברי : פואטיקה, מוסיקה, היסטוריה, תרבות / עורכת הקובץ: תמר וולף-מונזון",
       "link": "https://www.nli.org.il/en/books/NNL_ALEPH003454760/NLI",
       "diff": 0.0
     },
     "diagnostic_info": {
       "main_title": {
         "standard": "New DIN 31631",
         "foreign_tokens": false,
         "transliteration_tokens": true,
         "fully_converted": true,
         "all_cached": true,
         "all_recognized": true
       },
       "subtitle": {
         "standard": "New DIN 31631",
         "foreign_tokens": false,
         "transliteration_tokens": true,
         "fully_converted": true,
         "all_cached": true,
         "all_recognized": true
       },
       "responsibility": {
         "standard": "New DIN 31631",
         "foreign_tokens": false,
         "transliteration_tokens": true,
         "fully_converted": true,
         "all_cached": false,
         "all_recognized": false
       }
     }
   }

.. _converted:

``converted`` Is the text produced by retroconversion process. **When
dealing with verified output, the `matched_title` is to be preferred.**

.. _matched_title:

The ``matched_title`` value is an object with ``text``, ``link`` and
``diff`` keys. The ``text`` value is the text of the matched title, the
``link`` is a URL to this resource in an online catalog, and the
``diff`` shows how different the title the conversion algorithm
generated is from the matched title.

They are usually quite similar, but they can be different for a variety
of reason. The most obvious reason for differences is that the
retroconversion process failed to produce the right form. However, it is
also very common for the titles to actually be somewhat different, based
on different cataloging rules or differing interpretations by individual
catalogers of the title page. This is especially the case in very long
titles, were large sections may be replaced with ellipses. In general,
we are quite strict about ensuring the main title is very similar to
what was converted. However, if the main title is almost identical and
other metadata fields are matched, we are more relaxed about the
subtitle and the responsibility statement.

**When a match is found, it is always recommended to use the form of the
title found in the matched data for automated entry into the catalog.**
This title may have more or less information than the title given as
input, but we feel it is more valuable to have the correct spellings of
personal names (a weak point for retroconversion, at present) and words
with non-standard spellings. Generally the Hebrew title will be added
*in addition* to the existing transliterated title, so none of the
original data will be lost.

At Frankfurt, we have found that titles matched in this way are correct
more than 99% of the time. In our formal audit of more than 200 titles,
no mismatches were found. However, a few mismatches have been found
outside of the formal audit. Still, the error rate is so low that we
titles verified in this way back into the catalog without manually
checking them.

The diagnostic_info_ is less important for verified conversions than
for unverified conversions, so it will be covered in the following
section.

.. _unverified:

Unverified results
~~~~~~~~~~~~~~~~~~~

.. code:: json

   {
     "type": "unverified",
     "record": {
       "title": ["Mivḥar. Liriḳa u-reshimot / Ya'akov Shteinberg"],
       "isPartOf": ["Sifriyat Devir le-ʿam"],
       "creator": ["Shṭeinberg, Yaʿaḳov"],
       "publisher": ["Dvir, Tel-Aviv"],
       "_publisherFields": ["033A"],
       "identifier": ["419745025"]
     },
     "converted": "מבחר. ליריקה ורשימות / יעקב שתאינברג",
     "top_query_result": {
       "text": ["מבחר ליריקה ורשימות / יעקב שטיינברג."],
       "link": "https://www.nli.org.il/en/books/NNL_ALEPH001326301/NLI"
     },
     "diagnostic_info": {
       "main_title": {
         "standard": "New DIN 31631",
         "foreign_tokens": false,
         "transliteration_tokens": true,
         "fully_converted": true,
         "all_cached": true,
         "all_recognized": true
       },
       "subtitle": null,
       "responsibility": {
         "standard": "New DIN 31631",
         "foreign_tokens": false,
         "transliteration_tokens": false,
         "fully_converted": true,
         "all_cached": false,
         "all_recognized": false
       }
     }
   }

Many times, a title cannot be reliably verified with existing Hebrew
metadata, either because the data does not exist in our database, or
because of discrepancies in the title and insufficient metadata with
which to verify, as in the above case.

Here, "Ya'akov Shteinberg" is not correct transcription according to any
of the standards we support, and appears to be a more informal type of
Romanization. This is quite common in personal names in metadata.
Because of this, the retroconversion process could not successfully
reconstruct “שטיינברג”. Additionally, this record lacks a ``date``
field, which is one of the fields used to establish matches when there
discrepancies in the title.

``unverified`` results contain a ``top_query_result`` field with
whatever our full-text search of the Hebrew metadata returned. This is
more for Humans trying to see what happened than for any automated use.

When there is no verified match, we may turn to the ``diagnostic_info``
to decide what to do with the converted data.

.. _diagnostic_info:

Diagnostic Info
+++++++++++++++

The ``diagnostic_info`` value contains data about the title fields
given as input, as well as some data about the output, broken down for
each part of the title. In the future, when fields of other types are
converted, they will have their own entries in the
``diagnostic_info``.  The fields currently presented are
``main_title``, ``subtitle`` and ``responsibility``. For each of
these, the value may be an object or ``null``, if the specific title
does not have this field. If it is an object, the object contains the
fields ``standard`` ``foreign_tokens``, ``transliteration_tokens``,
``fully_converted``, ``all_cached``, and ``all_recognized``.

There are five possible values for ``standard``:

1. ``New DIN 31631``. This is the Romanization standard adopted by DIN
   in 2011 (and its updates), which is nearly identical the one used by
   American Library Association and the Library of Congress. Our
   retroconversion works with both.
2. ``Old DIN 31631``. This is conversion system for DIN standards for
   Romanized Hebrew which were in effect from the early eighties until

   2011. 

3. ``PI``. This is the Prussian Instructions standard for Romanization,
   which was in effect for many years in collections around various
   German-speaking countries.
4. ``unknown``. This means the transcription standard could not be
   determined. In such cases, the “Old DIN” conversion system is used as
   a fallback because it is the most robust for dealing with various
   novelties and errors in transcription.
5. ``not_latin``. This indicates that no Latin characters were detected
   in the title, and it is therefore not Romanization.

``foreign_tokens`` may be either ``true`` or ``false``. This means the
input contains tokens (i.e. characters or groups of characters) which
should not occur in Hebrew transcription but are common in other
languages. This is most often because the input is not Hebrew
transcription at all. However, it is not uncommon for titles with
transcription errors to contain some of these foreign tokens. **Such
cases have a higher rate of failure for retroconversion, and are not
recommended for automatic catalog entry unless they have been verified
with existing Hebrew data.** That is to say, you want ``foreign_tokens``
to be ``false``.

``transliteration_tokens`` may be ``true`` or ``false``. This indicates
that the title has non-ASCII charaters which appear in transliteration.
This can be useful as a guide for which titles that contain foreign
tokens may nonetheless be Hebrew transcription. However, it may be true
for languages like French which use the circumflex /^/ over vowels, or
languages which use /š/, such as most Latin-script Slavic languages, as
well as Romanization systems for other languages which contain special
charaters similar to those used for Hebrew. This field is included,
along with ``foreign_tokens`` to narrow down which titles one may want
to look at individually, but should not be taken as reliable indicators
of the input language without human verification.

``fully_converted`` means that all words in this portion of a title
could be converted to Hebrew script. If it is ``false``, it means there
were transcription tokens in some of the words which were not recognized
and retroconversion could not be fully carried out. **No fields which
have not been fully converted should be automatically entered into
catalogs unless they have been verified with existing Hebrew data.**

``all_cached`` means that all conversions for individual words could be
verified as having been correctly identified in the past. Titles for
which this is ``true`` are very likely to be correctly converted and may
be entered into the catalog with the disclaimer that homophones may
cause errors, as well as personal names without a standardized
orthography. If you are not comfortable with this risk, it is at least
recommended to use them for searchable fields which are not displayed to
the end-user. This will improve discoverability. **Our recommendation is
to automatically enter main titles and subtitles for display in the
catalog if this is ``true``, recognizing that there will be occasional
errors, but to use the responsibility statement for search-only
fields.** This is because personal names have more variation in
spelling.

``all_recognized`` means that all conversions for individual words were
recognized as valid Hebrew, either from retroconversion caching, the use
of a large Hebrew word-list or the use of a Hebrew spell checker
(Hspell). Such fields are very likely to be correct, but have a higher
rate of error than fields where all conversions could be verified with
the cache. **Our recommendation is to use conversions for which this is
``true`` as searchable fields. We may recommend them for display in the
future, after a more complete analysis of the rate of error they
contain.**

.. _recommendation:

Recommendation
++++++++++++++

While the ``diagnostic_info`` is useful for more in-depth analysis of
the properties of a title, the API result also has a
``recommendation`` field. This value of this field is an object with a
``display`` property and a ``search`` property. The value of each of
these properties is an array of strings, telling which sections of a
converted title are recommended for display in the catalog interface,
and which parts, while not certain enough for display seem like good
candidates for including in a non-display searchable field.

Here is pseudo-code for the decision tree used to determine whether
various parts of the title are suitable for display or search:

.. code:: python

   if type == verified:
       add matched_title to catalog for display and search

   else if type == unverified:

        can_display(x) =
            x is not null
            and x.all_cached
            and not x.foreign_tokens
            and x.standard is not unknown

       good_for_search(x) =
           x is not null
           and x.all_recognized
           and x.transliteration_tokens
           and not x.foreign_tokens
           and x.standard is not unknown

        # this avoids displaying the main title if the subtitle exists
        # but is not fit for display.
        if can_display(main_title):
            if can_display(subtitle):
                use main_title and subtitle for display
            else if subtitle is null:
                use main_title for display

        if good_for_search(main_title):
            use main_title for search
            if good_for_search(subtitle):
                use subtitle for search

        if good_for_search(responsibility):
            use responsibility statment in searchable data


.. _error: 

Error results
~~~~~~~~~~~~~

An ``error`` type will contain a very short ``message`` describing the
nature of the error:

.. code:: json

   {
     "type": "error",
     "message": "CombinatorialExplosion",
     "record": {
       "title": ["Ṣēdā lā-derek / verf. von Paul laskar u. S. N. Margulies, hrsg. vom ʿCentralbureau für jüd. Auswanderungsangelegenheitenʾ"],
       "creator": ["Laskar, Paul", "Margulies, S. N."],
       "date": [1905],
       "publisher": ["Centralbureau, Berlin"],
       "identifier": ["78824745X"]
     }
   }

In this case, there was combinatorial explosion. The first step of
retroconversion is generating all possible Hebrew forms of a given
input, which is a Cartesian product of all possible conversion forms for
each transcription token. For long words this can become a huge number.
Rather than crash the server, we stop when more than 10,000 forms are
generated for a word. This is almost certainly the case for
*Auswanderungsangelegenheitenʾ* in the above example. In practice we
have never seen this happen with a Hebrew word, only long words from
other languages.

We may note here that the API will attempt to convert anything it
receives as input. There are many works which are cataloged as Hebrew
but may have titles in other languages, or titles in multiple languages,
as the above example. Our system does use heuristics to determine
weather the input appears to be Hebrew transcription, but these
heuristics are not 100% accurate and sometimes a conversion can still be
verified even if our system thought it didn't look like Hebrew
transcription.
