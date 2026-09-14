/* 手機選單鍵盤可達（2026-09-14 第一批修復）
   按鈕以 aria-expanded 驅動顯示／隱藏，CSS 用 [aria-expanded="true"] 屬性選擇器連動，
   不再依賴滑鼠/觸控限定的 checkbox+label hack。 */
(function () {
  function initNavToggle(btn) {
    var navId = btn.getAttribute('aria-controls');
    var nav = navId && document.getElementById(navId);
    if (!nav) return;
    btn.addEventListener('click', function () {
      var open = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!open));
    });
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      if (btn.getAttribute('aria-expanded') !== 'true') return;
      btn.setAttribute('aria-expanded', 'false');
      btn.focus();
    });
  }
  document.querySelectorAll('.nav-toggle-btn').forEach(initNavToggle);
})();
