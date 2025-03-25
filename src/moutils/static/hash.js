/** @typedef {{ hash: string }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

function isValidHash(hash) {
  try {
    // Empty hash is valid
    if (!hash) return true;

    // Must start with #
    if (!hash.startsWith('#')) return false;

    // Check for invalid characters
    const invalidChars = /[\s\<\>\"\|\?\*\{\}\\\^\[\]`]/;
    if (invalidChars.test(hash)) return false;

    // Check for valid URL encoding
    try {
      decodeURIComponent(hash.slice(1));
    } catch {
      return false;
    }

    return true;
  } catch (e) {
    return false;
  }
}

function normalizeHash(hash) {
  try {
    if (!hash) return '';
    return `#${hash.replace(/^#+/, '')}`;
  } catch (e) {
    return '';
  }
}

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  const handleHashChange = () => {
    if (debug) console.log('[moutils:hash] Hash changed', window.location.hash);
    const newHash = normalizeHash(window.location.hash);
    model.set('hash', newHash);
    model.save_changes();
  };

  window.addEventListener('hashchange', handleHashChange);

  let isUpdating = false;
  model.on('change:hash', () => {
    if (isUpdating) return;
    isUpdating = true;

    try {
      if (debug) console.log('[moutils:hash] Hash changed', model.get('hash'));

      const newHash = model.get('hash');
      if (!isValidHash(newHash)) {
        console.error('[moutils:hash] Invalid hash:', newHash);
        model.set('hash', window.location.hash);
        model.save_changes();
        return;
      }

      const normalizedHash = normalizeHash(newHash);
      if (window.location.hash !== normalizedHash) {
        window.location.hash = normalizedHash;
      }
    } catch (error) {
      console.error('[moutils:hash] Error updating hash:', error);
    } finally {
      isUpdating = false;
    }
  });

  return () => {
    window.removeEventListener('hashchange', handleHashChange);
  };
}

function initialize({ model }) {
  if (debug) console.log('[moutils:hash] Initializing hash widget');

  const initialHash = normalizeHash(window.location.hash);
  model.set('hash', initialHash);
  model.save_changes();
}

export default { render, initialize };
