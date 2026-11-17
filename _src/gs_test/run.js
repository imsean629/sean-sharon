const fs=require('fs');
// --- 가짜 Sheets: 실제처럼 "'" 접두는 텍스트로 저장, 아니면 숫자·날짜로 자동 변환
function conv(v){ if(typeof v!=='string') return v; if(v.startsWith("'")) return v.slice(1);
  if(/^\d+$/.test(v)) return Number(v); if(/^\d{4}-\d{2}-\d{2}$/.test(v)) return new Date(v+'T00:00:00+09:00'); return v; }
function Sheet(name){ this.name=name; this.d=[]; }
Sheet.prototype={ appendRow(r){this.d.push(r.map(conv));}, setFrozenRows(){}, getLastRow(){return this.d.length;},
  getRange(r,c,nr,nc){ const S=this; return { getValues(){ return S.d.slice(r-1,r-1+nr).map(x=>{const y=x.slice(c-1,c-1+nc); while(y.length<nc) y.push(''); return y;}); },
    setValues(v){ v.forEach((row,i)=>{ S.d[r-1+i]=S.d[r-1+i]||[]; row.forEach((x,j)=>S.d[r-1+i][c-1+j]=conv(x)); }); } }; } };
const book={tabs:{}, getSheetByName(n){return this.tabs[n]||null;}, insertSheet(n){return this.tabs[n]=new Sheet(n);}};
global.SpreadsheetApp={getActiveSpreadsheet:()=>book, openById:()=>book};
global.LockService={getScriptLock:()=>({waitLock(){},releaseLock(){}})};
global.ContentService={MimeType:{JSON:'json'}, createTextOutput:(t)=>({t, setMimeType(){return this;}, getContent(){return this.t;}})};
global.Utilities={formatDate:(d)=>new Date(d.getTime()+9*3600e3).toISOString().slice(0,10)};
eval(fs.readFileSync('../apps_script_Code.gs','utf8')+';global.doPost=doPost;global.doGet=doGet;');
const post=o=>doPost({postData:{contents:JSON.stringify(o)}}).getContent();
const get=p=>JSON.parse(doGet({parameter:p}).getContent());
let ok=true; const chk=(c,m)=>{ok=ok&&c;console.log((c?'OK  ':'FAIL')+' '+m);};
chk(post({kind:'balance',code:'0429',day:'2026-11-17',who:'Sean',pick:'A',memo:'=바다가 좋아'})==='ok','Sean 오늘 답 저장');
chk(post({kind:'balance',code:'0429',day:'2026-11-17',who:'Sean',pick:'B',memo:''})==='updated','같은 날 다시 고르면 덮어쓰기');
chk(post({kind:'balance',code:'0429',day:'2026-11-17',who:'Sharon',pick:'B'})==='ok','Sharon 저장');
chk(post({kind:'balance',code:'1111',day:'2026-11-17',who:'Sean',pick:'A'})==='ok','다른 코드');
chk(post({kind:'balance',code:'04a9',day:'2026-11-17',who:'Sean',pick:'A'})==='ignored','잘못된 코드 무시');
chk(post({kind:'balance',code:'0429',day:'2026-11-17',who:'Tom',pick:'A'})==='ignored','이름 검증');
const g=get({type:'balance',code:'0429'});
chk(g.rows.length===2 && g.rows.every(r=>r.day==='2026-11-17'), '코드별 조회: '+JSON.stringify(g.rows));
chk(g.questions.length===60 && g.penalties.length===20, '질문·벌칙 탭 자동 생성 '+g.questions.length+'/'+g.penalties.length);
chk(book.tabs['밸런스'].d[1][3]==='0429' && typeof book.tabs['밸런스'].d[1][2]==='string','코드 0429·날짜가 텍스트로 유지');
book.tabs['밸런스질문'].d[1][2]='수정된 A'; chk(get({type:'balance',code:'0429'}).questions[0][1]==='수정된 A','시트에서 고친 질문 반영');
chk(get({type:'balance',code:'12'}).error==='code','코드 형식 오류');
// 설문 회귀
chk(post({kind:'survey',sid:'x1',level:'중',grade:2,q1:'1~2시간',q9:'IT·AI|교육',q18:'=hi'})==='ok','설문 저장(회귀)');
const s=get({type:'survey'}); chk(s.count===1 && s.by['중'].q9['교육']===1 && !JSON.stringify(s).includes('hi'),'설문 집계(회귀)');
console.log(ok?'ALL OK':'SOME FAILED');
