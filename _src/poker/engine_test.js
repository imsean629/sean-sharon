const PK = require('./engine.js'); let ok = true; const chk = (c, m) => { ok = ok && c; console.log((c ? 'OK  ' : 'FAIL') + ' ' + m); };
const C = s => s.split(' ').map(t => ({ r: '23456789TJQKA'.indexOf(t[0]) + 2, s: 'shdc'.indexOf(t[1]) }));
const E = s => PK.evaluate(C(s));
const cases = [['As Ks Qs Js Ts', '로열 스트레이트 플러시'], ['9h 8h 7h 6h 5h', '스트레이트 플러시'], ['Ah 2h 3h 4h 5h', '스트레이트 플러시'], ['9s 9h 9d 9c 2s', '포카드'], ['3s 3h 3d 2c 2s', '풀하우스'],
  ['Ah 9h 7h 4h 2h', '플러시'], ['As 2d 3c 4h 5s', '스트레이트'], ['Ts Jd Qc Kh As', '스트레이트'], ['7s 7h 7d Kc 2s', '트리플'], ['7s 7h Kd Kc 2s', '투페어'], ['7s 7h Kd Qc 2s', '원페어'], ['As Kh 9d 5c 2s', '하이카드'], ['Qs Kh Ad 2c 3s', '하이카드']];
cases.forEach(([h, n]) => chk(E(h).name === n, h + ' → ' + E(h).name));
const gt = (a, b, m) => chk(PK.cmp(E(a).score, E(b).score) === 1, m);
gt('6s 5h 4d 3c 2s', 'As 2d 3c 4h 5s', '6-하이 스트레이트 > 휠(5-하이)');
gt('Ks Kh 3d 3c 2s', 'Qs Qh Jd Jc As', 'KK33 > QQJJ');
gt('8s 8h Ad 4c 2s', '8d 8c Kd Qc Js', '같은 원페어면 키커 A');
gt('2s 2h 2d Ac Ks', 'As Kh Qd Jc 9s', '트리플 > 하이카드');
gt('Ac Qc 9c 4c 3c', 'Ah Qh 9h 4h 2h', '플러시끼리는 마지막 키커까지 비교 (3 > 2)');
chk(PK.cmp(E('Ah Kh 9h 4h 2h').score, E('Ad Kd 9d 4d 2d').score) === 0, '완전 동률');
// 덱: 같은 시드 = 같은 덱, 20장 서로 겹치지 않음
const a = PK.dealt('0429', '2026-11-17', 1, 'Sean'), b = PK.dealt('0429', '2026-11-17', 1, 'Sharon');
const all = [...a.init, ...a.repl, ...b.init, ...b.repl].map(c => c.r + '-' + c.s);
chk(new Set(all).size === 20, '두 사람 배분·교체 카드 20장 중복 없음');
chk(JSON.stringify(PK.dealt('0429', '2026-11-17', 1, 'Sean')) === JSON.stringify(a), '같은 날·판은 같은 카드');
chk(JSON.stringify(PK.dealt('0429', '2026-11-17', 2, 'Sean')) !== JSON.stringify(a), '판이 바뀌면 다른 카드');
const f = PK.final('0429', '2026-11-17', 1, 'Sean', '3,0');
chk(f[0].r === a.repl[0].r && f[0].s === a.repl[0].s && f[3].s === a.repl[1].s && f[3].r === a.repl[1].r && f[1].r === a.init[1].r && f[1].s === a.init[1].s, '교체: 앞 카드부터 교체용 카드로');
// 정산
const ev = s => ({ ev: E(s) });
chk(PK.settle({ bet: 0 }, { bet: 5 }).d === -1, 'A 폴드 → A -1');
chk(PK.settle({ bet: 10, ...ev('As Ah 2d 3c 4s') }, { bet: 2, ...ev('Ks Qh 2h 3h 5s') }).d === 3, '이기면 1 + 작은 베팅(2) = 3');
chk(PK.settle({ bet: 5, ...ev('Ks Qh 2h 3h 5s') }, { bet: 10, ...ev('As Ah 2d 3c 4s') }).d === -6, '지면 -(1+5)');
chk(PK.settle({ bet: 0 }, { bet: 0 }).d === 0, '둘 다 폴드 0');
// 분포 확인 (드로우 없이 1만 판)
const freq = {}; for (let i = 0; i < 10000; i++) { const h = PK.dealt('0429', 'd' + i, 1, 'Sean').init; const n = PK.evaluate(h).name; freq[n] = (freq[n] || 0) + 1; }
chk(freq['원페어'] > 4000 && freq['원페어'] < 4500 && freq['하이카드'] > 4800, '족보 분포 정상 ' + JSON.stringify(freq));
console.log(ok ? 'ALL OK' : 'SOME FAILED');
