/**
 * sean-sharon 참여형 콘텐츠 — 응답 수집용 Google Apps Script (콘텐츠 공용)
 *  1) 학원생 설문(학업·진로·AI)  https://imsean629.github.io/sean-sharon/survey/   → '설문응답' 탭
 *  2) 오늘의 밸런스 게임(커플)     https://imsean629.github.io/sean-sharon/balance/  → '밸런스' 탭
 *  3) 오늘의 쇼다운(커플 포커)      https://imsean629.github.io/sean-sharon/poker/    → '포커' 탭 (제출한 판은 수정 불가)
 *     질문·벌칙은 '밸런스질문'·'밸런스벌칙' 탭에서 고치면 앱에 바로 반영됩니다(처음 접속 때 기본값으로 자동 생성).
 *     질문 순서 = 탭의 행 순서. 행을 추가/삭제하면 이후 날짜의 질문 배정이 바뀌니, 중간 삽입보다 끝에 추가를 권장합니다.
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
  balance: {
    name: '밸런스',
    cols: ['ts', 'sid', 'day', 'code', 'who', 'pick', 'memo'],
    text: { memo: 30 },
    asText: ['day', 'code'],                // 날짜·코드가 숫자/날짜로 바뀌지 않게 텍스트로 저장
  },
  poker: {
    name: '포커',
    cols: ['ts', 'sid', 'day', 'round', 'code', 'who', 'disc', 'bet'],
    asText: ['day', 'code', 'disc'],
    lock: true,                             // 한 번 낸 패·베팅은 덮어쓰지 않음
  },
};
const BAL_Q_TAB = '밸런스질문', BAL_P_TAB = '밸런스벌칙';

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
  if (kind === 'balance') {
    if (!/^\d{4}$/.test(String(d.code)) || !/^\d{4}-\d{2}-\d{2}$/.test(String(d.day))) return false;
    if (['Sean', 'Sharon'].indexOf(d.who) < 0 || ['A', 'B'].indexOf(d.pick) < 0) return false;
    d.sid = [d.code, d.day, d.who].join('_');  // 한 사람이 하루 한 번 (다시 고르면 덮어쓰기)
  }
  if (kind === 'poker') {
    if (!/^\d{4}$/.test(String(d.code)) || !/^\d{4}-\d{2}-\d{2}$/.test(String(d.day))) return false;
    if (['Sean', 'Sharon'].indexOf(d.who) < 0 || [1, 2, 3].indexOf(Number(d.round)) < 0) return false;
    if ([0, 2, 5, 10].indexOf(Number(d.bet)) < 0 || !/^([0-4](,[0-4]){0,4})?$/.test(String(d.disc || ''))) return false;
    d.round = Number(d.round); d.bet = Number(d.bet); d.disc = String(d.disc || '');
    d.sid = [d.code, d.day, d.round, d.who].join('_');
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
    if (!kind || !valid_(kind, d) || !d.sid) return ContentService.createTextOutput('ignored');
    const t = TABS[kind], sh = sheet_(kind);
    d.ts = new Date();
    const row = t.cols.map(c => {
      if (c === 'ts') return d.ts;
      const v = clean_(d[c], (t.text || {})[c]);
      return (t.asText || []).indexOf(c) >= 0 && String(v).charAt(0) !== "'" ? "'" + v : v;
    });
    const sidCol = t.cols.indexOf('sid') + 1, last = sh.getLastRow();
    if (last > 1) {
      const ids = sh.getRange(2, sidCol, last - 1, 1).getValues().map(r => String(r[0]));
      const i = ids.indexOf(String(d.sid));
      if (i >= 0) {
        if (t.lock) return ContentService.createTextOutput('locked');
        sh.getRange(i + 2, 1, 1, t.cols.length).setValues([row]); return ContentService.createTextOutput('updated');
      }
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
  if (p.type === 'balance') return balance_(String(p.code || ''));
  if (p.type === 'poker') return poker_(String(p.code || ''));
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

// 밸런스 게임: 커플 코드가 같은 기록 + 시트의 질문·벌칙
function balance_(code) {
  if (!/^\d{4}$/.test(code)) return json_({ error: 'code' });
  const ss = book_(), tz = 'Asia/Seoul';
  const fmt = v => v instanceof Date ? Utilities.formatDate(v, tz, 'yyyy-MM-dd') : String(v).replace(/^'/, '');
  const t = TABS.balance, sh = sheet_('balance'), last = sh.getLastRow();
  const rows = last > 1 ? sh.getRange(2, 1, last - 1, t.cols.length).getValues() : [];
  const at = c => t.cols.indexOf(c), out = [];
  rows.forEach(r => {
    let c = fmt(r[at('code')]); if (/^\d+$/.test(c)) c = ('0000' + c).slice(-4);
    if (c !== code) return;
    out.push({ day: fmt(r[at('day')]), who: String(r[at('who')]), pick: String(r[at('pick')]), memo: String(r[at('memo')]).replace(/^'/, '') });
  });
  return json_({ rows: out, questions: balTab_(ss, BAL_Q_TAB), penalties: balTab_(ss, BAL_P_TAB) });
}

// 쇼다운 포커: 커플 코드가 같은 판 기록 (카드는 앱이 날짜·판 번호로 똑같이 만들어 냄)
function poker_(code) {
  if (!/^\d{4}$/.test(code)) return json_({ error: 'code' });
  const tz = 'Asia/Seoul', fmt = v => v instanceof Date ? Utilities.formatDate(v, tz, 'yyyy-MM-dd') : String(v).replace(/^'/, '');
  const t = TABS.poker, sh = sheet_('poker'), last = sh.getLastRow(), at = c => t.cols.indexOf(c);
  const rows = last > 1 ? sh.getRange(2, 1, last - 1, t.cols.length).getValues() : [], out = [];
  rows.forEach(r => {
    let c = fmt(r[at('code')]); if (/^\d+$/.test(c)) c = ('0000' + c).slice(-4);
    if (c !== code) return;
    out.push({ day: fmt(r[at('day')]), round: Number(r[at('round')]), who: String(r[at('who')]), disc: String(r[at('disc')]).replace(/^'/, ''), bet: Number(r[at('bet')]) });
  });
  return json_({ rows: out });
}

function balTab_(ss, name) {
  let sh = ss.getSheetByName(name);
  if (!sh) {  // 처음이면 기본 질문·벌칙으로 만들어 둠
    sh = ss.insertSheet(name);
    const data = name === BAL_Q_TAB ? [['번호', '분류', 'A', 'B']].concat(BAL_DEFAULT_Q.map((q, i) => [i + 1].concat(q)))
                                    : [['번호', '벌칙']].concat(BAL_DEFAULT_P.map((p, i) => [i + 1, p]));
    sh.getRange(1, 1, data.length, data[0].length).setValues(data);
    sh.setFrozenRows(1);
  }
  const last = sh.getLastRow();
  if (last < 2) return [];
  const v = sh.getRange(2, 1, last - 1, name === BAL_Q_TAB ? 4 : 2).getValues();
  return name === BAL_Q_TAB ? v.filter(r => r[2] && r[3]).map(r => [String(r[1]), String(r[2]), String(r[3])])
                            : v.filter(r => r[1]).map(r => String(r[1]));
}

const BAL_DEFAULT_Q = [["데이트", "계획 완벽한 데이트", "그날 기분대로 즉흥 데이트"], ["데이트", "대구에서 만나기", "김해에서 만나기"], ["데이트", "바다", "산"], ["데이트", "맛집 웨이팅 1시간", "옆집 바로 입장"], ["데이트", "영화관", "집에서 넷플릭스"], ["데이트", "사진 100장 찍는 데이트", "사진 0장, 눈에만 담기"], ["데이트", "놀이공원", "전시회"], ["데이트", "아침 9시에 만나기", "저녁 6시에 만나기"], ["데이트", "드라이브 데이트", "기차 여행"], ["데이트", "비 오는 날 집 데이트", "비 오는 날 우산 쓰고 산책"], ["음식", "떡볶이", "치킨"], ["음식", "탕수육 부먹", "탕수육 찍먹"], ["음식", "민트초코", "반민초"], ["음식", "한 달간 라면 금지", "한 달간 커피 금지"], ["음식", "녹차", "홍차"], ["음식", "둘이 요리해 먹기", "배달 시켜 먹기"], ["음식", "마지막 한 조각 양보받기", "반으로 나눠 먹기"], ["음식", "평생 한식만", "평생 양식만"], ["연락", "하루 종일 카톡", "저녁에 1시간 통화"], ["연락", "긴 카톡 한 번", "짧은 카톡 여러 번"], ["연락", "영상통화", "음성통화"], ["연락", "이모티콘 폭탄", "텍스트만"], ["연락", "1분 안에 짧은 답장", "1시간 뒤 정성 가득한 답장"], ["연락", "매일 굿모닝 인사만", "매일 굿나잇 인사만"], ["연락", "음성 메시지", "손편지 사진"], ["일상", "깜짝 선물", "갖고 싶던 선물 정확히"], ["일상", "편지", "꽃"], ["일상", "커플템 티 나게", "커플템 은근히"], ["일상", "기념일 크게 챙기기", "평소에 자주 챙기기"], ["일상", "서운한 건 바로 말하기", "하루 생각하고 말하기"], ["일상", "친구들과 다 같이 놀기", "둘이서만 놀기"], ["일상", "상대 유튜브 알고리즘 구경", "상대 사진첩 구경"], ["일상", "주말 늦잠", "주말 아침 산책"], ["일상", "여행은 숙소가 좋은 곳", "여행은 맛집이 많은 곳"], ["일상", "여행 계획은 엑셀로 꼼꼼히", "여행은 그날그날 즉흥"], ["상상", "순간이동 (대구↔김해 0분)", "시간 멈추기"], ["상상", "10년 전으로 가서 더 일찍 만나기", "10년 뒤 우리 미리 보고 오기"], ["상상", "상대 속마음 하루 듣기", "상대 기억 하루 들여다보기"], ["상상", "무인도에 둘이 3일", "고급 호텔에 혼자 3일"], ["상상", "연애 프로그램 출연", "우리 연애가 웹툰으로 연재"], ["상상", "복권 당첨되면 바로 말하기", "깜짝 선물로 먼저 쓰기"], ["상상", "도시 아파트", "마당 있는 시골집"], ["상상", "강아지", "고양이"], ["상상", "평생 여름", "평생 겨울"], ["상상", "눈 오는 날", "벚꽃 피는 날"], ["우리", "처음 만난 날로 돌아가기", "가장 행복했던 날로 돌아가기"], ["우리", "Sharon이 영어로만 말하는 하루", "Sean이 사투리 금지인 하루"], ["우리", "Sean이 영어 수업 하기", "Sharon이 엑셀 보고서 만들기"], ["우리", "다도 체험 데이트", "카페 투어 데이트"], ["우리", "연애 기록은 사진으로", "연애 기록은 글로"], ["우리", "서로 옷 골라주기", "서로 머리 스타일 골라주기"], ["우리", "질투 조금 하는 연인", "질투 전혀 안 하는 연인"], ["우리", "요리 잘하는 연인", "정리정돈 잘하는 연인"], ["우리", "아플 때 죽 사 들고 오기", "아플 때 푹 자게 두기"], ["우리", "데이트 비용 번갈아 내기", "데이트 통장 만들기"], ["우리", "커플 사진 프사", "프사는 각자"], ["기타", "노래방 발라드", "노래방 댄스곡"], ["기타", "공포영화", "로맨틱 코미디"], ["기타", "운동 같이 하기", "게임 같이 하기"], ["기타", "지금 당장 10분 만나기", "이번 주말 하루 종일 만나기"]];
const BAL_DEFAULT_P = ["다음 통화 때 애교 한 번 (거절 불가)", "상대가 고른 쪽이 맞는 이유 3가지 말하기", "오늘 밤 굿나잇 음성 메시지 보내기", "다음 데이트 커피 쏘기", "상대 칭찬 5개 카톡으로 보내기", "상대가 골라 준 프사 하루 동안 쓰기", "다음 만날 때 사진 포즈는 상대 맘대로", "상대가 고른 노래 한 소절 불러서 보내기", "지금 셀카 한 장 보내기", "다음 데이트 메뉴 결정권 넘기기", "오늘 카톡 3번 말끝마다 ‘~했쪄’ 붙이기", "처음 봤을 때 첫인상 솔직하게 말하기", "Sharon이 내는 영어 문제 1개 맞히기 (틀리면 하나 더)", "다음 만날 때 손편지 3줄", "상대가 고른 이모티콘 하나 선물", "우리 처음 만난 날 기억나는 장면 하나 적기", "다음 통화 10분은 상대 이야기만 듣기", "내일 아침 굿모닝 인사 먼저 하기", "상대가 골라 준 차 한 잔 마시고 인증하기", "오늘 있었던 일 3줄 일기 보내기"];

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
