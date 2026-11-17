/**
 * sean-sharon 참여형 콘텐츠 — 응답 수집용 Google Apps Script (콘텐츠 공용)
 *  1) 학원생 설문(학업·진로·AI)  https://imsean629.github.io/sean-sharon/survey/  → '설문응답' 탭
 *
 * 설치
 *  1. 응답을 받을 구글 스프레드시트를 열고 [확장 프로그램 → Apps Script]를 누릅니다.
 *  2. 기본 코드를 지우고 이 파일 전체를 붙여넣은 뒤 저장합니다.
 *     (시트에서 바로 열었으면 SHEET_ID는 비워 둬도 됩니다. 별도 프로젝트라면 시트 ID를 넣으세요.)
 *  3. [배포 → 새 배포 → 유형: 웹 앱] / 실행 사용자: 나 / 액세스 권한: 모든 사용자 → 배포
 *  4. 나온 웹 앱 URL(https://script.google.com/macros/s/…/exec)을 알려 주세요.
 *  코드를 고친 뒤에는 [배포 → 배포 관리 → 수정(연필) → 버전: 새 버전]으로 올려야 URL이 유지됩니다.
 *
 * 개인정보: 이름·연락처·학교명은 받지 않습니다. sid는 설문 1회마다 만드는 무작위 값(재전송 시 덮어쓰기용)입니다.
 * 주관식(q10 장래희망, q18 선생님께 한마디)은 시트에만 저장되고 집계 화면에는 나오지 않습니다.
 */
const SHEET_ID = ''; // 비워 두면 이 스크립트가 붙어 있는 시트를 사용

const TABS = {
  survey: {
    name: '설문응답',
    cols: ['ts', 'sid', 'level', 'grade', 'q1', 'q2_like', 'q2_hard', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9', 'q10',
      'q11', 'q12', 'q13', 'q14', 'q15', 'q16', 'q17', 'q18'],
    text: { q10: 20, q18: 100 },            // 주관식 글자 수 제한
    private: ['ts', 'sid', 'q10', 'q18'],   // 집계(doGet)에서 제외
  },
};

function book_() { return SHEET_ID ? SpreadsheetApp.openById(SHEET_ID) : SpreadsheetApp.getActiveSpreadsheet(); }

function sheet_(kind) {
  const t = TABS[kind], ss = book_();
  let sh = ss.getSheetByName(t.name);
  if (!sh) { sh = ss.insertSheet(t.name); sh.appendRow(t.cols); sh.setFrozenRows(1); }
  return sh;
}

function clean_(v, max) {
  if (v === null || v === undefined) return '';
  if (typeof v === 'number') return isFinite(v) ? v : '';
  let s = String(v).replace(/[<>]/g, '').replace(/\s+/g, ' ').trim().slice(0, max || 200);
  if (/^[=+\-@]/.test(s)) s = "'" + s; // 수식 주입 방지
  return s;
}

function valid_(kind, d) {
  if (kind === 'survey') {
    if (['초', '중', '고'].indexOf(d.level) < 0) return false;
    const g = Number(d.grade);
    if (!(g >= 1 && g <= 6)) return false;
    if (d.level !== '초' && g > 3) return false;
  }
  return true;
}

// 응답 기록: 같은 sid면 그 행을 갱신, 아니면 새 행
function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const d = JSON.parse(e.postData.contents);
    const kind = d && TABS[d.kind] ? d.kind : null;
    if (!kind || !d.sid || !valid_(kind, d)) return ContentService.createTextOutput('ignored');
    const t = TABS[kind], sh = sheet_(kind);
    d.ts = new Date();
    const row = t.cols.map(c => c === 'ts' ? d.ts : clean_(d[c], (t.text || {})[c]));
    const sidCol = t.cols.indexOf('sid') + 1, last = sh.getLastRow();
    if (last > 1) {
      const ids = sh.getRange(2, sidCol, last - 1, 1).getValues().map(r => String(r[0]));
      const i = ids.indexOf(String(d.sid));
      if (i >= 0) { sh.getRange(i + 2, 1, 1, t.cols.length).setValues([row]); return ContentService.createTextOutput('updated'); }
    }
    sh.appendRow(row);
    return ContentService.createTextOutput('ok');
  } finally {
    lock.releaseLock();
  }
}

// 집계 조회: ?type=survey → {count, by:{전체:{n, q4:{단어:3,…}, …}, 초:{…}, 중:{…}, 고:{…}}}
//  복수 응답(a|b)은 항목별로 셉니다. 주관식·시각·sid는 내보내지 않습니다.
function doGet(e) {
  const p = (e && e.parameter) || {};
  if (p.type === 'survey') return tally_('survey');
  return json_({ ok: true });
}

function tally_(kind) {
  const t = TABS[kind], sh = sheet_(kind), last = sh.getLastRow();
  const rows = last > 1 ? sh.getRange(2, 1, last - 1, t.cols.length).getValues() : [];
  const keys = t.cols.filter(c => (t.private || []).indexOf(c) < 0 && c !== 'level');
  const lv = t.cols.indexOf('level'), by = {};
  const bucket = name => by[name] || (by[name] = { n: 0 });
  rows.forEach(r => {
    const level = String(r[lv]).replace(/^'/, '');
    if (!level) return;
    [bucket('전체'), bucket(level)].forEach(b => {
      b.n++;
      keys.forEach(k => {
        String(r[t.cols.indexOf(k)]).replace(/^'/, '').split('|').forEach(v => {
          v = v.trim(); if (!v) return;
          const m = b[k] || (b[k] = {});
          m[v] = (m[v] || 0) + 1;
        });
      });
    });
  });
  return json_({ count: (by['전체'] || { n: 0 }).n, by: by });
}

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
