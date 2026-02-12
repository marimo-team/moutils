/** @typedef {{ trigger: boolean }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  if (model.get('trigger')) {
    if (debug) console.log('[moutils:print_page] Triggering print');
    requestAnimationFrame(() => {
      window.print();
      model.set('trigger', false);
      model.save_changes();
    });
  }

  return () => {};
}

function initialize({ model }) {
  if (debug) console.log('[moutils:print_page] Initializing print page widget');
}

export default { render, initialize };
