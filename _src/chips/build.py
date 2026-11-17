"""칩 테이블 빌드: template.html + peerjs + QR → out/index.html"""
import base64, os, segno
H = os.path.dirname(os.path.abspath(__file__))
URL = "https://imsean629.github.io/sean-sharon/chips/"
os.makedirs(f"{H}/out", exist_ok=True)
segno.make(URL, error="q").save(f"{H}/out/qr.png", scale=8, border=2, dark="#1F4D40")
qr = "data:image/png;base64," + base64.b64encode(open(f"{H}/out/qr.png", "rb").read()).decode()
peer = open(f"{H}/node/node_modules/peerjs/dist/peerjs.min.js").read().replace("</script", "<\\/script")
peer = peer.split("//# sourceMappingURL")[0]
s = open(f"{H}/template.html").read().replace("/*__PEER__*/", "/*! PeerJS 1.5.5 (MIT) */\n" + peer).replace("__QR__", qr).replace("__URL__", URL)
assert "/*__" not in s and "__URL__" not in s
open(f"{H}/out/index.html", "w").write(s)
F = "/home/claude/work/fonts/node_modules/@fontsource"
loc = "".join(f'<link rel="stylesheet" href="fonts/{x}">' for x in ["jua/400.css", "noto-sans-kr/400.css", "noto-sans-kr/700.css", "noto-sans-kr/900.css"])
open(f"{H}/out/index_mock.html", "w").write(s.replace("</head>", loc + "</head>"))
print("built", os.path.getsize(f"{H}/out/index.html") // 1024, "KB")
