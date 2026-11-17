"""쇼다운 포커 Playwright 테스트 — Sean·Sharon 두 휴대폰 + Apps Script poker_() 흉내"""
import asyncio, json, os
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright

H = os.path.dirname(os.path.abspath(__file__))
U = f"file://{H}/out/index_mock.html"
DB = {}
KST = timezone(timedelta(hours=9))
def at(day, hour=21): return datetime.fromisoformat(f"{day}T{hour:02d}:00:00").replace(tzinfo=KST)

async def route(rt, req):
    if req.method == "POST":
        d = json.loads(req.post_data); k = (d["code"], d["day"], int(d["round"]), d["who"])
        if k in DB: return await rt.fulfill(status=200, body="locked")
        DB[k] = {"day": d["day"], "round": int(d["round"]), "who": d["who"], "disc": d["disc"], "bet": int(d["bet"])}
        return await rt.fulfill(status=200, body="ok")
    code = req.url.split("code=")[1][:4]
    return await rt.fulfill(status=200, content_type="application/json", body=json.dumps({"rows": [v for k, v in DB.items() if k[0] == code]}))

async def phone(b, name, day, code="0429"):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, accept_downloads=True)
    await ctx.route("https://mock.sheet.test/**", route); await ctx.route("https://fonts.googleapis.com/**", lambda r, q: r.abort())
    pg = await ctx.new_page(); pg.errs = []; pg.on("pageerror", lambda e: pg.errs.append(str(e)))
    await pg.clock.set_fixed_time(at(day)); await pg.goto(U)
    await pg.click(f".whob[data-w={name}]"); await pg.fill("#code", code); await pg.click("#btn-go"); await pg.wait_for_selector("#s-main.on")
    return pg

async def play(pg, cards, b):
    for i in cards: await pg.click(f"#my-hand .card:nth-child({i + 1})")
    await pg.click("#act .goldbtn")
    await pg.click(f"#act .bet:nth-child({ {0: 1, 2: 2, 5: 3, 10: 4}[b] })"); await pg.click("#act .goldbtn"); await pg.wait_for_timeout(2000)

