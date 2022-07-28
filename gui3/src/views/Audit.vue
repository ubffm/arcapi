<template>
  <div style="text-align: left">
    <span v-if="(typeof recordsObject !== 'string' || audited.length !== 0)">
      <button @click="currTab = Tab.Input" :class="isActive(Tab.Input)">
        input records ({{ (typeof recordsObject) !== 'string' ? recordsObject.length : 0 }})
      </button>
    </span>
    <span v-if="(typeof recordsObject !== 'string')">
      <button @click="currTab = Tab.Filter" :class="isActive(Tab.Filter)"> filter input </button>
      <button @click="currTab = Tab.Audit" :class="isActive(Tab.Audit)">
        audit individual records
      </button>
    </span>
    <span v-if="(typeof recordsObject !== 'string' || audited.length !== 0)">
      <button @click="currTab = Tab.Export" :class="isActive(Tab.Export)">
        export audited ({{ audited.length }})
      </button>
    </span>
    <br />
    <br />
    <div v-if="typeof currentRecord === 'string'">
      {{ currentRecord }}
      <br />
      <br />
    </div>
    <!-- input tab -->
    <div v-if="currTab === 'input'">
      Load a JSON file of API output here: <br />
      <input type="file" id="recordInput" @change="loadFile($event)">
      <br />
      <p>or copy records in as text in the box below.</p>
      <textarea v-model="textRecords"></textarea> <br />
      <div v-if="typeof currentRecord === 'string'">
        Once records are loaded tabs will appear above to provide further functionality.
      </div>
      <div v-else>
        <button @click="clearInput">clear input (cannot be undone)</button> <br /> <br />
        Use the tab buttons at the top of the page to
        interact with your data in different ways.
        <br /> <br />
        current number of input records: {{ recordsObject.length }}
      </div>
    </div>
    <!-- filter tab -->
    <div v-if="currTab === 'filter'">
      <p>
        This page allows you to filter different kinds of records out
        of the data set which may be irrelevant to your audit
      </p>
      Show these types:<br />
      <input type="checkbox" name="verified" v-model="filVerified"> verified
      <input type="checkbox" name="unverified" v-model="filUnverified"> unverified
      <input type="checkbox" name="error" v-model="filError"> error
      <br /><br />
      Show records with the following recommendations:<br />
      <input type="checkbox" name="display" v-model="filDisplay"> display
      <input type="checkbox" name="search" v-model="filSearch"> search
      <input type="checkbox" name="none" v-model="filNoRecommendation"> none
      <br /><br />
      Keep only records likely to have transliterated titles?<br />
      <input type="checkbox" name="likelyTranscription" v-model="filLikelyTranscription"> yes
      <br /><br />
      <!-- <button @click="toggleAdvancedFilters">show advanced filters</button>
    <div v-if="showAdvancedFilters">
      Title subfields to include in filtration:<br />
      main title - subtitle - responsibility statement
      <br /><br />
      Fields MUST have the following:<br />
      transliteration standard - foreign tokens - transliteration tokens
      - fully converted - all cached - all recognized
      <br /><br />
      Fields must NOT have the following:<br />
      transliteration standard - foreign tokens - transliteration tokens
      - fully converted - all cached - all recognized
    </div>
    <br v-else /><br /> -->
      <div v-if="filterResults !== null">
        <div class="flexcontainer">
          <div class="scrollbox">
            remaining records: {{ filterResults[0].length }}
            <br />
            <div v-for="(el, i) in filterResults[0]" :key="i">
              {{ getTitle(el) }}<br />
              <span dir="rtl">{{ getHebrewTitle(el) }}</span> <br /> <br />
            </div>
          </div>
          <div class="scrollbox">
            removed records: {{ filterResults[1].length }} <br />
            <div v-for="(el, i) in filterResults[1]" :key="i">
              {{ getTitle(el) }}<br />
              <span dir="rtl">{{ getHebrewTitle(el) }}</span> <br /> <br />
            </div>
          </div>
        </div>
        <button @click="applyFilters">apply filters</button>
        <a :href="exportRemaining()" download="remaining.json"><button>export remaining</button></a>
        <a :href="exportRemoved()" download="removed.json"><button>export removed</button></a>
      </div>
    </div>
    <!-- audit tab -->
    <div v-if="currTab === 'audit'">
      <div v-if="(typeof currentRecord!== 'string')">
        <em>{{ currentRecord.type }}</em> <br />
        <div class="worktitle" style="display: inline-block">
          {{ getTitle(currentRecord) }} <br /><br />
          <div class="hebrew" dir="rtl" style="text-align-last:right;">
            {{ currentHebrewTitle }}
          </div>
        </div> <br />
        {{ getDate(currentRecord) }} <br />
        {{ getPublisher(currentRecord) }} <br />
        {{ getCreator(currentRecord) }}
        <!-- utility buttons -->
        <div v-if="currentRecord.type !== 'error'">
          <!-- <input id="converted-words" style="display:none"> -->
          <!-- <p><button@click="copyText(converted)">copy Hebrew text</button></p> -->
          <a :href="applyQuery('nli', currentConverted.converted)" target="_blank">search NLI</a> |
          <a :href="applyQuery('kvk', currentConverted.converted)" target="_blank">search KVK</a> |
          <a :href="applyQuery('google', currentConverted.converted)" target="_blank">
            search Google
          </a> |
          <a :href="applyQuery('googleTranslate', currentConverted.converted)" target="_blank">
            Google Translate
          </a>
        </div>
        <br />
        <div v-if="currentRecord.type === 'verified'">matched title:</div>
        <div v-if="currentRecord.type === 'unverified'">top query result: </div>
        <div style="display:inline-block;margin-left:1em;font-size:0.9em;">
          <a :href="topQuery.link" target="_blank">
            <div class="hebrew" dir="rtl" style="text-align-last:right;margin-left:1em">
              {{ delist(topQuery.text) }}
            </div>
          </a>
          <button
            v-if="currentRecord.type === 'unverified'"
            @click="acceptTopQuery" style="font-size:0.8em"
          >
            accept top query result
          </button>
        </div><br /><br />
        <button v-if="currentRecord.type !== 'error'" @click="accept">
          accept displayed title
        </button>
        <button @click="reject">reject</button>
        <button @click="showCorrectionInterface = !(showCorrectionInterface)"
          :class="showCorrectionInterface ? 'active' : ''">
          edit title
        </button>
        <button
          @click="showFullRecord = !(showFullRecord)"
          :class="(showFullRecord ? 'active': '')"
        >
          show full record
        </button>
        <button @click="undo">
          undo last
        </button>
        <br />
        <div v-if="showCorrectionInterface" dir="rtl">
          <textarea v-if="showSimpleEditor" v-model="simpleEditorText"
            style="font-size:1.3em;font-family:'Times New Roman', Times, serif"
            rows="3"
          ></textarea>
          <div v-else-if="repContainers === null">loading editor...</div>
          <div v-else>
            <div class="word-box hover-me" v-for="(word, index) in repContainers" :key="index">
              <div v-if="!word.hot">
                <div @click="activateEditor(word)">
                  <div dir="ltr">&nbsp;{{ word.currKey }}</div>
                  <div class="hebrew" style="font-size:1.6em">{{ word.currRep }}&nbsp;</div>
                </div>
                <!-- dropdown replacement list -->
                <div class="dropdown-content">
                  <div
                    class="hebrew"
                    v-for="rep in word.reps"
                    @click="word.currRep = rep"
                    style="font-size:1.6em"
                    :key="rep"
                  >
                    {{ rep }}
                  </div>
                </div>
              </div>
              <div v-else>
                <div dir="ltr" @click="word.hot = false">&nbsp;{{ word.currKey }}</div>
                <input :id="'input' + word.idx" class="hebrew" v-model="word.currRep"
                  :style='boxSize(word, 1) + "; font-size:1.6em"' @keyUp.enter="word.hot = false">
                <div>
                  <a :href="applyQuery('morfix', word.currRep)" target="_blank">morfix</a><br />
                  <button @click="deleteWord(word)">delete word</button> <br />
                  <button @click="addWord(word)">add word</button> <br />
                  <button @click="moveWord(word, -1)">&lt;-</button>
                  move
                  <button @click="moveWord(word, 1)">-&gt;</button>
                </div>
              </div>
            </div>
          </div>
          <br />
          <button @click="acceptEdited">accept edited Hebrew</button>
          <button
            @click="toggleSimpleEditor()"
            :class="showSimpleEditor? 'active' : ''"
          >use simple editor</button>
        </div>
        <table v-if="showFullRecord && (typeof currentRecord !== 'string')">
          <tr v-for="(value, name, index) in currentRecord.record" :key="index">
            <td>{{ name }}:</td>
            <td v-if="Array.isArray(value) && value.length === 1">{{ value[0] }}</td>
            <td v-else>{{ value }}</td>
          </tr>
          <tr>
            <td> <br /></td>
          </tr>
          <tr>full API output:<td> </td>
          </tr>
          <tr v-for="(value, name, index) in currentRecord" :key="index">
            <td><code>{{ name }}:</code></td>
            <td><code>{{ value }}</code></td>
          </tr>
        </table>
        <br />
      </div>
    </div>
    <!-- export tab -->
    <div v-if="currTab === 'export'">
        <div class="scrollbox">
          <br />
          <br />
          <div v-for="(el, i) in audited" :key="i">
            {{ getTitle(el) }}<br />
            <span v-if="el.audit_result.title" dir="rtl">
              {{ el.audit_result.title }} <br />
            </span>
            <em>{{ el.audit_result.type }}</em><br /> <br />
          </div>
        </div>
      <a :href="exportAudited()" download="audited.json"><button>export audited</button></a>
      <button @click="clearAudited">clear audited (cannot be undone)</button>
    </div>
  </div>
