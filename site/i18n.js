/**
 * NaviTools i18n — language switcher
 *
 * Supported languages: en (default), es, fr
 *
 * HTML conventions:
 *   data-i18n="key"           → sets element.textContent
 *   data-i18n-html="key"      → sets element.innerHTML  (use for content with <b>, <em>, etc.)
 *   data-i18n-ph="key"        → sets element.placeholder (for inputs / textareas)
 *   data-i18n-opt="key"       → sets element.textContent for <option> elements
 *
 * To add a new language: add its JSON file to lang/<code>.json and a button in the switcher.
 * To add new content:    add data-i18n="new.key" to HTML, add the string to lang/en.json,
 *                        then run: python3 translate.py
 */

(function () {
  var SUPPORTED = ['en', 'es', 'fr'];
  var DEFAULT = 'en';
  var CACHE = {};

  function getLang() {
    try {
      return localStorage.getItem('nt-lang') || DEFAULT;
    } catch (e) {
      return DEFAULT;
    }
  }

  function setLang(lang) {
    if (SUPPORTED.indexOf(lang) === -1) return;
    try { localStorage.setItem('nt-lang', lang); } catch (e) {}
    loadAndApply(lang);
  }

  function loadAndApply(lang) {
    if (CACHE[lang]) {
      apply(lang, CACHE[lang]);
      return;
    }
    // Cache-bust with a version string to avoid stale translations after updates.
    // Update this version number after running translate.py with significant changes.
    var v = '10';
    fetch('lang/' + lang + '.json?v=' + v)
      .then(function (r) { return r.json(); })
      .then(function (t) {
        CACHE[lang] = t;
        apply(lang, t);
      })
      .catch(function (e) {
        console.warn('NaviTools i18n: could not load', lang, e);
      });
  }

  function apply(lang, t) {
    // Plain text
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var v = t[el.dataset.i18n];
      if (v !== undefined) el.textContent = v;
    });

    // Rich HTML (contains <b>, <em>, etc.)
    document.querySelectorAll('[data-i18n-html]').forEach(function (el) {
      var v = t[el.dataset.i18nHtml];
      if (v !== undefined) el.innerHTML = v;
    });

    // Input / textarea placeholders
    document.querySelectorAll('[data-i18n-ph]').forEach(function (el) {
      var v = t[el.dataset.i18nPh];
      if (v !== undefined) el.placeholder = v;
    });

    // <option> text
    document.querySelectorAll('[data-i18n-opt]').forEach(function (el) {
      var v = t[el.dataset.i18nOpt];
      if (v !== undefined) el.textContent = v;
    });

    // Page meta
    if (t['meta.title']) document.title = t['meta.title'];
    var md = document.querySelector('meta[name="description"]');
    if (md && t['meta.description']) md.setAttribute('content', t['meta.description']);

    // html lang attribute
    document.documentElement.lang = lang;

    // Update switcher button states
    document.querySelectorAll('[data-lang]').forEach(function (el) {
      el.classList.toggle('lang-active', el.dataset.lang === lang);
      el.setAttribute('aria-pressed', el.dataset.lang === lang ? 'true' : 'false');
    });
  }

  // Init on DOM ready
  function init() {
    var lang = getLang();
    // Always apply so switcher state is correct; for English the JSON is small
    loadAndApply(lang);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose globally for onclick handlers
  window.setLang = setLang;

  // Re-apply translations to dynamically-inserted DOM (e.g. press list, future widgets).
  // Uses the cached translations for the current language; falls back to a fresh load.
  window.NTApplyI18n = function () {
    var lang = getLang();
    if (CACHE[lang]) {
      apply(lang, CACHE[lang]);
    } else {
      loadAndApply(lang);
    }
  };
})();
