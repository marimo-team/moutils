/** @typedef {{ width: number, height: number }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  let timeout = null;

  function update() {
    if (debug) console.log('[moutils:viewport] resize:', window.innerWidth, 'x', window.innerHeight);
    model.set('width', window.innerWidth);
    model.set('height', window.innerHeight);
    model.save_changes();
  }

  function onResize() {
    clearTimeout(timeout);
    timeout = setTimeout(update, 150);
  }

  window.addEventListener('resize', onResize);

  return () => {
    clearTimeout(timeout);
    window.removeEventListener('resize', onResize);
  };
}

function initialize({ model }) {
  if (debug) console.log('[moutils:viewport] Initializing viewport widget');

  model.set('width', window.innerWidth);
  model.set('height', window.innerHeight);
  model.save_changes();
}

export default { render, initialize };
