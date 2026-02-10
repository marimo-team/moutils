/** @typedef {{ scheme: string, prefers_dark: boolean }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  const mql = window.matchMedia('(prefers-color-scheme: dark)');

  function update() {
    const isDark = mql.matches;
    if (debug) console.log('[moutils:colorscheme] scheme changed:', isDark ? 'dark' : 'light');
    model.set('scheme', isDark ? 'dark' : 'light');
    model.set('prefers_dark', isDark);
    model.save_changes();
  }

  mql.addEventListener('change', update);

  return () => {
    mql.removeEventListener('change', update);
  };
}

function initialize({ model }) {
  if (debug) console.log('[moutils:colorscheme] Initializing colorscheme widget');

  const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  model.set('scheme', isDark ? 'dark' : 'light');
  model.set('prefers_dark', isDark);
  model.save_changes();
}

export default { render, initialize };
