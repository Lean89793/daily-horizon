"""网页版学习包的阅读追踪脚本。

只注入到归档网页（docs/packs/*.html），不注入邮件——邮件客户端会剥掉 script。
功能：真实阅读计时（可见 + 有操作才算）、滚动位置记忆、右下角已读悬浮条。
"""

from __future__ import annotations

import json

_JS = r"""
(function () {
  var ID = __PACK_ID__;
  var K = { t: 'dh_t_' + ID, s: 'dh_s_' + ID };

  function read(k) { var v = parseInt(localStorage.getItem(k) || '0', 10); return isNaN(v) ? 0 : v; }
  function write(k, v) { try { localStorage.setItem(k, String(v)); } catch (e) {} }

  var total = read(K.t);
  var sessionBase = total;
  var reported = 0;
  var lastAct = Date.now();

  function markAct() { lastAct = Date.now(); }
  ['scroll', 'mousemove', 'keydown', 'touchstart', 'click', 'wheel'].forEach(function (ev) {
    window.addEventListener(ev, markAct, { passive: true });
  });

  function active() {
    return document.visibilityState === 'visible' && (Date.now() - lastAct) < 90000;
  }

  var hud = document.createElement('div');
  hud.style.cssText =
    'position:fixed;right:18px;bottom:18px;z-index:99999;padding:9px 13px;border-radius:12px;' +
    'background:rgba(22,22,26,.88);color:#fff;font:12.5px/1.35 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;' +
    'box-shadow:0 8px 24px rgba(0,0,0,.28);letter-spacing:.02em;user-select:none;';
  function fmt(s) {
    var m = Math.floor(s / 60), x = Math.floor(s % 60);
    return m + ':' + (x < 10 ? '0' : '') + x;
  }
  function render() {
    hud.textContent = '本次 ' + fmt(total - sessionBase) + ' · 累计 ' + fmt(total);
  }

  function flush() {
    var d = total - reported;
    if (d > 0 && window.dhBridge && window.dhBridge.report) {
      window.dhBridge.report(ID, d);
      reported = total;
    }
  }

  setInterval(function () {
    if (!active()) return;
    total += 5;
    write(K.t, total);
    if (total - reported >= 60) flush();
    render();
  }, 5000);

  var saveScroll = function () { write(K.s, Math.round(window.scrollY || window.pageYOffset || 0)); };
  var scrollTimer = null;
  window.addEventListener('scroll', function () {
    if (scrollTimer) return;
    scrollTimer = setTimeout(function () { scrollTimer = null; saveScroll(); }, 700);
  }, { passive: true });

  var saved = read(K.s);
  if (saved > 240) {
    window.addEventListener('load', function () {
      setTimeout(function () { window.scrollTo(0, saved); }, 140);
    });
  }

  if (document.body) document.body.appendChild(hud); else window.addEventListener('DOMContentLoaded', function () { document.body.appendChild(hud); });
  render();

  window.addEventListener('pagehide', function () { saveScroll(); flush(); });
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'hidden') { saveScroll(); flush(); } });
})();
"""


def script(pack_id: str) -> str:
    """返回注入网页的脚本标签。"""
    return "<script>" + _JS.replace("__PACK_ID__", json.dumps(pack_id)) + "</script>"
