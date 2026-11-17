"""Playwright 테스트 — 가짜 시트(https://mock.sheet.test/**)로 초/중/고 흐름, 전송 값, 건너뛰기, 비교, 카드 저장, 집계판 확인"""
import asyncio, json, os
from playwright.async_api import async_playwright
from data import QS, COLS

H = os.path.dirname(os.path.abspath(__file__))
U = f"file://{H}/out/index_mock.html"
DB = {}  # sid → row (Apps Script처럼 sid 기준 upsert)
PRIVATE = {"ts", "sid", "q10", "q18", "level"}

def tally():  # apps_script tally_() 와 같은 규칙
    by = {}
    for r in DB.values():
        for name in ("전체", r["level"]):
            b = by.setdefault(name, {"n": 0}); b["n"] += 1
            for k in COLS:
                if k in PRIVATE: continue
                for v in str(r.get(k, "")).split("|"):
                    v = v.strip()
                    if v: b.setdefault(k, {}); b[k][v] = b[k].get(v, 0) + 1
    return {"count": by.get("전체", {"n": 0})["n"], "by": by}

async def route(rt, req):
    if req.method == "POST":
        d = json.loads(req.post_data); DB[d["sid"]] = d
        return await rt.fulfill(status=200, body="ok")
    return await rt.fulfill(status=200, content_type="application/json", headers={"Access-Control-Allow-Origin": "*"}, body=json.dumps(tally(), ensure_ascii=False))

Q = {q["id"]: q for q in QS}
def opts(qid, L):
    o = Q[qid].get("opts"); return o if isinstance(o, list) else o[L]

async def play(pg, L, grade, picks):
    """picks: {qid: 값 | [값..] | 정수(척도) | 문자열(주관식)}; 없는 문항은 첫 선택지"""
    await pg.goto(U)
    await pg.click(f".lvl[data-l={L}]")
    await pg.click(f"#grades .grade:has-text('{grade}학년')")
    await pg.click("#btn-start")
    seen = []
    for _ in range(40):
        if await pg.is_visible("#s-done.on"): break
        txt = await pg.text_content("#q-text"); cnt = await pg.text_content("#q-count")
        qid = next(q["id"] for q in QS if (q["text"] if isinstance(q["text"], str) else q["text"].get(L)) == txt)
        seen.append(qid); q = Q[qid]; v = picks.get(qid)
        if q["type"] == "single":
            v = v or opts(qid, L)[0]
            await pg.click(f"#q-body .opt:text-is('{v}')")
            await pg.wait_for_function("t => document.querySelector('#q-text').textContent !== t || document.querySelector('#s-done.on')", arg=txt)
        elif q["type"] == "multi":
            for x in (v or [opts(qid, L)[0]]): await pg.click(f"#q-body .opt:text-is('{x}')")
            await pg.click("#btn-next")
        elif q["type"] == "scale":
            await pg.click(f"#q-body .sc:nth-child({v or 3})")
            await pg.wait_for_function("t => document.querySelector('#q-text').textContent !== t || document.querySelector('#s-done.on')", arg=txt)
        else:
            if v: await pg.fill("#q-input", v)
            await pg.click("#btn-next")
    await pg.wait_for_selector("#s-done.on")
    return seen

