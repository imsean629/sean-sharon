"""A3 QR 포스터(PDF·PNG) + 공유 미리보기 og.png 생성, QR 해독 확인"""
import asyncio, base64, os
from playwright.async_api import async_playwright
from PIL import Image
from pyzbar.pyzbar import decode

H = os.path.dirname(os.path.abspath(__file__))
URL = "https://imsean629.github.io/sean-sharon/survey/"
F = "/home/claude/work/fonts/node_modules/@fontsource"
qr = "data:image/svg+xml;base64," + base64.b64encode(open(f"{H}/out/qr.svg", "rb").read()).decode()
FONTS = "".join(f'<link rel="stylesheet" href="file://{F}/{x}">' for x in ["jua/400.css", "noto-sans-kr/400.css", "noto-sans-kr/700.css", "noto-sans-kr/900.css"])
BASE = """*{box-sizing:border-box}body{margin:0;font-family:'Noto Sans KR',sans-serif;color:#3B3551;word-break:keep-all}.jua{font-family:'Jua',sans-serif;font-weight:400}
.blob{position:absolute;border-radius:50%}"""

POSTER = f"""<!DOCTYPE html><html><head><meta charset="utf-8">{FONTS}<style>{BASE}
.pg{{width:1123px;height:1587px;position:relative;overflow:hidden;background:#FFF7F2;padding:96px 92px}}
.tag{{display:inline-block;padding:14px 30px;border-radius:999px;background:#FFFFFF;font-size:30px;font-weight:900;color:#D9466B;box-shadow:0 5px 0 #F0E2E8}}
h1{{margin:44px 0 0;font-size:128px;line-height:1.12;letter-spacing:-2px}} h1 em{{font-style:normal;color:#D9466B}}
.lead{{margin:30px 0 0;font-size:38px;line-height:1.55;color:#7A7290;font-weight:500}} .lead b{{color:#3B3551}}
.chips{{margin-top:36px;display:flex;gap:18px}} .chips span{{padding:16px 34px;border-radius:24px;font-size:38px;font-weight:900}}
.qrbox{{position:absolute;left:92px;right:92px;bottom:96px;background:#FFFFFF;border-radius:48px;padding:48px;display:flex;gap:48px;align-items:center;box-shadow:0 18px 48px rgba(217,70,107,.12)}}
.qrbox img{{width:400px;height:400px;display:block}}
.qrbox h2{{margin:0;font-size:62px;line-height:1.25}} .qrbox h2 em{{font-style:normal;color:#D9466B}}
.qrbox ul{{margin:26px 0 0;padding:0;list-style:none;font-size:32px;font-weight:700;line-height:1.9;white-space:nowrap;color:#7A7290}}
.qrbox ul li::before{{content:'';display:inline-block;width:16px;height:16px;border-radius:50%;background:#FF8FAB;margin-right:14px;vertical-align:middle}}
.url{{margin-top:22px;white-space:nowrap;font-size:20px;font-weight:700;color:#A59CB5}}
</style></head><body><div class="pg">
<i class="blob" style="width:620px;height:620px;background:#FFE3EA;top:-200px;right:-180px"></i>
<i class="blob" style="width:360px;height:360px;background:#BDEBD9;top:560px;left:-190px;opacity:.6"></i>
<i class="blob" style="width:300px;height:300px;background:#FFF0A8;top:330px;right:-90px;opacity:.7"></i>
<div style="position:relative">
<span class="tag">5분 · 이름 없이 · 익명 설문</span>
<h1 class="jua">우리 학원<br>친구들의 <em>생각</em>은?</h1>
<p class="lead">공부, 진로, AI에 대해 솔직하게 답해 주세요.<br>마지막에 <b>나의 미래 카드</b>를 받을 수 있어요!</p>
<div class="chips"><span style="background:#FFD9C2">공부</span><span style="background:#CFE6FF">진로</span><span style="background:#E2D8FF">AI</span></div>
</div>
<div class="qrbox"><img src="{qr}"><div><h2 class="jua">휴대폰 카메라로<br><em>QR</em>을 찍어요</h2>
<ul><li>초·중·고 맞춤 질문</li><li>이름은 묻지 않아요</li><li>나의 미래 카드 저장!</li></ul>
<div class="url">{URL.replace('https://', '')}</div></div></div>
</div></body></html>"""

OG = f"""<!DOCTYPE html><html><head><meta charset="utf-8">{FONTS}<style>{BASE}
.pg{{width:1200px;height:630px;position:relative;overflow:hidden;background:#FFF7F2;padding:72px 80px}}
h1{{margin:26px 0 0;font-size:92px;line-height:1.12}} h1 em{{font-style:normal;color:#D9466B}}
.tag{{display:inline-block;padding:10px 22px;border-radius:999px;background:#FFFFFF;font-size:26px;font-weight:900;color:#D9466B}}
p{{margin:26px 0 0;font-size:32px;color:#7A7290;font-weight:500}}
.card{{position:absolute;right:80px;top:110px;width:300px;height:410px;border-radius:30px;background:linear-gradient(160deg,#FFE6EE,#FFF3E6 55%,#EAF4FF);border:6px solid #FFFFFF;box-shadow:0 20px 40px rgba(217,70,107,.2);transform:rotate(6deg);padding:30px}}
.card small{{font-size:16px;font-weight:900;color:#D9466B}} .card b{{display:block;margin-top:14px;font-size:38px;line-height:1.2}}
.card i{{display:block;height:46px;border-radius:14px;background:rgba(255,255,255,.8);margin-top:14px}}
</style></head><body><div class="pg">
<i class="blob" style="width:420px;height:420px;background:#FFE3EA;top:-160px;left:520px"></i>
<div class="card"><small>MY FUTURE CARD</small><b class="jua">미래의<br>테크 리더</b><i></i><i></i><i></i><i></i></div>
<div style="position:relative"><span class="tag">공부 · 진로 · AI 5분 설문</span>
<h1 class="jua">우리 학원<br>친구들의 <em>생각</em>은?</h1><p>이름 없이 참여하고 나의 미래 카드 받기</p></div>
</div></body></html>"""

async def main():
    open(f"{H}/out/poster.html", "w").write(POSTER); open(f"{H}/out/og.html", "w").write(OG)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": 1123, "height": 1587}, device_scale_factor=2)
        await pg.goto(f"file://{H}/out/poster.html"); await pg.evaluate("document.fonts.ready")
        await pg.screenshot(path=f"{H}/out/poster_A3.png")
        await pg.pdf(path=f"{H}/out/poster_A3.pdf", width="297mm", height="420mm", print_background=True, scale=297 / (1123 * 25.4 / 96), margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        og = await b.new_page(viewport={"width": 1200, "height": 630})
        await og.goto(f"file://{H}/out/og.html"); await og.evaluate("document.fonts.ready")
        await og.screenshot(path=f"{H}/out/og.png")
        await b.close()
    d = decode(Image.open(f"{H}/out/poster_A3.png"))
    got = [x.data.decode() for x in d]
    print("QR 해독:", got, "OK" if got == [URL] else "FAIL")
    # PDF 페이지 수·크기 확인
    import re
    raw = open(f"{H}/out/poster_A3.pdf", "rb").read()
    print("PDF pages:", raw.count(b"/Type /Page") - raw.count(b"/Type /Pages"), re.findall(rb"/MediaBox \[[^\]]+\]", raw)[:1])

asyncio.run(main())
