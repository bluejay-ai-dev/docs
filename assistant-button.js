// Bluejay AI launcher: clicks Mintlify's hidden assistant entry, which toggles the assistant panel.
(function () {
  function add() {
    if (document.getElementById('bj-assistant-button')) return;
    var button = document.createElement('button');
    button.id = 'bj-assistant-button';
    button.type = 'button';
    button.title = 'Bluejay AI';
    button.setAttribute('aria-label', 'Open Bluejay AI');
    button.appendChild(document.createElement('span'));
    button.addEventListener('click', function () {
      var entry = document.querySelector('[data-layout-item="assistant-entry"]');
      if (entry) entry.click();
      else console.warn('assistant-button: no assistant entry on this page');
    });
    document.body.appendChild(button);
  }

  new MutationObserver(add).observe(document.body, { childList: true });
  add();
})();
