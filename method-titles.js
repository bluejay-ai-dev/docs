// Endpoint titles ("POST /v1/…"): style.css draws the method pill and path from these attributes.
// The text node stays untouched, so React can still update it on client-side navigation.
(function () {
  var TITLE = /^(GET|POST|PUT|PATCH|DELETE)\s+(\/\S*)$/;

  function set(el, name, value) {
    if (value === null) {
      if (el.hasAttribute(name)) el.removeAttribute(name);
    } else if (el.getAttribute(name) !== value) {
      el.setAttribute(name, value);
    }
  }

  function update() {
    var title = document.getElementById('page-title');
    if (!title) return;
    var m = TITLE.exec((title.textContent || '').trim());
    set(title, 'data-bj-method', m ? m[1] : null);
    set(title, 'data-bj-path', m ? m[2] : null);
  }

  new MutationObserver(update).observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true,
  });
  update();
})();
