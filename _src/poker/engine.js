// 쇼다운 포커 엔진 (앱에 그대로 삽입) — 시드 덱, 드로우, 족보, 정산
var PK = (function(){
  function hash(s){ var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function rng(seed){ return function(){ seed |= 0; seed = seed + 0x6D2B79F5 | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function deck(code, day, round){
    var d = []; for (var s = 0; s < 4; s++) for (var r = 2; r <= 14; r++) d.push({ r: r, s: s });
    var R = rng(hash(code + '|' + day + '|' + round));
    for (var i = d.length - 1; i > 0; i--) { var j = Math.floor(R() * (i + 1)); var t = d[i]; d[i] = d[j]; d[j] = t; }
    return d;
  }
  // Sean: 0~4 배분, 10~14 교체용 / Sharon: 5~9 배분, 15~19 교체용 (서로 겹치지 않음)
  function dealt(code, day, round, who){ var d = deck(code, day, round), o = who === 'Sean' ? 0 : 5; return { init: d.slice(o, o + 5), repl: d.slice(10 + o, 15 + o) }; }
  function parseDisc(s){ s = String(s == null ? '' : s).replace(/^'/, ''); if (!s) return []; return s.split(',').map(Number).filter(function(x){ return x >= 0 && x <= 4; }); }
  function final(code, day, round, who, disc){
    var h = dealt(code, day, round, who), out = h.init.slice(), k = 0, ds = parseDisc(disc).slice().sort();
    ds.forEach(function(i){ out[i] = h.repl[k++]; });
    return out;
  }
  var NAMES = ['하이카드', '원페어', '투페어', '트리플', '스트레이트', '플러시', '풀하우스', '포카드', '스트레이트 플러시'];
  function evaluate(cards){
    var cnt = {}, suits = {}, rs = [];
    cards.forEach(function(c){ cnt[c.r] = (cnt[c.r] || 0) + 1; suits[c.s] = 1; });
    var groups = Object.keys(cnt).map(Number).map(function(r){ return [cnt[r], r]; }).sort(function(a, b){ return b[0] - a[0] || b[1] - a[1]; });
    var uniq = groups.map(function(g){ return g[1]; });
    var flush = Object.keys(suits).length === 1, straight = false, high = 0;
    if (uniq.length === 5) {
      var srt = uniq.slice().sort(function(a, b){ return b - a; });
      if (srt[0] - srt[4] === 4) { straight = true; high = srt[0]; }
      else if (srt.join() === '14,5,4,3,2') { straight = true; high = 5; }
    }
    var cat, tb;
    if (straight && flush) { cat = 8; tb = [high]; }
    else if (groups[0][0] === 4) { cat = 7; tb = uniq; }
    else if (groups[0][0] === 3 && groups[1][0] === 2) { cat = 6; tb = uniq; }
    else if (flush) { cat = 5; tb = uniq.slice().sort(function(a, b){ return b - a; }); }
    else if (straight) { cat = 4; tb = [high]; }
    else if (groups[0][0] === 3) { cat = 3; tb = uniq; }
    else if (groups[0][0] === 2 && groups[1][0] === 2) { cat = 2; tb = uniq; }
    else if (groups[0][0] === 2) { cat = 1; tb = uniq; }
    else { cat = 0; tb = uniq.slice().sort(function(a, b){ return b - a; }); }
    var name = cat === 8 && high === 14 ? '로열 스트레이트 플러시' : NAMES[cat];
    return { cat: cat, score: [cat].concat(tb), name: name };
  }
  function cmp(a, b){ for (var i = 0; i < Math.max(a.length, b.length); i++) { var x = a[i] || 0, y = b[i] || 0; if (x !== y) return x > y ? 1 : -1; } return 0; }
  // 정산: 참가비 1칩씩. 폴드 = 참가비만 잃음. 둘 다 콜 → 이긴 사람이 (참가비 + 둘 중 작은 베팅)만큼 가져감
  function settle(a, b){ // a, b: {bet, ev}
    if (!a.bet && !b.bet) return { d: 0, how: '둘 다 폴드' };
    if (!a.bet) return { d: -1, how: 'fold-a' };
    if (!b.bet) return { d: 1, how: 'fold-b' };
    var c = cmp(a.ev.score, b.ev.score), amt = 1 + Math.min(a.bet, b.bet);
    return { d: c * amt, how: c ? 'show' : 'tie', amt: amt };
  }
  return { hash: hash, deck: deck, dealt: dealt, final: final, parseDisc: parseDisc, evaluate: evaluate, cmp: cmp, settle: settle };
})();
if (typeof module !== 'undefined') module.exports = PK;