async def main():
    ok = True; log = []
    def chk(c, m):
        nonlocal ok; ok &= bool(c); log.append(("OK  " if c else "FAIL") + " " + m)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True, device_scale_factor=2)
        await ctx.route("https://mock.sheet.test/**", route)
        await ctx.route("https://fonts.googleapis.com/**", lambda r, q: r.abort())
        pg = await ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))

        await pg.goto(U); await pg.screenshot(path="shot_start.png", full_page=True)
        chk(await pg.is_disabled("#btn-start"), "학교급·학년 고르기 전 시작 버튼 비활성")

        # 1) 중학생 — 전 문항, 최대 2개 제한
        await pg.goto(U); await pg.click(".lvl[data-l=m]"); await pg.click("#grades .grade:has-text('2학년')"); await pg.click("#btn-start")
        await pg.screenshot(path="shot_q1.png", full_page=True)
        seen = await play(pg, "m", 2, {"q4": "문법", "q12": "주 몇 번", "q9": ["IT·AI", "교육"], "q13": ["숙제", "영어·번역"], "q6": 4, "q15": 5,
                                     "q10": "게임 개발자", "q18": "=수업 재밌어요 <b>", "q7": "일반고", "q17": ["게임", "팝송"]})
        chk(len(seen) == 19 and "q7" in seen and "q11" in seen, f"중학생 문항 수 {len(seen)} (19 예상)")
        r = list(DB.values())[-1]
        chk(r["level"] == "중" and r["grade"] == 2 and r["kind"] == "survey" and r["sid"], "학교급·학년·kind·sid 전송")
        chk(r["q9"] == "IT·AI|교육" and r["q13"] == "숙제|영어·번역" and r["q6"] == 4 and r["q15"] == 5, f"복수·척도 값: q9={r['q9']} q6={r['q6']}")
        chk(r["q10"] == "게임 개발자" and "<" not in r["q18"], f"주관식 정리: q18={r['q18']}")
        chk(set(COLS) - {"ts"} <= set(r.keys()), "응답 시트 열 이름과 전송 키 일치")
        chk(await pg.text_content("#fc-title") == "미래의 테크 리더", "결과 카드 제목(관심 분야 1순위 IT·AI)")
        await pg.wait_for_selector("#cmp:not([hidden])", timeout=8000)
        cmp = await pg.text_content("#cmp-list"); chk("100%" in cmp and "문법" in cmp, "친구들과 비교 표시")
        await pg.wait_for_timeout(600); await pg.screenshot(path="shot_done.png", full_page=True)
        async with pg.expect_download(timeout=10000) as dl: await pg.click("#btn-save")
        fn = (await dl.value).suggested_filename; path = await (await dl.value).path()
        chk(fn == "나의미래카드_미래의테크리더.png" and os.path.getsize(path) > 30000, f"카드 이미지 저장: {fn} {os.path.getsize(path)//1024}KB")
        os.replace(path, f"{H}/shot_card.png")

        # 2) 초등학생 — 문항 축소, AI 안 써봄 → q13 건너뜀, 주관식 건너뛰기
        seen = await play(pg, "e", 5, {"q12": "안 써봄", "q9": ["스포츠"], "q4": "말하기"})
        chk("q13" not in seen and "q7" not in seen and "q14" not in seen and len(seen) == 14, f"초등 문항 {len(seen)}개, q13 건너뜀 {seen}")
        r = list(DB.values())[-1]
        chk(r["level"] == "초" and r["q13"] == "" and r["q7"] == "" and r["q10"] == "", "초등: 해당 없는 문항은 빈 값")
        chk(await pg.text_content("#fc-title") == "미래의 국가대표", "초등 카드 제목")

        # 3) 고등학생 — 문항 선택지 분기
        await pg.goto(U); await pg.click(".lvl[data-l=h]"); await pg.click("#grades .grade:has-text('3학년')"); await pg.click("#btn-start")
        for _ in range(5):
            if (await pg.text_content("#q-text")) == "영어를 배우는 이유는?": break
            if await pg.is_visible("#q-body .opt"):
                c = await pg.text_content("#q-count"); first = pg.locator("#q-body .opt").first; await first.click()
                if await pg.is_enabled("#btn-next") and "multi" in (await pg.get_attribute("#q-body .opts", "class")): await pg.click("#btn-next")
                await pg.wait_for_function(f"document.querySelector('#q-count').textContent !== '{c}'")
        o = await pg.locator("#q-body .opt").all_text_contents()
        chk([x.replace("✓", "") for x in o] == ["내신", "수능", "진로", "해외(유학·여행)"], f"고등 q5 선택지 {o}")
        for x in ["내신", "수능", "진로"]: await pg.click(f"#q-body .opt:text-is('{x}')")
        w = await pg.text_content("#q-warn"); sel = await pg.locator("#q-body .opt.sel").count()
        chk(sel == 2 and "최대 2개" in w, "복수 선택 최대 2개 제한")
        await pg.screenshot(path="shot_multi.png", full_page=True)
        seen = await play(pg, "h", 3, {"q9": ["의료"]})
        chk(len(seen) == 19, f"고등 문항 수 {len(seen)}")

        # 4) 집계판
        bp = await ctx.new_page(); await bp.set_viewport_size({"width": 1920, "height": 1080})
        await bp.goto(U + "#board"); await bp.wait_for_function("document.querySelector('#bd-sum').textContent.indexOf('명 참여') >= 0", timeout=8000)
        s = await bp.text_content("#bd-sum"); chk("3명 참여" in s and "초등 1" in s and "중등 1" in s and "고등 1" in s, f"집계판 요약: {s}")
        chk(await bp.locator(".panel").count() == 8, "집계판 패널 8개")
        await bp.screenshot(path="shot_board.png")
        await bp.keyboard.press("3"); await bp.wait_for_timeout(300)
        chk("on" in (await bp.get_attribute(".bd-tab:nth-child(3)", "class")), "숫자 키로 학교급 전환")
        body = json.dumps(tally(), ensure_ascii=False)
        chk("게임 개발자" not in body and "수업" not in body, "집계에 주관식이 나가지 않음")

        # 5) 미리보기(시트 미연결) 모드에서도 오류 없이 동작
        pv = await ctx.new_page(); await pv.goto(f"file://{H}/out/index.html")
        chk(await pv.is_visible("#s-start.on"), "실제 파일 시작 화면")
        chk(not errs, f"페이지 오류 없음 {errs}")
        await b.close()
    print("\n".join(log)); print("ALL OK" if ok else "SOME FAILED")

asyncio.run(main())
