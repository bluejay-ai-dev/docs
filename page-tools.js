(function () {
  var TOOLBAR_ID = 'bluejay-page-tools';
  var TOAST_ID = 'bluejay-toast';

  var icons = {
    copy: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',
    check: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    chevron: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>',
    markdown: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3v4a1 1 0 001 1h4"/><path d="M17 21H7a2 2 0 01-2-2V5a2 2 0 012-2h7l5 5v11a2 2 0 01-2 2z"/><path d="M9 17v-6l3 3 3-3v6"/></svg>',
    chatgpt: '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M22.282 9.821a5.985 5.985 0 00-.516-4.91 6.046 6.046 0 00-6.51-2.9A6.065 6.065 0 004.981 4.18a5.985 5.985 0 00-3.998 2.9 6.046 6.046 0 00.743 7.097 5.98 5.98 0 00.51 4.911 6.051 6.051 0 006.515 2.9A5.985 5.985 0 0013.26 24a6.056 6.056 0 005.772-4.206 5.99 5.99 0 003.997-2.9 6.056 6.056 0 00-.747-7.073zM13.26 22.43a4.476 4.476 0 01-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 00.392-.681v-6.737l2.02 1.168a.071.071 0 01.038.052v5.583a4.504 4.504 0 01-4.494 4.494zM3.6 18.304a4.47 4.47 0 01-.535-3.014l.142.085 4.783 2.759a.771.771 0 00.78 0l5.843-3.369v2.332a.08.08 0 01-.033.062L9.74 19.95a4.5 4.5 0 01-6.14-1.646zM2.34 7.896a4.485 4.485 0 012.366-1.973V11.6a.766.766 0 00.388.676l5.815 3.355-2.02 1.168a.076.076 0 01-.071 0l-4.83-2.786A4.504 4.504 0 012.34 7.872zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 01.071 0l4.83 2.791a4.494 4.494 0 01-.676 8.105v-5.678a.79.79 0 00-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 00-.785 0L9.409 9.23V6.897a.066.066 0 01.028-.061l4.83-2.787a4.5 4.5 0 016.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 01-.038-.057V6.075a4.5 4.5 0 017.375-3.453l-.142.08L8.704 5.46a.795.795 0 00-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z"/></svg>',
    claude: '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1L14.5 9.5L23 12L14.5 14.5L12 23L9.5 14.5L1 12L9.5 9.5Z"/></svg>'
  };

  function getContentEl() {
    return document.querySelector('.mdx-content') ||
      document.getElementById('content-area') ||
      document.getElementById('body-content') ||
      document.querySelector('article') ||
      document.querySelector('main');
  }

  function getAnchorEl() {
    return document.getElementById('content-area') ||
      document.getElementById('header') ||
      document.querySelector('.mdx-content') ||
      document.querySelector('article');
  }

  function htmlToMd(node) {
    if (!node) return '';
    if (node.nodeType === Node.TEXT_NODE) return node.textContent || '';
    if (node.nodeType !== Node.ELEMENT_NODE) return '';

    var tag = node.tagName.toLowerCase();
    var skip = ['script', 'style', 'svg', 'noscript', 'iframe', 'button', 'input', 'select', 'textarea'];
    if (skip.indexOf(tag) !== -1) return '';
    if (node.id === TOOLBAR_ID || node.id === TOAST_ID) return '';
    if (node.hidden || (node.style && node.style.display === 'none')) return '';

    var children = Array.from(node.childNodes).map(htmlToMd).join('');

    switch (tag) {
      case 'h1': return '\n# ' + children.trim() + '\n\n';
      case 'h2': return '\n## ' + children.trim() + '\n\n';
      case 'h3': return '\n### ' + children.trim() + '\n\n';
      case 'h4': return '\n#### ' + children.trim() + '\n\n';
      case 'h5': return '\n##### ' + children.trim() + '\n\n';
      case 'h6': return '\n###### ' + children.trim() + '\n\n';
      case 'p': return '\n' + children.trim() + '\n\n';
      case 'br': return '\n';
      case 'strong': case 'b': return '**' + children.trim() + '**';
      case 'em': case 'i': return '*' + children.trim() + '*';
      case 'code':
        if (node.parentElement && node.parentElement.tagName.toLowerCase() === 'pre') return children;
        return '`' + children.trim() + '`';
      case 'pre':
        var lang = '';
        var codeEl = node.querySelector('code');
        if (codeEl) {
          var m = (codeEl.className || '').match(/language-(\w+)/);
          if (m) lang = m[1];
        }
        return '\n```' + lang + '\n' + (codeEl ? codeEl.textContent : node.textContent).trim() + '\n```\n\n';
      case 'a':
        var href = node.getAttribute('href') || '';
        if (href.startsWith('/')) href = window.location.origin + href;
        return '[' + children.trim() + '](' + href + ')';
      case 'img':
        return '![' + (node.getAttribute('alt') || '') + '](' + (node.getAttribute('src') || '') + ')';
      case 'ul': return '\n' + children + '\n';
      case 'ol': return '\n' + children + '\n';
      case 'li':
        var parent = node.parentElement;
        var prefix = '- ';
        if (parent && parent.tagName.toLowerCase() === 'ol') {
          prefix = (Array.from(parent.children).indexOf(node) + 1) + '. ';
        }
        return prefix + children.trim() + '\n';
      case 'blockquote':
        return '\n' + children.trim().split('\n').map(function (l) { return '> ' + l; }).join('\n') + '\n\n';
      case 'table': return '\n' + tableToMd(node) + '\n\n';
      case 'thead': case 'tbody': case 'tfoot': case 'tr': case 'th': case 'td': return children;
      case 'hr': return '\n---\n\n';
      default: return children;
    }
  }

  function tableToMd(table) {
    var rows = Array.from(table.querySelectorAll('tr'));
    if (!rows.length) return '';
    var lines = [];
    rows.forEach(function (row, i) {
      var cells = Array.from(row.querySelectorAll('th, td'));
      lines.push('| ' + cells.map(function (c) { return c.textContent.trim(); }).join(' | ') + ' |');
      if (i === 0) lines.push('| ' + cells.map(function () { return '---'; }).join(' | ') + ' |');
    });
    return lines.join('\n');
  }

  function getPageMarkdown() {
    var content = getContentEl();
    if (!content) return document.body.innerText;
    var md = htmlToMd(content);
    return md.replace(/\n{3,}/g, '\n\n').trim();
  }

  function buildPrompt() {
    return "I'm building with Bluejay, the testing, monitoring, and improvement platform for conversational AI agents - can you read this docs page " + window.location.href + " so I can ask you questions about it?";
  }

  // -- toast --

  function showToast(msg) {
    var t = document.getElementById(TOAST_ID);
    if (t) t.remove();
    t = document.createElement('div');
    t.id = TOAST_ID;
    t.textContent = msg;
    document.body.appendChild(t);
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { t.classList.add('show'); });
    });
    setTimeout(function () {
      t.classList.remove('show');
      setTimeout(function () { if (t.parentNode) t.remove(); }, 300);
    }, 2000);
  }

  // -- actions --

  function copyPage() {
    var md = getPageMarkdown();
    var mainBtn = document.querySelector('.bj-main-btn');

    function onSuccess() {
      if (!mainBtn) return;
      var iconSpan = mainBtn.querySelector('.bj-btn-icon');
      var labelSpan = mainBtn.querySelector('.bj-btn-label');
      if (iconSpan) iconSpan.innerHTML = icons.check;
      if (labelSpan) labelSpan.textContent = 'Copied!';
      setTimeout(function () {
        if (iconSpan) iconSpan.innerHTML = icons.copy;
        if (labelSpan) labelSpan.textContent = 'Copy page';
      }, 2000);
    }

    navigator.clipboard.writeText(md).then(onSuccess).catch(function () {
      var ta = document.createElement('textarea');
      ta.value = md;
      ta.style.cssText = 'position:fixed;opacity:0;left:-9999px';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      onSuccess();
    });
  }

  function viewAsMarkdown() {
    var md = getPageMarkdown();
    var title = document.title || 'Page';
    var escaped = md.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    var page = [
      '<!DOCTYPE html><html><head><meta charset="utf-8">',
      '<title>' + title + ' — Markdown</title>',
      '<style>',
      '*{box-sizing:border-box}',
      'body{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;max-width:900px;margin:40px auto;padding:0 24px;line-height:1.7;color:#24292f;background:#fff}',
      '@media(prefers-color-scheme:dark){body{color:#e6edf3;background:#0d1117}}',
      '.bar{display:flex;gap:8px;align-items:center;margin-bottom:16px;padding-bottom:16px;border-bottom:1px solid #d0d7de}',
      '@media(prefers-color-scheme:dark){.bar{border-color:#30363d}}',
      '.bar h1{margin:0;font-size:16px;font-weight:600;flex:1}',
      'button{font-family:inherit;padding:6px 16px;border:1px solid #d0d7de;border-radius:6px;background:#f6f8fa;cursor:pointer;font-size:13px;font-weight:500;color:#24292f}',
      '@media(prefers-color-scheme:dark){button{background:#21262d;border-color:#30363d;color:#e6edf3}}',
      'button:hover{background:#eaeef2}@media(prefers-color-scheme:dark){button:hover{background:#30363d}}',
      'pre{white-space:pre-wrap;word-wrap:break-word;tab-size:2;font-size:14px;line-height:1.6;padding:16px;background:#f6f8fa;border-radius:8px;border:1px solid #d0d7de}',
      '@media(prefers-color-scheme:dark){pre{background:#161b22;border-color:#30363d}}',
      '</style></head><body>',
      '<div class="bar"><h1>' + title + '</h1>',
      "<button onclick=\"navigator.clipboard.writeText(document.getElementById('md').textContent).then(function(){this.textContent='Copied!'}.bind(this))\">Copy markdown</button></div>",
      '<pre id="md">' + escaped + '</pre>',
      '</body></html>'
    ].join('');
    var blob = new Blob([page], { type: 'text/html;charset=utf-8' });
    window.open(URL.createObjectURL(blob), '_blank');
  }

  function openInChatGPT() {
    var prompt = buildPrompt();
    navigator.clipboard.writeText(prompt).catch(function () {});
    window.open('https://chatgpt.com/?q=' + encodeURIComponent(prompt), '_blank');
  }

  function openInClaude() {
    var prompt = buildPrompt();
    navigator.clipboard.writeText(prompt).catch(function () {});
    window.open('https://claude.ai/new?q=' + encodeURIComponent(prompt), '_blank');
  }

  // -- dropdown --

  function closeDropdown() {
    var dd = document.querySelector('.bj-dropdown');
    if (dd) dd.classList.remove('open');
  }

  function toggleDropdown() {
    var dd = document.querySelector('.bj-dropdown');
    if (dd) dd.classList.toggle('open');
  }

  document.addEventListener('click', function (e) {
    if (!e.target.closest('#' + TOOLBAR_ID)) closeDropdown();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeDropdown();
  });

  // -- toolbar --

  function createToolbar() {
    if (document.getElementById(TOOLBAR_ID)) return;

    var anchor = getAnchorEl();
    if (!anchor) return;

    var wrapper = document.createElement('div');
    wrapper.id = TOOLBAR_ID;

    var splitBtn = document.createElement('div');
    splitBtn.className = 'bj-split-btn';

    var mainBtn = document.createElement('button');
    mainBtn.className = 'bj-main-btn';
    mainBtn.setAttribute('aria-label', 'Copy page');
    mainBtn.innerHTML =
      '<span class="bj-btn-icon">' + icons.copy + '</span>' +
      '<span class="bj-btn-label">Copy page</span>';
    mainBtn.addEventListener('click', copyPage);

    var divider = document.createElement('span');
    divider.className = 'bj-split-divider';

    var chevronBtn = document.createElement('button');
    chevronBtn.className = 'bj-chevron-btn';
    chevronBtn.setAttribute('aria-label', 'More actions');
    chevronBtn.innerHTML = icons.chevron;
    chevronBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      toggleDropdown();
    });

    splitBtn.appendChild(mainBtn);
    splitBtn.appendChild(divider);
    splitBtn.appendChild(chevronBtn);

    var dropdown = document.createElement('div');
    dropdown.className = 'bj-dropdown';

    var items = [
      { label: 'View as Markdown', icon: icons.markdown, fn: viewAsMarkdown },
      { label: 'Open in ChatGPT', icon: icons.chatgpt, fn: openInChatGPT },
      { label: 'Open in Claude', icon: icons.claude, fn: openInClaude }
    ];

    items.forEach(function (item) {
      var btn = document.createElement('button');
      btn.className = 'bj-dropdown-item';
      btn.innerHTML =
        '<span class="bj-item-icon">' + item.icon + '</span>' +
        '<span>' + item.label + '</span>';
      btn.addEventListener('click', function () {
        item.fn();
        closeDropdown();
      });
      dropdown.appendChild(btn);
    });

    wrapper.appendChild(splitBtn);
    wrapper.appendChild(dropdown);

    anchor.style.position = 'relative';
    anchor.insertBefore(wrapper, anchor.firstChild);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createToolbar);
  } else {
    createToolbar();
  }

  new MutationObserver(function () {
    if (!document.getElementById(TOOLBAR_ID)) createToolbar();
  }).observe(document.body, { childList: true, subtree: true });
})();
