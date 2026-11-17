import asyncio, os
from playwright.async_api import async_playwright
F="/home/claude/work/fonts/node_modules/@fontsource"
L="".join(f'<link rel="stylesheet" href="file://{F}/{x}">' for x in ["jua/400.css","noto-sans-kr/700.css","noto-sans-kr/900.css"])
def chip(c,t,x,y,rot,fg):
    return f'<div style="position:absolute;left:{x}px;top:{y}px;width:150px;height:150px;border-radius:50%;transform:rotate({rot}deg);background:radial-gradient(circle,{c} 0 46%,transparent 47%),repeating-conic-gradient({c} 0 20deg,#fff 20deg 40deg);box-shadow:0 0 0 8px {c},0 10px 0 rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center;font:900 40px Noto Sans KR;color:{fg}">{t}</div>'
chips=chip("#2B2B33","500",760,120,-12,"#F2CF5B")+chip("#3B7DD8","100",930,200,8,"#fff")+chip("#E0475E","50",800,330,20,"#fff")+chip("#F4F1EA","10",980,380,-6,"#3B3551")
HTML=f"""<!DOCTYPE html><html><head><meta charset="utf-8">{L}<style>*{{box-sizing:border-box}}body{{margin:0}}.p{{width:1200px;height:630px;background:radial-gradient(ellipse at 40% 45%,#3A8069,#2E6B58 55%,#1F4D40);position:relative;overflow:hidden;font-family:'Noto Sans KR';color:#fff;padding:80px}}
h1{{font-family:Jua;font-weight:400;font-size:104px;line-height:1.1;margin:22px 0 0}}h1 em{{font-style:normal;color:#F2CF5B}}.t{{display:inline-block;background:#fff;border-radius:99px;padding:10px 22px;font-size:26px;font-weight:700;color:#D9466B}}</style></head>
<body><div class="p">{chips}<span class="t">Sean ♥ Sharon</span><h1>칩<br><em>테이블</em></h1><p style="font-size:32px;opacity:.9;margin-top:24px;font-weight:700">카드는 실물로, 칩은 휴대폰으로 ⬆</p></div></body></html>"""
async def m():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--allow-file-access-from-files"]); pg=await b.new_page(viewport={"width":1200,"height":630})
        open("out/og.html","w").write(HTML); await pg.goto("file://"+os.path.abspath("out/og.html")); await pg.evaluate("document.fonts.ready"); await pg.screenshot(path="out/og.png"); await b.close()
asyncio.run(m())
