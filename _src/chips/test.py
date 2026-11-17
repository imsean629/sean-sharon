"""칩 테이블 3기기 테스트 — 로컬 PeerJS 서버(127.0.0.1:9000) + http.server(8765)"""
import asyncio, os
from playwright.async_api import async_playwright
H = os.path.dirname(os.path.abspath(__file__))
B = "http://127.0.0.1:8765/index_mock.html?peerhost=127.0.0.1&peerport=9000&code=0429&as="

async def dev(b, who, w, h):
    ctx = await b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, has_touch=False)
    await ctx.route("https://fonts.googleapis.com/**", lambda r, q: r.abort())
    pg = await ctx.new_page(); pg.errs = []; pg.on("pageerror", lambda e: pg.errs.append(str(e))); pg.on("dialog", lambda d: asyncio.ensure_future(d.accept()))
    await pg.goto(B + who); return pg

async def swipe(pg, sel, dy=-160):
    box = await pg.locator(sel).bounding_box(); x = box["x"] + box["width"] / 2; y = box["y"] + box["height"] * 0.6
    await pg.mouse.move(x, y); await pg.mouse.down()
    for i in range(1, 7): await pg.mouse.move(x, y + dy * i / 6)
    await pg.mouse.up(); await pg.wait_for_timeout(900)

async def stacks(t):
    return await t.evaluate("(()=>{const s=window.__CT.S();return [s.p.Sean.stack,s.p.Sharon.stack,s.pot]})()")

