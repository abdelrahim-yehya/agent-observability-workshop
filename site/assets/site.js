(function () {
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var q = $('#q');
  if (q) {
    var fTool = $('#f-tool'), fCat = $('#f-cat'), count = $('#count'), clear = $('#clear'), none = $('#none');
    var entries = $$('.metric'), main = entries.filter(function (x) { return !x.classList.contains('extra'); });
    var apply = function () {
      var text = q.value.trim().toLowerCase(), type = $('input[name="f-type"]:checked').value, tool = fTool.value, cat = fCat.value, n = 0;
      entries.forEach(function (x) {
        var ok = (!text || x.dataset.text.indexOf(text) >= 0) && (!type || x.dataset.type === type) &&
                 (!cat || x.dataset.cat === cat) && (!tool || x.dataset.tools.split('|').indexOf(tool) >= 0);
        x.hidden = !ok;
        if (ok && main.indexOf(x) >= 0) n++;
      });
      $$('.cat-group, .type-group').forEach(function (g) {
        g.hidden = !$$('.metric', g).some(function (x) { return !x.hidden; });
      });
      var filtered = !!(text || type || tool || cat);
      count.textContent = filtered ? n + ' of ' + main.length + ' metrics' : 'All ' + main.length + ' metrics';
      clear.hidden = !filtered;
      none.hidden = entries.some(function (x) { return !x.hidden; });
    };
    // Links from other pages can preset the filters: metrics.html?tool=Langfuse, ?type=Evaluation, ?cat=..., ?q=...
    var p = new URLSearchParams(location.search);
    if (p.get('q')) q.value = p.get('q');
    if (p.get('tool')) fTool.value = p.get('tool');
    if (p.get('cat')) fCat.value = p.get('cat');
    $$('input[name="f-type"]').forEach(function (r) { if (r.value && r.value === p.get('type')) r.checked = true; });
    $('#filters').addEventListener('input', apply);
    $('#filters').addEventListener('change', apply);
    $('#filters').addEventListener('submit', function (ev) { ev.preventDefault(); });
    clear.addEventListener('click', function () {
      q.value = ''; fTool.value = ''; fCat.value = ''; $('#f-type-all').checked = true; apply();
      history.replaceState(null, '', location.pathname);
    });
    apply();
  }

  // Hover text for the coverage table.
  var tip = $('#tip'), table = $('.mx');
  if (!table) return;
  function show(ev) {
    var c = ev.target.closest('[data-tip]');
    if (!c) { tip.hidden = true; return; }
    tip.textContent = c.dataset.tip;
    tip.hidden = false;
    var r = c.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
    var x = Math.max(8, Math.min(window.innerWidth - w - 8, r.left + r.width / 2 - w / 2));
    var y = r.top - h - 8 < 8 ? r.bottom + 8 : r.top - h - 8;
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  }
  table.addEventListener('mouseover', show);
  table.addEventListener('click', show);
  table.addEventListener('mouseleave', function () { tip.hidden = true; });
  window.addEventListener('scroll', function () { tip.hidden = true; }, { passive: true });
})();
