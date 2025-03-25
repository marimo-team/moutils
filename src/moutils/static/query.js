/** @typedef {{ selector: string, result: Array<{text: string, html: string, attributes: Record<string, string>}> }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';
const QUERY_TIMEOUT = 5000; // 5 second timeout
const DEBOUNCE_DELAY = 250; // 250ms debounce

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

function validateSelector(selector) {
  try {
    document.querySelector(selector);
    return true;
  } catch (e) {
    return false;
  }
}

async function queryDOM(model, selector) {
  try {
    if (debug) console.log('[moutils:query] Querying DOM with selector', selector);

    if (!selector || !validateSelector(selector)) {
      console.error('[moutils:query] Invalid selector:', selector);
      model.set('result', []);
      model.save_changes();
      return;
    }

    const doc = window.document;
    if (!doc) {
      console.error('[moutils:query] Document not available');
      return;
    }

    const queryPromise = new Promise((resolve) => {
      const elements = Array.from(doc.querySelectorAll(selector));
      if (debug) console.log('[moutils:query] Found', elements.length, 'elements');
      const results = elements.map((el) => ({
        text: el.textContent || '',
        html: el.innerHTML,
        attributes: Object.fromEntries(Array.from(el.attributes || []).map((attr) => [attr.name, attr.value])),
      }));
      resolve(results);
    });

    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Query timeout')), QUERY_TIMEOUT);
    });

    const results = await Promise.race([queryPromise, timeoutPromise]);
    model.set('result', results);
    model.save_changes();
  } catch (error) {
    console.error('[moutils:query] DOM query failed:', error);
    model.set('result', []);
    model.save_changes();
  }
}

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  const debouncedQuery = debounce((selector) => queryDOM(model, selector), DEBOUNCE_DELAY);

  model.on('change:selector', () => {
    const selector = model.get('selector');
    if (selector) {
      debouncedQuery(selector);
    }
  });

  return () => {};
}

function initialize({ model }) {
  if (debug) console.log('[moutils:query] Initializing DOM query widget');

  const selector = model.get('selector');
  if (selector) {
    queryDOM(model, selector);
  }
}

export default { render, initialize };
