"""밸런스 게임 Playwright 테스트 — Sean·Sharon 두 휴대폰, Apps Script balance_()를 흉내 낸 가짜 시트"""
import asyncio, json, os
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright
from data import QUESTIONS, PENALTIES

H = os.path.dirname(os.path.abspath(__file__))
U = f"file://{H}/out/index_mock.html"
DB = {}            # (code, day, who) → row
SHEET_Q = None     # 시트에서 질문을 고친 상황 흉내

async def route(rt, req):
    if req.method == "POST":
        d = json.loads(req.post_data)
        if d.get("kind") == "balance" and len(d["code"]) == 4 and d["who"] in ("Sean", "Sharon") and d["pick"] in ("A", "B"):
            DB[(d["code"], d["day"], d["who"])] = {k: d[k] for k in ("day", "who", "pick", "memo")}
        return await rt.fulfill(status=200, body="ok")
    code = req.url.split("code=")[1][:4]
    rows = [v for k, v in DB.items() if k[0] == code]
    body = {"rows": rows, "questions": SHEET_Q or QUESTIONS, "penalties": PENALTIES}
    return await rt.fulfill(status=200, content_type="application/json", headers={"Access-Control-Allow-Origin": "*"}, body=json.dumps(body, ensure_ascii=False))

KST = timezone(timedelta(hours=9))
def at(day, hour=13): return datetime.fromisoformat(f"{day}T{hour:02d}:00:00").replace(tzinfo=KST)

async def phone(b, name, code, day):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, accept_downloads=True)
    await ctx.route("https://mock.sheet.test/**", route)
    await ctx.route("https://fonts.googleapis.com/**", lambda r, q: r.abort())
    pg = await ctx.new_page(); pg.errs = []; pg.on("pageerror", lambda e: pg.errs.append(str(e)))
    await pg.clock.set_fixed_time(at(day)); await pg.goto(U)
    await pg.click(f".whob[data-w={name}]"); await pg.fill("#code", code); await pg.click("#btn-go")
    await pg.wait_for_selector("#s-main.on")
    return pg

async def goto_day(pg, day):
    await pg.clock.set_fixed_time(at(day)); await pg.reload(); await pg.wait_for_selector("#s-main.on"); await pg.wait_for_timeout(400)

async def pick(pg, k, memo=""):
    await pg.click(f".opt.{k}"); await pg.fill("#memo", memo); await pg.click("#btn-pick"); await pg.wait_for_timeout(2200)