async def main():
    ok = True; log = []
    def chk(c, m):
        nonlocal ok; ok &= bool(c); log.append(("OK  " if c else "FAIL") + " " + m)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome")
        t = await dev(b, "table", 820, 1180)
        await t.evaluate("localStorage.clear()"); await t.reload(); await t.wait_for_timeout(1500)
        sean = await dev(b, "Sean", 390, 844); sharon = await dev(b, "Sharon", 390, 844)
        await t.wait_for_function("document.querySelector('#t-conn').textContent.split('연결됨').length===3", timeout=15000)
        chk(True, "태블릿에 두 휴대폰 연결")
        await sean.wait_for_selector("#p-main:not([hidden])", timeout=8000)
        chk(await sean.text_content("#p-stack") == "1,000", "휴대폰에 내 칩 1,000")
        await t.screenshot(path="shot_t0.png")

        # 핸드 1: 블라인드 (딜러 Sean = SB 10, Sharon = BB 20)
        await t.click("#t-new"); await t.wait_for_timeout(900)
        chk(await stacks(t) == [990, 980, 30], f"핸드1 블라인드 {await stacks(t)}")
        await sean.wait_for_timeout(300)
        chk(await sean.text_content("#p-call") == "콜 10", f"Sean 콜 금액 {await sean.text_content('#p-call')}")
        # Sean: 콜 버튼 → 트레이 10 → 위로 스와이프
        await sean.click("#p-play .quick .btn:nth-child(1)")
        chk((await sean.text_content("#p-play .tray .amt")) == "10", "콜 누르면 트레이에 10")
        await sean.screenshot(path="shot_p_tray.png")
        await swipe(sean, "#p-play .tray")
        chk(await stacks(t) == [980, 980, 40], f"스와이프 베팅 → 팟 {await stacks(t)}")
        await t.wait_for_timeout(200); await t.screenshot(path="shot_t1.png")
        # Sharon 체크, 다음 카드
        await sharon.wait_for_timeout(300)
        chk(await sharon.text_content("#p-play .quick .btn:nth-child(1)") == "체크", "콜할 게 없으면 체크")
        await sharon.click("#p-play .quick .btn:nth-child(1)"); await t.wait_for_timeout(500)
        chk("Sharon 체크" in await t.text_content("#t-banner"), "체크가 테이블에 표시")
        await t.click("#t-street"); await t.wait_for_timeout(500)
        # Sean 칩 선택: 100 ×2 + 50 → 250 베팅
        for i in (3, 3, 2): await sean.click(f"#p-play .rack button:nth-child({i})")
        chk(await sean.text_content("#p-play .tray .amt") == "250", "칩 눌러 담기 100+100+50")
        await swipe(sean, "#p-play .tray", dy=-35)  # 짧게 끌면 취소
        chk(await stacks(t) == [980, 980, 40] and await sean.text_content("#p-play .tray .amt") == "250", "짧게 끌면 베팅 안 됨")
        await swipe(sean, "#p-play .tray")
        chk(await stacks(t) == [730, 980, 290], f"250 베팅 {await stacks(t)}")
        await sharon.wait_for_timeout(300)
        chk(await sharon.text_content("#p-call") == "콜 250" and "베팅 250" in await sharon.text_content("#p-oppbet"), "Sharon 화면에 콜 250")
        await sharon.screenshot(path="shot_p_sharon.png")
        # Sharon 폴드 → Sean이 팟 획득
        await sharon.click("#p-play .quick .btn:nth-child(4)"); await t.wait_for_timeout(1200)
        chk(await stacks(t) == [1020, 980, 0], f"폴드 → Sean 팟 획득 {await stacks(t)}")
        await sean.wait_for_timeout(300); chk(await sean.text_content("#p-stack") == "1,020", "Sean 휴대폰 1,020")

        # 핸드 2: Sharon 딜러. Sharon 올인, Sean 콜, Sean 승
        await t.click("#t-new"); await t.wait_for_timeout(800)
        chk(await stacks(t) == [1000, 970, 30], f"핸드2 블라인드 딜러 교대 {await stacks(t)}")
        await sharon.wait_for_timeout(300); await sharon.click("#p-play .quick .btn:nth-child(2)"); await swipe(sharon, "#p-play .tray")
        chk(await stacks(t) == [1000, 0, 1000], f"Sharon 올인 {await stacks(t)}")
        await sean.wait_for_timeout(300); await sean.click("#p-play .quick .btn:nth-child(1)")
        chk(await sean.text_content("#p-play .tray .amt") == "960", "Sean 콜 960")
        await swipe(sean, "#p-play .tray")
        chk(await stacks(t) == [40, 0, 1960], f"콜 → 팟 1960 {await stacks(t)}")
        await t.click("#w-a"); await t.wait_for_timeout(1300)
        chk(await stacks(t) == [2000, 0, 0], "Sean 승 → 2000")
        await t.screenshot(path="shot_t_win.png")
        await t.click("#t-undo"); await t.wait_for_timeout(500)
        chk(await stacks(t) == [40, 0, 1960], "되돌리기")
        await t.click("#w-split"); await t.wait_for_timeout(1200)
        s = await stacks(t); chk(s[0] + s[1] == 2000 and s[2] == 0 and abs(s[0] - 40 - 980) <= 0, f"찹 반반 {s}")

        # 재연결: Sean 폰 새로고침, 태블릿 새로고침(상태 유지)
        await sean.reload(); await sean.wait_for_selector("#p-main:not([hidden])", timeout=10000)
        chk(await sean.text_content("#p-stack") == f"{s[0]:,}", "Sean 휴대폰 새로고침 후 재연결")
        await t.reload(); await t.wait_for_timeout(1000)
        chk(await stacks(t) == s, "태블릿 새로고침해도 칩 유지")
        await t.wait_for_function("document.querySelector('#t-conn').textContent.split('연결됨').length===3", timeout=25000)
        chk(True, "태블릿 새로고침 후 두 휴대폰 자동 재연결")
        await sharon.wait_for_timeout(500)
        chk(await sharon.text_content("#p-stack") == f"{s[1]:,}", "재연결 후 Sharon 칩 일치")

        # 태블릿 단독 모드
        await t.click("#t-set"); await t.check("#o-local"); await t.click("#o-ok"); await t.wait_for_timeout(500)
        chk(await t.is_visible("#local-bot .tray") and await t.is_visible("#local-top .tray"), "단독 모드: 위·아래 칩 받침")
        await t.click("#t-new"); await t.wait_for_timeout(600); s0 = await stacks(t)
        await t.click("#local-bot .rack button:nth-child(3)"); await swipe(t, "#local-bot .tray", dy=-160)
        s1 = await stacks(t); chk(s1[2] == s0[2] + 100, f"아래 자리 위로 밀어 베팅 {s0}→{s1}")
        await t.click("#local-top .rack button:nth-child(3)"); await swipe(t, "#local-top .tray", dy=160)
        s2 = await stacks(t); chk(s2[2] == s1[2] + 100, f"위 자리(회전) 가운데로 밀어 베팅 {s2}")
        chk(sum(s2) == 2000, "칩 총합 항상 2000")
        await t.screenshot(path="shot_t_local.png")
        chk(not (t.errs or sean.errs or sharon.errs), f"페이지 오류 없음 {t.errs + sean.errs + sharon.errs}")
        await b.close()
    print("\n".join(log)); print("ALL OK" if ok else "SOME FAILED")

asyncio.run(main())
