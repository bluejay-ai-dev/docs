// Gives the pager's Previous card the page title from the matching sidebar link.
// Collapsed sidebar groups are not in the DOM, so a miss reads the sidebar of the
// previous page's own HTML, where its group is open.
(function () {
  var fetched = {};

  function path(href) {
    try {
      return new URL(href, location.origin).pathname.replace(/\/+$/, '') || '/';
    } catch (e) {
      return null;
    }
  }

  function sidebarTitle(root, target) {
    var links = root.querySelectorAll('#sidebar li a[href]');
    for (var i = 0; i < links.length; i++) {
      if (path(links[i].getAttribute('href')) !== target) continue;
      var copy = links[i].cloneNode(true);
      copy.querySelectorAll('.method-nav-pill').forEach(function (pill) {
        pill.remove();
      });
      return (copy.textContent || '').replace(/\s+/g, ' ').trim();
    }
    return '';
  }

  function fetchTitle(target) {
    if (fetched[target] !== undefined) return;
    fetched[target] = '';
    fetch(target, { credentials: 'same-origin' })
      .then(function (res) {
        return res.ok ? res.text() : '';
      })
      .then(function (html) {
        if (!html) return;
        fetched[target] = sidebarTitle(new DOMParser().parseFromString(html, 'text/html'), target);
        if (fetched[target]) update();
      })
      .catch(function (err) {
        console.warn('pager-titles: could not load', target, err);
      });
  }

  function update() {
    var pager = document.querySelector('div#pagination');
    if (!pager) return;
    var prev = pager.querySelector(':scope > a:not(.w-full)');
    if (!prev) return;

    var target = path(prev.getAttribute('href'));
    if (!target) return;
    var title = sidebarTitle(document, target) || fetched[target];
    if (!title) fetchTitle(target);

    if (title) {
      if (prev.getAttribute('data-bj-title') !== title) prev.setAttribute('data-bj-title', title);
    } else if (prev.hasAttribute('data-bj-title')) {
      prev.removeAttribute('data-bj-title');
    }
  }

  new MutationObserver(update).observe(document.body, { childList: true, subtree: true });
  update();
})();
