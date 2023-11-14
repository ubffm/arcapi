interface Dictionary<T> {[key: string]: T; }
const queryURLs: Dictionary<string> = {
  morfix: 'http://www.morfix.co.il/QUERY_HERE',
  googleTranslate: 'https://translate.google.com/#iw/en/QUERY_HERE',
  nli: 'http://merhav.nli.org.il/primo_library/libweb/action/search.do;jsessionid=DD40D325955438DF28DC1C47A7B81B2C?fn=search&ct=search&initialSearch=true&mode=Basic&tab=default_tab&indx=1&dum=true&srt=rank&vid=NLI&frbg=&vl%28freeText0%29=QUERY_HERE&scp.scps=scope%3A%28NNL%29',
  kvk: 'http://kvk.bibliothek.kit.edu/hylib-bin/kvk/nph-kvk2.cgi?maske=kvk-redesign&lang=de&title=KIT-Bibliothek%3A+Karlsruher+Virtueller+Katalog+KVK+%3A+Ergebnisanzeige&head=%2F%2Fkvk.bibliothek.kit.edu%2Fasset%2Fhtml%2Fhead.html&header=%2F%2Fkvk.bibliothek.kit.edu%2Fasset%2Fhtml%2Fheader.html&spacer=%2F%2Fkvk.bibliothek.kit.edu%2Fasset%2Fhtml%2Fspacer.html&footer=%2F%2Fkvk.bibliothek.kit.edu%2Fasset%2Fhtml%2Ffooter.html&css=none&input-charset=utf-8&ALL=&TI=QUERY_HERE&AU=&CI=&ST=&PY=&SB=&SS=&PU=&kataloge=COPAC&kataloge=VERBUND_ISRAEL&kataloge=WORLDCAT&ref=direct&client-js=yes',
  google: 'https://google.com/search?q=QUERY_HERE',
  marc21: 'https://www.loc.gov/marc/bibliographic/concise/bdQUERY_HERE.html',
  hebis: 'http://cbsopac.rz.uni-frankfurt.de/DB=2.1/PPNSET?PPN=QUERY_HERE',
};

const applyQuery = (template: string, query: string): string => {
  const encoded = encodeURIComponent(query);
  return queryURLs[template].replace('QUERY_HERE', encoded);
};

export {
  Dictionary,
  applyQuery,
};
