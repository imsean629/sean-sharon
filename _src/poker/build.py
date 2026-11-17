"""쇼다운 포커 빌드: engine.js + template.html → out/index.html, out/index_mock.html"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__))
URL = "https://imsean629.github.io/sean-sharon/poker/"
SHEET = sys.argv[1] if len(sys.argv) > 1 else "https://script.google.com/macros/s/AKfycbzltb6Q5-GcsaCb3hSEgw5hcKCVM-_ZSkF-amQV4ZZxCxOp7qn8P6FomEzV5KfQ2H6kog/exec"
os.makedirs(f"{H}/out", exist_ok=True)
h2c = open(f"{H}/../vendor/html2canvas.min.js").read().replace("</script", "<\\/script")
eng = open(f"{H}/engine.js").read()
s = open(f"{H}/template.html").read().replace("/*__H2C__*/", h2c).replace("/*__ENGINE__*/", eng).replace("__URL__", URL)
assert "/*__" not in s and "__URL__" not in s
open(f"{H}/out/index.html", "w").write(s.replace('SHEET_URL: ""', f'SHEET_URL: "{SHEET}"'))
F = "/home/claude/work/fonts/node_modules/@fontsource"
loc = "".join(f'<link rel="stylesheet" href="file://{F}/{x}">' for x in ["jua/400.css", "noto-sans-kr/400.css", "noto-sans-kr/700.css", "noto-sans-kr/900.css"])
open(f"{H}/out/index_mock.html", "w").write(s.replace('SHEET_URL: ""', 'SHEET_URL: "https://mock.sheet.test/exec"').replace("</head>", loc + "</head>"))
print("built", os.path.getsize(f"{H}/out/index.html") // 1024, "KB")
