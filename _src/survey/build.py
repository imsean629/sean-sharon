"""학원생 설문 빌드: data.py + template.html → out/index.html (실제), out/index_mock.html (테스트용 가짜 시트)
사용: python3 build.py [SHEET_URL]   (생략하면 아래 SHEET 값, 비어 있으면 미리보기 모드)"""
import base64, json, os, sys, segno
from data import LEVELS, QS, TITLES, BOARD

H = os.path.dirname(os.path.abspath(__file__))
URL = "https://imsean629.github.io/sean-sharon/survey/"
SHEET = sys.argv[1] if len(sys.argv) > 1 else "https://script.google.com/macros/s/AKfycbzltb6Q5-GcsaCb3hSEgw5hcKCVM-_ZSkF-amQV4ZZxCxOp7qn8P6FomEzV5KfQ2H6kog/exec"
DARK = "#3B3551"

os.makedirs(f"{H}/out", exist_ok=True)
q = segno.make(URL, error="q")
q.save(f"{H}/out/qr.png", scale=20, border=2, dark=DARK)
q.save(f"{H}/out/qr.svg", scale=10, border=2, dark=DARK)
b64 = lambda p, m: f"data:{m};base64," + base64.b64encode(open(p, "rb").read()).decode()
h2c = open(f"{H}/../vendor/html2canvas.min.js").read().replace("</script", "<\\/script")
J = lambda o: json.dumps(o, ensure_ascii=False)

s = open(f"{H}/template.html").read()
for k, v in {"LEVELS": LEVELS, "QS": QS, "TITLES": TITLES, "BOARD": BOARD}.items():
    s = s.replace(f"/*__{k}__*/null", J(v))
s = s.replace("/*__H2C__*/", h2c).replace("__QR__", b64(f"{H}/out/qr.png", "image/png")).replace("__URL__", URL)
assert "/*__" not in s and "__QR__" not in s
real = s.replace('SHEET_URL: ""', f'SHEET_URL: "{SHEET}"') if SHEET else s
open(f"{H}/out/index.html", "w").write(real)

F = "/home/claude/work/fonts/node_modules/@fontsource"
loc = "".join(f'<link rel="stylesheet" href="file://{F}/{x}">' for x in ["jua/400.css", "noto-sans-kr/400.css", "noto-sans-kr/700.css", "noto-sans-kr/900.css"])
mock = s.replace('SHEET_URL: ""', 'SHEET_URL: "https://mock.sheet.test/exec"').replace("</head>", loc + "</head>")
open(f"{H}/out/index_mock.html", "w").write(mock)
print("built", os.path.getsize(f"{H}/out/index.html") // 1024, "KB", "| sheet:", SHEET or "(미연결)")
