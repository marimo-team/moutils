/** @typedef {{ visible: boolean, state: string }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  function onVisibilityChange() {
    const state = document.visibilityState;
    const visible = state === 'visible';
    if (debug) console.log('[moutils:visibility] state:', state);
    model.set('visible', visible);
    model.set('state', state);
    model.save_changes();
  }

  document.addEventListener('visibilitychange', onVisibilityChange);

  return () => {
    document.removeEventListener('visibilitychange', onVisibilityChange);
  };
}

function initialize({ model }) {
  if (debug) console.log('[moutils:visibility] Initializing page visibility widget');

  const state = document.visibilityState;
  model.set('visible', state === 'visible');
  model.set('state', state);
  model.save_changes();
}

export default { render, initialize };
