/** @typedef {{ path: string }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

function isValidPath(path) {
  try {
    // Basic path validation
    if (!path.startsWith('/')) return false;
    if (path.includes('..')) return false;
    if (path.includes('//')) return false;

    // Check for invalid characters
    const invalidChars = /[\<\>\:\"\|\?\*]/;
    if (invalidChars.test(path)) return false;

    return true;
  } catch (e) {
    return false;
  }
}

function normalizePath(path) {
  try {
    // Remove multiple slashes and trailing slash
    return `/${path}`.replace(/\/+/g, '/').replace(/\/$/, '') || '/';
  } catch (e) {
    return '/';
  }
}

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  const handlePopState = () => {
    if (debug) console.log('[moutils:path] Path changed', window.location.pathname);
    const newPath = normalizePath(window.location.pathname);
    model.set('path', newPath);
    model.save_changes();
  };

  window.addEventListener('popstate', handlePopState);

  let isUpdating = false;
  model.on('change:path', () => {
    if (isUpdating) return;
    isUpdating = true;

    try {
      if (debug) console.log('[moutils:path] Path changed', model.get('path'));

      const newPath = model.get('path');
      if (!isValidPath(newPath)) {
        console.error('[moutils:path] Invalid path:', newPath);
        model.set('path', window.location.pathname);
        model.save_changes();
        return;
      }

      const normalizedPath = normalizePath(newPath);
      if (window.location.pathname !== normalizedPath) {
        window.history.pushState({}, '', normalizedPath);
      }
    } catch (error) {
      console.error('[moutils:path] Error updating path:', error);
    } finally {
      isUpdating = false;
    }
  });

  return () => {
    window.removeEventListener('popstate', handlePopState);
  };
}

function initialize({ model }) {
  if (debug) console.log('[moutils:path] Initializing path widget');

  const initialPath = normalizePath(window.location.pathname);
  model.set('path', initialPath);
  model.save_changes();
}

export default { render, initialize };