async def main():
    ok = True; log = []
    def chk(c, m):
        nonlocal ok; ok &= bool(c); log.append(("OK  " if c else "FAIL") + " " + m)
    D = "2026-11-17"
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        sean = await phone(b, "Sean", D)
        chk(await sean.text_content("#season") == "11월 시즌" and await sean.text_content("#pl-Sean .c span") == "100", "시즌·시작 칩 100")
        init = await sean.evaluate(f"PK.dealt('0429','{D}',1,'Sean').init.map(c=>c.r+'-'+c.s)")
        shown = await sean.evaluate("[...document.querySelectorAll('#my-hand .card')].map(e=>e.textContent)")
        chk(len(shown) == 5 and await sean.locator("#op-hand .card.back").count() == 5, f"내 패 5장·상대 뒷면 {shown}")
        await sean.screenshot(path="shot_draw.png", full_page=True)
        # 1판: Sean 0,1번 교체 → 베팅 화면에서 새로고침해도 재교체 불가
        await sean.click("#my-hand .card:nth-child(1)"); await sean.click("#my-hand .card:nth-child(2)")
        chk("2장 교체" in await sean.text_content("#act .goldbtn"), "교체 장수 표시")
        await sean.click("#act .goldbtn"); fin1 = await sean.evaluate("[...document.querySelectorAll('#my-hand .card')].map(e=>e.textContent)")
        await sean.reload(); await sean.wait_for_selector("#s-main.on")
        fin2 = await sean.evaluate("[...document.querySelectorAll('#my-hand .card')].map(e=>e.textContent)")
        chk(fin1 == fin2 and await sean.locator("#act .bet").count() == 4, "교체 후 새로고침해도 같은 패·베팅 단계 유지")
        await sean.screenshot(path="shot_bet.png", full_page=True)
        await sean.click("#act .bet:nth-child(3)"); await sean.click("#act .goldbtn"); await sean.wait_for_timeout(2000)
        chk(DB[("0429", D, 1, "Sean")] == {"day": D, "round": 1, "who": "Sean", "disc": "0,1", "bet": 5}, f"1판 제출 {DB.get(('0429', D, 1, 'Sean'))}")
        chk("Sharon의 차례" in await sean.text_content("#act"), "상대 대기 화면")
        await sean.screenshot(path="shot_wait.png", full_page=True)

        sharon = await phone(b, "Sharon", D); await sharon.wait_for_timeout(600)
        chk("상대 대기 중" in await sharon.text_content("#rounds .rd:nth-child(1)") and "제출 완료" in await sharon.text_content("#op-st"), "Sharon: 상대가 냈다는 표시(패는 비공개)")
        chk(await sharon.locator("#op-hand .card.back").count() == 5, "쇼다운 전 상대 패 뒷면")
        await play(sharon, [], 10)
        exp = await sharon.evaluate(f"""(()=>{{const a=PK.final('0429','{D}',1,'Sean','0,1'),b=PK.final('0429','{D}',1,'Sharon','');
            return PK.settle({{bet:5,ev:PK.evaluate(a)}},{{bet:10,ev:PK.evaluate(b)}}).d}})()""")
        v = await sharon.text_content("#act .verdict h3")
        chk((exp > 0 and "Sean 승" in v) or (exp < 0 and "Sharon 승" in v) or (exp == 0 and "무승부" in v), f"쇼다운 판정 = 엔진 계산 (Sean {exp:+d}) / {v}")
        cs = [int(await sharon.text_content(f"#pl-{w} .c span")) for w in ("Sean", "Sharon")]
        chk(cs == [100 + exp, 100 - exp], f"칩 반영 {cs}")
        chk(await sharon.locator("#op-hand .card:not(.back)").count() == 5, "쇼다운 때 상대 패 공개")
        await sharon.screenshot(path="shot_show.png", full_page=True)
        async with sharon.expect_download(timeout=10000) as dl: await sharon.click("#btn-save")
        os.replace(await (await dl.value).path(), f"{H}/shot_card.png"); chk(os.path.getsize(f"{H}/shot_card.png") > 40000, "쇼다운 카드 저장")

        # 2판: Sean 폴드, Sharon 2칩 → Sharon +1 / 3판: 둘 다 2칩
        await sean.reload(); await sean.wait_for_selector("#s-main.on"); await sean.wait_for_timeout(500)
        chk("판" in await sean.text_content("#rounds .rd.on") and await sean.evaluate("document.querySelector('#rounds .rd.on b').textContent") == "2판", "다 낸 판 다음(2판)으로 자동 이동")
        await play(sean, [], 0); await sean.click("#rounds .rd:nth-child(3)"); await play(sean, [4], 2)
        await sharon.click("#rounds .rd:nth-child(2)"); await play(sharon, [0, 1, 2], 2)
        v2 = await sharon.text_content("#act .verdict")
        chk("Sharon 승" in v2 and "참가비 1칩" in v2, "상대 폴드 → 참가비 1칩")
        await sharon.click("#rounds .rd:nth-child(3)"); await play(sharon, [], 2)
        tot = await sharon.evaluate(f"""(()=>{{let n=0;const R=[[1,'0,1',5,'',10],[2,'',0,'0,1,2',2],[3,'4',2,'',2]];
            for(const [r,da,ba,db,bb] of R){{n+=PK.settle({{bet:ba,ev:PK.evaluate(PK.final('0429','{D}',r,'Sean',da))}},{{bet:bb,ev:PK.evaluate(PK.final('0429','{D}',r,'Sharon',db))}}).d}} return n}})()""")
        cs = [int(await sharon.text_content(f"#pl-{w} .c span")) for w in ("Sean", "Sharon")]
        chk(cs == [100 + tot, 100 - tot] and sum(cs) == 200, f"세 판 합산 칩 {cs} (Sean {tot:+d})")
        chk("오늘의 승자" in await sharon.text_content("#today"), f"오늘의 승자 표시: {await sharon.text_content('#today')}")
        await sean.reload(); await sean.wait_for_timeout(700)
        chk([int(await sean.text_content(f"#pl-{w} .c span")) for w in ("Sean", "Sharon")] == cs, "두 휴대폰 칩 일치")
        await sean.click("[data-p=rec]"); await sean.wait_for_timeout(300)
        chk(await sean.text_content("#r-hands") == "3", "전적: 3판")
        await sean.screenshot(path="shot_rec.png", full_page=True)

        # 12월: 새 시즌, 11월 칩왕 1회
        await sean.clock.set_fixed_time(at("2026-12-01")); await sean.reload(); await sean.wait_for_timeout(600)
        cs12 = [await sean.text_content(f"#pl-{w} .c span") for w in ("Sean", "Sharon")]
        await sean.click("[data-p=rec]"); sw = await sean.text_content("#a-seasons")
        chk(cs12 == ["100", "100"] and await sean.text_content("#season") == "12월 시즌", "12월 새 시즌 100:100")
        chk(sw == ("1 : 0" if tot > 0 else "0 : 1" if tot < 0 else "0 : 0"), f"지난 시즌 칩왕 {sw}")
        chk(len({str(await sean.evaluate("JSON.stringify(PK.dealt('0429','2026-12-01',1,'Sean').init)"))}) == 1, "새 날짜 새 카드")
        chk(not (sean.errs or sharon.errs), f"페이지 오류 없음 {sean.errs + sharon.errs}")
        await b.close()
    print("\n".join(log)); print("ALL OK" if ok else "SOME FAILED")

asyncio.run(main())
