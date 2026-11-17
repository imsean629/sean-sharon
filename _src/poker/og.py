import asyncio, os
from playwright.async_api import async_playwright
F="/home/claude/work/fonts/node_modules/@fontsource"
L="".join(f'<link rel="stylesheet" href="file://{F}/{x}">' for x in ["jua/400.css","noto-sans-kr/700.css","noto-sans-kr/900.css"])
def card(r,s,red,rot,x,y): return f'<div style="position:absolute;left:{x}px;top:{y}px;width:120px;height:168px;border-radius:14px;background:#fff;transform:rotate({rot}deg);box-shadow:0 6px 0 rgba(0,0,0,.2);display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:Noto Sans KR;font-weight:900;color:{"#D23B4E" if red else "#2B2B3A"}"><div style="font-size:52px;line-height:1">{r}</div><div style="font-size:48px">{s}</div></div>'
cards="".join(card(*c) for c in [("A","♠",0,-14,700,190),("A","♥",1,-5,790,170),("K","♦",1,4,880,170),("K","♣",0,12,970,190),("K","♥",1,20,1055,225)])
HTML=f"""<!DOCTYPE html><html><head><meta charset="utf-8">{L}<style>*{{box-sizing:border-box}}body{{margin:0}}.p{{width:1200px;height:630px;background:linear-gradient(165deg,#3A8069,#2E6B58 55%,#23574A);position:relative;overflow:hidden;font-family:'Noto Sans KR';color:#fff;padding:80px}}
h1{{font-family:Jua;font-weight:400;font-size:100px;line-height:1.1;margin:22px 0 0}}h1 em{{font-style:normal;color:#F2CF5B}}.t{{display:inline-block;background:#fff;border-radius:99px;padding:10px 22px;font-size:26px;font-weight:700;color:#D9466B}}</style></head>
<body><div class="p">{cards}<span class="t">Sean ♥ Sharon</span><h1>오늘의<br><em>쇼다운</em></h1><p style="font-size:32px;opacity:.9;margin-top:24px;font-weight:700">하루 세 판 · 바꾸고, 걸고, 까 보자</p></div></body></html>"""
async def m():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--allow-file-access-from-files"]); pg=await b.new_page(viewport={"width":1200,"height":630})
        open("out/og.html","w").write(HTML); await pg.goto("file://"+os.path.abspath("out/og.html")); await pg.evaluate("document.fonts.ready"); await pg.screenshot(path="out/og.png"); await b.close()
asyncio.run(m())
