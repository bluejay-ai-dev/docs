// Live filter for glossary.mdx. Rebinds after Mintlify SPA navigation.
(function () {
  function bind(input) {
    if (input._glossaryBound) return;
    input._glossaryBound = true;

    var countEl = document.getElementById('glossary-results-count');
    var empty = document.getElementById('glossary-empty-state');
    var items = document.querySelectorAll('[data-gl-item]');
    var groups = document.querySelectorAll('[data-gl-group]');
    if (!countEl || !empty || !items.length) return;

    function applyFilter() {
      var query = input.value.trim().toLowerCase();
      var visible = 0;

      items.forEach(function (item) {
        var term = (item.getAttribute('data-term') || '').toLowerCase();
        var match =
          !query ||
          term.split(/[\s-]+/).some(function (w) {
            return w.startsWith(query);
          }) ||
          term.startsWith(query);
        item.hidden = !match;
        if (match) visible++;
      });

      groups.forEach(function (group) {
        var shown = !!group.querySelector('[data-gl-item]:not([hidden])');
        group.hidden = !shown;
        var jump = document.querySelector('.gl-jump a[href="#' + group.id + '"]');
        if (jump) jump.setAttribute('aria-disabled', shown ? 'false' : 'true');
      });

      countEl.textContent = visible + (visible === 1 ? ' term' : ' terms');
      empty.hidden = visible > 0;
    }

    input.addEventListener('input', applyFilter);
    input.addEventListener('search', applyFilter);
    applyFilter();
  }

  function tryBind() {
    var input = document.getElementById('glossary-search');
    if (input && !input._glossaryBound) bind(input);
  }

  new MutationObserver(tryBind).observe(document.body, { childList: true, subtree: true });
  tryBind();
})();
