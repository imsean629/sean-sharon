# 참여형 콘텐츠 제작 키트 (sean-sharon)

이 폴더는 GitHub Pages에 공개되지 않습니다(밑줄로 시작하는 폴더는 Jekyll이 제외).

| 폴더 | 콘텐츠 | 주소 |
|---|---|---|
| survey | 학원생 설문(학업·진로·AI), 초/중/고 분기 | /survey/ · 집계판 /survey/#board |
| balance | 오늘의 밸런스 게임 (Sean ♥ Sharon 전용, 커플 코드) | /balance/ (시작 페이지에 링크 안 함, noindex) |
| poker | 오늘의 쇼다운 (커플 1:1 드로우 포커, 하루 3판, 월 시즌) | /poker/ (링크 안 함, noindex) |
| apps_script_Code.gs | 모든 콘텐츠 공용 Apps Script (kind별 탭) | |
| gs_test/run.js | 가짜 Sheets로 Apps Script 검증 (`node run.js`) | |

각 콘텐츠 = `data.py`(문항·문구) + `template.html`(단일 파일 앱) + `build.py`(데이터·QR·html2canvas·SHEET_URL 주입 → out/index.html, out/index_mock.html) + `test.py`(Playwright, 가짜 시트 https://mock.sheet.test/**) + `poster.py`(A3 QR 포스터 PDF, og.png, QR 해독 확인).

## 복원
```bash
mkdir -p /home/claude/work && cp -r _src/* /home/claude/work/
mkdir -p /home/claude/work/fonts && cd /home/claude/work/fonts && npm i @fontsource/jua @fontsource/noto-sans-kr
pip install segno playwright pillow pyzbar --break-system-packages   # 크롬: /usr/bin/google-chrome, libzbar0 필요
cd /home/claude/work/survey && python3 build.py "<웹앱 URL>" && python3 test.py && python3 poster.py
```

## 공통 규칙
- 디자인: 파스텔(배경 #FFF7F2, 잉크 #3B3551, 포인트 핑크 #D9466B, 민트·하늘·라벤더 보조), 제목 Jua · 본문 Noto Sans KR, 로고 없음.
- 개인정보: 이름·학교·연락처를 받지 않음. sid는 참여 1회마다 무작위. 주관식은 시트에만, 집계(doGet)에서 제외.
- 시트 전송: `fetch(SHEET_URL, {method:'POST', mode:'no-cors', headers:{'Content-Type':'text/plain;charset=utf-8'}, body: JSON.stringify({kind, sid, ...})})` → TABS[kind] 탭에 sid 기준 upsert, =+-@ 시작 값은 ' 접두.
- 집계: `?type=<kind>` → `{count, by:{전체|초|중|고:{n, 문항:{값:개수}}}}`.
- 새 콘텐츠 = TABS에 추가 → Apps Script **배포 관리 → 새 버전**(URL 유지). 기존 탭에 열을 추가하면 탭을 지우고 다시 만들게 함.
- 대형 화면: 주소 뒤 `#board`.
- A3 포스터: 1123×1587px HTML → PDF 297×420mm, QR은 segno error='q'.

## 밸런스 게임 메모
- 날짜별 질문 = (그날 − LAUNCH 2026-11-17) % 질문 수. 사귄 날 START 2026-09-05 → D+일수.
- 벌칙·당첨자는 날짜+코드 해시로 두 휴대폰에서 같게 결정.
- 질문·벌칙: 구글 시트 '밸런스질문'·'밸런스벌칙' 탭(첫 조회 때 자동 생성)이 앱 기본값보다 우선. 행 순서 = 질문 순서.
- 기록: '밸런스' 탭 (day, code는 텍스트로 저장, sid = code_day_who 로 덮어쓰기).

## 쇼다운 포커 메모
- 카드는 서버에 저장하지 않음: 시드(코드|날짜|판)로 덱을 섞어 Sean 0~4·교체 10~14, Sharon 5~9·교체 15~19. 서버에는 교체 위치(disc)와 베팅(bet)만.
- '포커' 탭은 lock: 같은 sid(code_day_round_who) 재제출은 'locked'.
- 정산: 참가비 1. 폴드 −1. 둘 다 걸면 승자 +(1 + min(베팅)). 베팅 0/2/5/10.
- 시즌 = 달(KST). 각자 100칩에서 시작, 칩 = 100 ± 그달 합계.
- 이름·코드는 밸런스 게임과 같은 localStorage(bal_me, bal_code)를 공유.
- `node engine_test.js` 로 족보·정산 단위 테스트.
