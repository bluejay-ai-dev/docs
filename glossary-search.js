// reactive glossary search — survives Mintlify's SPA navigation
(function () {
  function bind(input) {
    if (input._glossaryBound) return;
    input._glossaryBound = true;

    var countEl = document.getElementById('glossary-results-count');
    var empty = document.getElementById('glossary-empty-state');
    var items = document.querySelectorAll('[data-glossary-item]');
    var sections = document.querySelectorAll('[data-glossary-section]');
    if (!countEl || !empty || !items.length) return;

    function applyFilter() {
      var query = input.value.trim().toLowerCase();
      var visible = 0;

      items.forEach(function (item) {
        var term = (item.getAttribute('data-term') || '').toLowerCase();
        var words = term.split(/\s+/);
        var match =
          !query ||
          term.startsWith(query) ||
          words.some(function (w) {
            return w.startsWith(query);
          });
        item.style.display = match ? '' : 'none';
        if (match) visible++;
      });

      sections.forEach(function (section) {
        var hasVisible = Array.from(
          section.querySelectorAll('[data-glossary-item]')
        ).some(function (i) {
          return i.style.display !== 'none';
        });
        section.style.display = hasVisible ? '' : 'none';
      });

      countEl.textContent = String(visible);
      empty.classList.toggle('hidden', visible > 0);
    }

    input.addEventListener('input', applyFilter);
    input.addEventListener('search', applyFilter);
    applyFilter();
  }

  var observer = new MutationObserver(function () {
    var input = document.getElementById('glossary-search');
    if (input && !input._glossaryBound) bind(input);
  });

  observer.observe(document.body, { childList: true, subtree: true });

  var input = document.getElementById('glossary-search');
  if (input) bind(input);
})();