</template>

<script lang="ts">
import {
  defineComponent, ref, Ref, computed, watch,
} from 'vue';
import {
  APIOutput,
  APIConverted,
  APIVerified,
  APIUnverified,
  APIAudited,
  AuditT,
  Tab,
  resultFilterer,
  getQueryResult,
  APIOutputT,
  APIText,
  delist,
  getTitle,
  getCreator,
  getDate,
  getPublisher,
  getHebrewTitle,
} from '../lib/datastructures';
import { applyQuery } from '../lib/nli_helpers';

interface RepContainer {
  currKey: string;
  currRep: string;
  reps: string[];
  hot: boolean;
  idx: number;
}

export default defineComponent({
  name: 'Audit',
  setup() {
    const textRecords = ref('');
    const recordsObject: Ref<APIOutput[] | string> = ref('Enter records to begin!');

    watch(textRecords,
      (newValue) => {
        let text = newValue.trim();
        if (text === '' || text === '[]') {
          recordsObject.value = 'Enter some records to begin!';
          window.localStorage.setItem('textRecords', text);
          return;
        }
        let start = text[0];
        if (start === '[' || start === ',') {
          start = '[';
        } else {
          start = `[${start}`;
        }
        let end = text.slice(-1);
        if (end === ']' || end === ',') {
          end = ']';
        } else {
          end = `${end}]`;
        }
        text = `${start}${text.slice(1, -1)}${end}`;
        window.localStorage.setItem('textRecords', text);
        try {
          recordsObject.value = JSON.parse(text);
        } catch (e) {
          recordsObject.value = 'Record input was invalid JSON';
        }
      });
    const currTab = ref(Tab.Input);

    const makeRepContainers = (replists: APIText): RepContainer[] => replists.output.map(
      (replist, i) => ({
        currKey: replist.key,
        currRep: replist.reps[0],
        reps: replist.reps.slice(0, 10),
        hot: false,
        idx: i,
      }),
    );

    const toggleRef = (someRef: Ref<boolean>) => {
      /* eslint-disable no-param-reassign */
      someRef.value = !(someRef.value);
    };

    const showSimpleEditor = ref(true);
    const toggleSimpleEditor = () => toggleRef(showSimpleEditor);
    const simpleEditorText = ref('');

    const audited: Ref<APIAudited[]> = ref([]);
    const saveAudited = () => window.localStorage
      .setItem('audited', JSON.stringify(audited.value));

    const pushAudited = (value: APIAudited) => {
      const out = audited.value.push(value);
      saveAudited();
      return out;
    };

    const popAudited = () => {
      const out = audited.value.pop();
      saveAudited();
      return out;
    };

    const repContainers: Ref<RepContainer[] | null> = ref(null);
    const currentRecord: Ref<string | APIOutput> = ref('');
    watch(recordsObject, (records) => {
      repContainers.value = null;
      showSimpleEditor.value = true;

      if (typeof records === 'string') {
        currentRecord.value = records;
        return;
      }
      if (recordsObject.value.length === 0) {
        currTab.value = audited.value.length !== 0 ? Tab.Audit : Tab.Input;

        currentRecord.value = 'No more records. Please enter some.';
        return;
      }
      const req = new XMLHttpRequest();
      req.onload = () => {
        let replists;
        try {
          replists = JSON.parse(req.responseText) as APIText;
        } catch (e) {
          console.log("didn't get valid JSON from the server");
          return;
        }
        repContainers.value = makeRepContainers(replists);
        showSimpleEditor.value = false;
      };
      req.open('GET', `/text/${encodeURI(getTitle(records[0]))}`);
      req.send();

      simpleEditorText.value = getHebrewTitle(records[0]);
      [currentRecord.value] = records;
    });
    const currentConverted = currentRecord as Ref<APIConverted>;

    const clearInput = () => {
      textRecords.value = '';
    };

    const currentHebrewTitle = computed(() => {
      if (typeof currentRecord.value === 'string') { return ''; }
      return getHebrewTitle(currentRecord.value);
    });

    // eslint-disable-next-line
    // const replists: Ref<APIText> = ref({"type": "text", "output": [{"key": "ʿosḳim", "reps": ["עוסקים", "עוסקם", "עסקים", "עסקם", "עוסקאם", "עאסקים", "עאסקם", "עסקאם", "עאסקאם"]}, {"key": "u-fidyon", "reps": ["ופדיון", "ופדין", "ופידיין", "ופידין", "ופדייאן", "ופדיאן", "ופידייאן", "ופידיאן", "ופדייון", "ופידייון", "ופידיון", "ופדיין"]}, {"key": "be-ʿanfe", "reps": ["בענפי", "בענפא", "בענפה", "בעאנפי", "בעאנפא", "בעאנפה"]}, {"key": "ha-mesheḳ", "reps": ["המשק", "המשיק", "המישק", "המישיק", "המשאק", "המאשק", "המישאק", "המאשיק", "המאשאק"]}, {"key": "ʿal", "reps": ["על", "אל", "עאל"]}, {"key": "pe", "reps": ["פה", "פי", "פא"]}, {"key": "mas", "reps": ["מס", "מאס"]}, {"key": "ʿerekh", "reps": ["ערך", "עריך", "עירך", "עיריך", "עראך", "עארך", "עיראך", "עאריך", "עאראך"]}, {"key": "musaf", "reps": ["מוסף", "מסף", "מסאף", "מוסאף"]}], "diagnostic_info": {"standard": APIStandard.NewDIN, "foreign_tokens": false, "transliteration_tokens": true, "fully_converted": true, "all_cached": false, "all_recognized": true}})
    // eslint-disable-next-line
    // const replists = {"type": "text", "output": [{"key": "sefirot", "reps": ["ספירות", "ספרות", "סיפירות", "סיפרות", "ספירת", "ספרת", "סיפירת", "סיפרת", "ספיראת", "ספארות", "סאפירות", "ספראת", "סיפיראת", "סיפארות", "סאפרות", "סיפראת", "ספארת", "סאפירת", "סיפארת", "סאפרת"]}, {"key": "tenuʿah", "reps": ["תנועה", "תנעה", "תאנועה", "תינעה", "טנועה", "טינועה", "תאנעה", "טנעה", "טאנועה", "טינעה", "טאנעה", "תינועה"]}, {"key": "ba-derakhim", "reps": ["בדרכים", "בדרכם", "בדירכים", "בדירכם", "בדרכאם", "בדראכים", "בדארכים", "בדראכם", "בדירכאם", "בדיראכים", "בדארכם", "בדיראכם", "בדראכאם", "בדארכאם", "בדאראכים", "בדיראכאם", "בדאראכם", "בדאראכאם"]}, {"key": "lo", "reps": ["לא", "לו", "לוא"]}, {"key": "-", "reps": ["-"]}, {"key": "ʿironiyot", "reps": ["עירוניות", "ערונייות", "ערוניות", "עירוניית", "עירנייות", "עירונית", "עירניות", "ערוניית", "ערנייות", "ערונית", "ערניות", "עירניית", "עירנית", "ערניית", "ערנית", "עירונייאת", "עיראנייות", "עארונייות", "עירוניאת", "עיראניות"]}], "diagnostic_info": {"standard": "New DIN 31631", "foreign_tokens": false, "transliteration_tokens": true, "fully_converted": true, "all_cached": false, "all_recognized": true}};
    let currentlyHot = 0;
    const activateEditor = (word: RepContainer) => {
      if (repContainers.value === null) { return; }
      repContainers.value[currentlyHot].hot = false;
      // eslint-disable-next-line
      word.hot = true;
      currentlyHot = word.idx;
    };
      /* eslint-disable no-param-reassign */
    const updateIdxs = (rcs: RepContainer[]) => rcs.forEach((word, i) => { word.idx = i; });
    const deleteWord = (word: RepContainer) => {
      if (repContainers.value === null) { return; }
      repContainers.value = repContainers.value.filter((_, i) => i !== word.idx);
      currentlyHot = 0;
      updateIdxs(repContainers.value);
    };
    const addWord = (word: RepContainer) => {
      if (repContainers.value === null) { return; }
      word.hot = false;
      repContainers.value.splice(word.idx + 1, 0, {
        currKey: '(added word)',
        currRep: '',
        reps: [''],
        hot: true,
        idx: 0,
      });
      updateIdxs(repContainers.value);
    };
    const moveWord = (word: RepContainer, inc: number) => {
      if (repContainers.value === null) { return; }
      const newPosition = word.idx + inc;
      if (newPosition >= repContainers.value.length || newPosition < 0) { return; }
      const other = repContainers.value[newPosition];
      repContainers.value[word.idx] = other;
      repContainers.value[newPosition] = word;
      updateIdxs(repContainers.value);
    };
    const isActive = (tab: Tab) => (currTab.value === tab ? 'active' : '');
    const boxSize = (word: RepContainer, ratio: number): string => (
      `max-width: ${Math.max(word.currRep.length, 2) * ratio}rem`
    );

    const topQuery = computed(() => {
      const current = currentRecord.value;
      if (typeof current === 'string' || current.type === 'error') {
        return { text: '', link: '' };
      }
      return getQueryResult(current as (APIVerified | APIUnverified));
    });
    const corrected = ref('');
    watch(currentRecord, (newValue) => {
      if (typeof newValue !== 'string' && newValue.type !== 'error') {
        corrected.value = (newValue as APIConverted).converted;
      }
    });

    const loadFile = (event: Event | null) => {
      if (event === null) { return; }
      const { files } = event.target as HTMLInputElement;
      if (files === null || files === undefined) { return; }
      files[0].text().then((text) => { textRecords.value = text; }, null);
    };

    const showFullRecord = ref(false);
    const toggleFullRecord = () => toggleRef(showFullRecord);
    const showCorrectionInterface = ref(false);
    const toggleCorrectionInterface = () => toggleRef(showCorrectionInterface);
    const showAdvancedFilters = ref(false);
    const toggleAdvancedFilters = () => toggleRef(showAdvancedFilters);

    const filVerified = ref(false);
    const filUnverified = ref(true);
    const filError = ref(false);
    const filDisplay = ref(true);
    const filSearch = ref(true);
    const filNoRecommendation = ref(true);
    const filLikelyTranscription = ref(true);

    const filterResults = computed(
      () : [APIOutput[], APIOutput[]] | null => {
        if (typeof recordsObject.value === 'string') {
          return null;
        }
        const result: APIOutput[] = [];
        const removed: APIOutput[] = [];
        recordsObject.value.forEach((el) => {
          if (resultFilterer(
            el,
            filVerified.value,
            filUnverified.value,
            filError.value,
            filDisplay.value,
            filSearch.value,
            filNoRecommendation.value,
            filLikelyTranscription.value,
          )) {
            result.push(el);
          } else {
            removed.push(el);
          }
        });
        return [result, removed];
      },
    );

    const getExportURL = (obj: APIOutput[], urlVar: string[]) => {
      const data = new Blob(
        [JSON.stringify(obj)], { type: 'application/json' },
      );
      if (urlVar.length !== 0) {
        URL.revokeObjectURL(urlVar[0]);
      }
      urlVar[0] = URL.createObjectURL(data);
      return urlVar[0];
    };

    const remainingURL: string[] = [];
    const exportRemaining = () => (
      filterResults.value === null ? '' : getExportURL(filterResults.value[0], remainingURL)
    );

    const removedURL: string[] = [];
    const exportRemoved = () => (
      filterResults.value === null ? '' : getExportURL(filterResults.value[1], removedURL)
    );

    const applyFilters = () => {
      if (filterResults.value === null) {
        return;
      }
      // eslint-disable-next-line
      textRecords.value = JSON.stringify(filterResults.value[0]);
    };

    const keepResultText = computed(() => {
      if (filterResults.value === null) {
        return '';
      }
      return JSON.stringify(filterResults.value[0]);
    });

    const auditedURL: string[] = [];
    const exportAudited = () => getExportURL(audited.value, auditedURL);
    const clearAudited = () => {
      audited.value = [];
      saveAudited();
    };
    const popRecord = () => {
      if (typeof recordsObject.value === 'string') {
        throw Error('No Records');
      }
      const [record] = recordsObject.value;
      recordsObject.value = recordsObject.value.slice(1);
      textRecords.value = JSON.stringify(recordsObject.value);
      return record;
    };

    const undo = () => {
      if (typeof recordsObject.value === 'string') { return; }
      const last = popAudited();
      if (last === undefined) { return; }

      recordsObject.value.splice(0, 0, last);
      textRecords.value = JSON.stringify(recordsObject.value);
    };

    const accept = () => {
      const auditRecord = popRecord() as APIAudited;
      const title = getHebrewTitle(auditRecord);
      let type: AuditT;
      if (auditRecord.type === APIOutputT.Verified) {
        type = AuditT.MatchedTitle;
      } else if (auditRecord.type === APIOutputT.Unverified) {
        type = AuditT.Converted;
      } else {
        return;
      }
      auditRecord.audit_result = { type, title };
      pushAudited(auditRecord);
    };

    const acceptEdited = () => {
      if (repContainers.value === null) {
        throw Error("don't accept edited with no input");
      }
      let title;
      if (showSimpleEditor.value === true) {
        title = simpleEditorText.value;
      } else {
        title = repContainers.value.map((rc) => rc.currRep).join(' ');
      }
      const auditRecord = popRecord() as APIAudited;
      auditRecord.audit_result = { type: AuditT.Edited, title };
      pushAudited(auditRecord);
    };

    const acceptTopQuery = () => {
      const record = popRecord();
      if (record.type !== 'unverified') {
        undo();
        throw Error('should only be possible to reach this code with unverified record.');
      }
      const unverified = record as APIUnverified;
      const title = delist(unverified.top_query_result.text);
      const auditRecord = record as APIAudited;
      auditRecord.audit_result = { type: AuditT.TopQuery, title };
      pushAudited(auditRecord);
      popRecord();
    };
    const reject = () => {
      const auditRecord = popRecord() as APIAudited;
      auditRecord.audit_result = { type: AuditT.Rejected, title: '' };
      pushAudited(auditRecord);
    };

    if (audited.value.length === 0) {
      const temp = window.localStorage.getItem('audited');
      if (temp !== null) {
        audited.value = JSON.parse(temp);
      }
    }
    if (textRecords.value === '') {
      const temp = window.localStorage.getItem('textRecords');
      if (temp !== null) {
        textRecords.value = temp;
      }
    }

    return {
      makeRepContainers,
      textRecords,
      recordsObject,
      currTab,
      isActive,
      Tab,
      currentRecord,
      currentConverted,
      loadFile,
      corrected,
      clearAudited,
      clearInput,
      accept,
      acceptEdited,
      acceptTopQuery,
      reject,
      undo,
      audited,
      showFullRecord,
      toggleRef,
      toggleFullRecord,
      showCorrectionInterface,
      showSimpleEditor,
      toggleSimpleEditor,
      simpleEditorText,
      toggleCorrectionInterface,
      deleteWord,
      addWord,
      moveWord,
      showAdvancedFilters,
      toggleAdvancedFilters,
      getTitle,
      getDate,
      getCreator,
      getPublisher,
      getHebrewTitle,
      currentHebrewTitle,
      filVerified,
      filUnverified,
      filError,
      filDisplay,
      filSearch,
      filNoRecommendation,
      filLikelyTranscription,
      filterResults,
      exportRemaining,
      exportRemoved,
      exportAudited,
      applyFilters,
      keepResultText,
      topQuery,
      delist,
      repContainers,
      applyQuery,
      activateEditor,
      boxSize,
    };
  },
});
</script>

