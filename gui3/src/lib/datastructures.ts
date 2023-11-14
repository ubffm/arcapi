/* eslint-disable */
type Field = string[] | undefined

interface APIRecord {
  title: Field;
  isPartOf: Field;
  creator: Field;
  date: number[] | undefined;
  publisher: Field;
  identifier: Field;
}

enum APIOutputT {
  Verified = 'verified',
  Unverified = 'unverified',
  Error = 'error',
}

interface APIOutput {
  type: APIOutputT;
  record: APIRecord;
}

interface APIError extends APIOutput {
  message: string;
}

enum APIStandard {
  NewDIN = 'New DIN 31631',
  OldDIN = 'Old DIN 31631',
  PI = 'PI',
  Unknown = 'unknown',
  NotLatin = 'not_latin',
}

interface DiagnosticAtom {
  standard: APIStandard;
  foreign_tokens: boolean;
  transliteration_tokens: boolean;
  fully_converted: boolean;
  all_cached: boolean;
  all_recognized: boolean;
}

interface DiagnosticInfo {
  main_title: DiagnosticAtom;
  subtitle: DiagnosticAtom | null;
  responsibility: DiagnosticAtom | null;
}

interface Recommendation {
  display: string[];
  search: string[];
}

interface APIConverted extends APIOutput {
  converted: string;
  diagnostic_info: DiagnosticInfo;
  recommendation: Recommendation
}

interface QueryResult {
  text: string | string[];
  link: string;
}

interface APIVerified extends APIConverted {
  matched_title: QueryResult;
}

interface APIUnverified extends APIConverted {
  top_query_result: QueryResult;
}

enum AuditT {
  MatchedTitle = "matched_title",
  Converted = "converted",
  TopQuery = "top_query_result",
  Edited = "edited",
  Rejected = "rejected",
}

interface AuditOutput {
  type: AuditT;
  title: string;
}

interface APIAudited extends APIConverted {
  audit_result: AuditOutput;
}

interface RepList {
  key: string;
  reps: string[];
}


interface APIText {
  type: string;
  output: RepList[];
  diagnostic_info: DiagnosticAtom;
}

const getTitle = (apiOutput: APIOutput) => {
  if (apiOutput.record.title) {
    return apiOutput.record.title[0];
  }
  if (apiOutput.record.isPartOf) {
    return apiOutput.record.isPartOf[0];
  }
  return '[record has no title]';
};

const getDate = (apiOutput: APIOutput) => {
  if (apiOutput.record.date) {
    return apiOutput.record.date[0];
  }
  return '';
};

const getCreator = (apiOutput: APIOutput) => {
  if (apiOutput.record.creator) {
    return apiOutput.record.creator[0];
  }
  return '';
};

const getPublisher = (apiOutput: APIOutput) => {
  if (apiOutput.record.publisher) {
    return apiOutput.record.publisher[0];
  }
  return '';
};

const getHebrewTitle = (apiOutput: APIOutput) => {
  if (apiOutput.type === APIOutputT.Unverified) {
    return (apiOutput as APIUnverified).converted;
  }
  if (apiOutput.type === APIOutputT.Verified) {
    return delist((apiOutput as APIVerified).matched_title.text);
  }
  return 'title not converted due to error';
};

const delist = <T>(input: T | T[]): T => {
  if (Array.isArray(input)) {
    return input[0];
  }
  return input;
}

const getQueryResult = (apiOutput: APIVerified | APIUnverified) : QueryResult => {
  if (apiOutput.type === APIOutputT.Unverified) {
    return (apiOutput as APIUnverified).top_query_result;
  } else {
    return (apiOutput as APIVerified).matched_title;
  }
}

const resultFilterer = (
  output: APIOutput,
  verified: boolean,
  unverified: boolean,
  error: boolean,
  display: boolean,
  search: boolean,
  noRecommendation: boolean,
  likelyTranscription: boolean,
) => {
  const t = output.type
  if (!(
    (t === APIOutputT.Verified && verified)
    || (t === APIOutputT.Unverified && unverified)
    || (t === APIOutputT.Error && error)
  )) {
    return false
  }
  if (t === APIOutputT.Error) {
    if (noRecommendation) {
      return true
    }
    return false
  } 
  const converted = output as APIConverted;
  const rec = converted.recommendation;
  if (!(
    (rec.display.length && display)
    || (rec.search.length && search)
    || (!rec.display.length && !rec.search.length && noRecommendation)
  )) {
    return false
  }
  const di = converted.diagnostic_info.main_title;
  if (likelyTranscription &&
     !(!di.foreign_tokens || di.transliteration_tokens || di.all_recognized)
  ) {
    return false;
  }
  return true;
}

enum Tab {
  Input = 'input',
  Audit = 'audit',
  Filter = 'filter',
  Export = 'export',
}

export {
  APIRecord,
  APIOutput,
  APIOutputT,
  APIConverted,
  APIVerified,
  APIUnverified,
  AuditT,
  APIAudited,
  APIError,
  APIText,
  APIStandard,
  RepList,
  Tab,
  resultFilterer,
  getQueryResult,
  delist,
  getTitle,
  getCreator,
  getDate,
  getPublisher,
  getHebrewTitle,
}
