// Applies the palette chosen on the home page. Shared by every sub-page.
(function () {
  var KEY = 'oeh-theme', root = document.documentElement;
  function apply(n) {
    root.setAttribute('data-theme', n);
    document.querySelectorAll('.theme-btn').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.set === n));
    });
    try { localStorage.setItem(KEY, n); } catch (e) {}
  }
  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  apply(saved || 'paper');
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.theme-btn');
    if (b) apply(b.dataset.set);
  });
})();
