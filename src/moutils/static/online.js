/** @typedef {{ online: boolean }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  function onOnline() {
    if (debug) console.log('[moutils:online] online');
    model.set('online', true);
    model.save_changes();
  }

  function onOffline() {
    if (debug) console.log('[moutils:online] offline');
    model.set('online', false);
    model.save_changes();
  }

  window.addEventListener('online', onOnline);
  window.addEventListener('offline', onOffline);

  return () => {
    window.removeEventListener('online', onOnline);
    window.removeEventListener('offline', onOffline);
  };
}

function initialize({ model }) {
  if (debug) console.log('[moutils:online] Initializing online status widget');

  model.set('online', navigator.onLine);
  model.save_changes();
}

export default { render, initialize };