async def main():
    global SHEET_Q
    ok = True; log = []
    def chk(c, m):
        nonlocal ok; ok &= bool(c); log.append(("OK  " if c else "FAIL") + " " + m)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        # 시작 화면
        ctx0 = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2); pg0 = await ctx0.new_page()
        await pg0.route("https://fonts.googleapis.com/**", lambda r, q: r.abort()); await pg0.goto(U)
        await pg0.click(".whob[data-w=Sean]"); await pg0.fill("#code", "04a2"); v = await pg0.input_value("#code")
        chk(v == "042" and await pg0.is_disabled("#btn-go"), f"코드는 숫자 4자리만 ({v})")
        await pg0.fill("#code", "0429"); await pg0.screenshot(path="shot_setup.png", full_page=True)

        D1, D2, D3, D4 = "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20"
        sean = await phone(b, "Sean", "0429", D1)
        chk(await sean.text_content("#dday") == "D+74", f"사귄 날 9/5 기준 {await sean.text_content('#dday')}")
        chk(await sean.text_content("#tA") == QUESTIONS[0][1] and "#1" in await sean.text_content("#q-date"), "출시일(11/17)은 1번 질문")
        await sean.screenshot(path="shot_today.png", full_page=True)
        await pick(sean, "A", "계획은 내가 짤게")
        chk(DB[("0429", D1, "Sean")]["pick"] == "A" and DB[("0429", D1, "Sean")]["memo"] == "계획은 내가 짤게", "Sean 답·한마디 전송")
        chk(await sean.is_visible("#wait") and "Sharon" in await sean.text_content("#lock-t"), "상대 대기 🔒 표시")
        await sean.screenshot(path="shot_wait.png", full_page=True)

        sharon = await phone(b, "Sharon", "0429", D1); await sharon.wait_for_timeout(600)
        chk(await sharon.text_content("#mA") == "" and await sharon.text_content("#mB") == "", "내가 고르기 전엔 상대 답이 안 보임")
        h = await sharon.evaluate("document.querySelector('[data-p=hist]').click(), document.querySelector('#hist').textContent")
        chk("🔒" in h and "계획은 내가" not in h, "기록 탭에서도 상대 답 잠금")
        await sharon.click("[data-p=today]")
        await pick(sharon, "B", "즉흥이 설레지")
        chk(await sharon.is_visible("#res") and "엇갈" in await sharon.text_content("#res-h"), "다르게 고르면 엇갈림")
        await sharon.click("#flip"); await sharon.wait_for_timeout(700)
        pw = await sharon.text_content("#pen-who"); pt = await sharon.text_content("#pen-t")
        chk(pt in PENALTIES and ("Sean" in pw or "Sharon" in pw), f"벌칙 카드: {pw} / {pt}")
        await sharon.screenshot(path="shot_diff.png", full_page=True)
        await sean.reload(); await sean.wait_for_timeout(800)
        chk(await sean.text_content("#pen-t") == pt and await sean.text_content("#pen-who") == pw, "두 휴대폰에 같은 벌칙·당첨자")
        chk("즉흥이 설레지" in await sean.text_content("#mB"), "상대 한마디 공개")
        async with sean.expect_download(timeout=10000) as dl: await sean.click("#btn-save")
        fp = await (await dl.value).path(); os.replace(fp, f"{H}/shot_card.png")
        chk(os.path.getsize(f"{H}/shot_card.png") > 30000, "오늘의 우리 카드 저장")

        # 2일차: 둘 다 같은 답 + 다시 고르기
        await goto_day(sean, D2); await goto_day(sharon, D2)
        chk(await sean.text_content("#tA") == QUESTIONS[1][1], "다음 날은 2번 질문")
        await pick(sean, "A"); await sean.click("#btn-repick"); await pick(sean, "B")
        chk(DB[("0429", D2, "Sean")]["pick"] == "B" and sum(1 for k in DB if k[1] == D2) == 1, "상대가 고르기 전 다시 고르기(덮어쓰기)")
        await sharon.reload(); await sharon.wait_for_timeout(600); await pick(sharon, "B")
        chk("통했다" in await sharon.text_content("#res-h") and await sharon.is_hidden("#flip"), "같은 답이면 통했다(벌칙 없음)")
        await sharon.screenshot(path="shot_same.png", full_page=True)

        # 4일차: 3일차를 건너뜀 → 놓친 문제 안내, 풀기
        await goto_day(sean, D4)
        chk(await sean.is_visible("#miss") and "어제" in await sean.text_content("#miss-t"), "어제 놓친 문제 안내")
        await sean.click("#miss-b"); chk(await sean.text_content("#tA") == QUESTIONS[2][1] and await sean.is_visible("#q-back"), "놓친 문제 열기")
        await pick(sean, "A"); chk(("0429", D3, "Sean") in DB, "지난 날짜로 저장")
        await sean.click("#q-back")
        await sean.click("[data-p=hist]"); await sean.wait_for_timeout(300)
        st = [await sean.text_content(x) for x in ("#s-days", "#s-rate", "#s-cur", "#s-best")]
        chk(st == ["2", "50%", "0", "1"], f"기록 통계 함께/일치율/연속/최고 = {st}")
        await sean.screenshot(path="shot_hist.png", full_page=True)

        # 시트에서 질문을 고치면 반영
        SHEET_Q = [list(q) for q in QUESTIONS]; SHEET_Q[3][1] = "시트에서 고친 질문"
        await sean.click("[data-p=today]"); await sean.reload(); await sean.wait_for_timeout(900)
        chk(await sean.text_content("#tA") == "시트에서 고친 질문", "구글 시트 질문 수정이 앱에 반영")

        # 코드가 다르면 안내
        other = await phone(b, "Sharon", "1234", D4); await other.wait_for_timeout(600)
        await pick(other, "A"); await other.click("[data-p=hist]")
        chk(await other.is_visible("#h-hint") and "1234" in await other.text_content("#h-hint"), "코드가 다르면 확인 안내")
        chk(not (sean.errs or sharon.errs or other.errs), f"페이지 오류 없음 {sean.errs + sharon.errs + other.errs}")
        await b.close()
    print("\n".join(log)); print("ALL OK" if ok else "SOME FAILED")

asyncio.run(main())