<style>
  body {
    max-width: 40em;
    margin: auto;
    background: rgb(236, 236, 236);
  }
  a:link {
    color: rgb(0, 69, 126);
    text-decoration: none;
  }
  .linky {
    color: rgb(0, 69, 126);
    text-decoration: none;
  }
  a:visited {
    color: rgb(0, 69, 126);
    text-decoration: none;
  }
  a:hover {
    color: rgb(41, 123, 190);
    text-decoration: none;
  }
  textarea {
    min-width: 30em;
    min-height: 20em;
    border-color: lightgray;
    border-radius: 10px;
    border-style: solid;
  }
  button {
    color: white;
    background: rgb(3, 75, 134);
    border-style: solid;
    border-color: rgba(236, 236, 236);
    padding: 0.4em;

  }
  .active {
    color: rgb(3, 75, 134);
    background: white;
    border-style: solid;
    border-color: rgb(3, 75, 134);
    padding: 0.4em;

  }
  .flexcontainer {
    display: flex;
  }
  .worktitle {
    font-family: 'Times New Roman', Times, serif;
    font-size: 1.7em;
  }
  .hebrew {
    font-family: 'Frank Ruehl CLM', 'Times New Roman', Times, serif;
    font-size: 1.3em;
    direction: rtl;
  }
  .scrollbox {
    width: 400px;
    height: 200px;
    overflow-x: hidden;
    overflow-y: auto;
  }
.word-box {
    display: inline-block;
    /* margin: 5px; */
    text-align: center;
    vertical-align: top;
    padding: 0.5em;
}

.hover-me {
    position: relative;
}
.control {
    display: inline-block;
    text-align: center;
    vertical-align: middle;
}

input {
    font-family: "Linux Libertine", "Times New Roman", Times, serif;
    font-size:1em;
    color: #436;
    background-color: transparent;
    border-width: 0px 0px 1px 0px;
    border-color: #666;
    text-align: center;
}

.dropdown-content {
    display: none;
    position: absolute;
    background-color: #f9f9f9;
    /* box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
    padding: 3px 3px; */
    z-index: 1;
}

.hover-me:hover .dropdown-content {
  display: block;
}
</style>
