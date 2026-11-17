import asyncio
from playwright.async_api import async_playwright
F="/home/claude/work/fonts/node_modules/@fontsource"
L="".join(f'<link rel="stylesheet" href="file://{F}/{x}">' for x in ["jua/400.css","noto-sans-kr/700.css"])
HTML=f"""<!DOCTYPE html><html><head><meta charset="utf-8">{L}<style>*{{box-sizing:border-box}}body{{margin:0}}.p{{width:1200px;height:630px;background:#FFF7F2;position:relative;overflow:hidden;font-family:'Noto Sans KR';color:#3B3551;padding:80px}}
h1{{font-family:Jua;font-weight:400;font-size:96px;line-height:1.1;margin:22px 0 0}}h1 em{{font-style:normal;color:#D9466B}}.t{{display:inline-block;background:#fff;border-radius:99px;padding:10px 22px;font-size:26px;font-weight:700;color:#D9466B}}
.c{{position:absolute;right:80px;width:330px;height:150px;border-radius:28px;font-family:Jua;font-size:40px;display:flex;align-items:center;padding:0 30px}}
.v{{position:absolute;right:205px;top:262px;width:80px;height:80px;border-radius:50%;background:#fff;font-family:Jua;font-size:32px;display:flex;align-items:center;justify-content:center;box-shadow:0 6px 16px rgba(0,0,0,.08)}}</style></head>
<body><div class="p"><div class="c" style="top:120px;background:#FFE3EA;border:4px solid #D9466B">A. 바다</div><div class="c" style="top:300px;background:#EAF4FF">B. 산</div><div class="v">VS</div>
<span class="t">Sean ♥ Sharon</span><h1>오늘의<br><em>밸런스</em> 게임</h1><p style="font-size:32px;color:#7A7290;margin-top:24px">하루 한 문제, 같은 걸 골랐을까?</p></div></body></html>"""
async def m():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--allow-file-access-from-files"]); pg=await b.new_page(viewport={"width":1200,"height":630})
        open("out/og.html","w").write(HTML); import os; await pg.goto("file://"+os.path.abspath("out/og.html")); await pg.evaluate("document.fonts.ready"); await pg.screenshot(path="out/og.png"); await b.close()
asyncio.run(m())
