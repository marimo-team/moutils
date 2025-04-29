/** @typedef {{ text: string, success: boolean, button_text: string, success_text: string }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  const handleCopy = async () => {
    try {
      if (debug) console.log('[moutils:copy] Copying text:', model.get('text'));
      await navigator.clipboard.writeText(model.get('text'));
      model.set('success', true);
      model.save_changes();
    } catch (err) {
      if (debug) console.error('[moutils:copy] Copy failed:', err);
      model.set('success', false);
      model.save_changes();
    }
  };

  el.innerHTML = `
    <div style="display: contents">
      <button>${model.get('button_text') || 'Copy to Clipboard'}</button>
      ${model.get('success') ? `<span>${model.get('success_text') || 'Copied!'}</span>` : ''}
    </div>
  `;

  const button = el.querySelector('button');
  button.addEventListener('click', handleCopy);

  return () => {
    button.removeEventListener('click', handleCopy);
  };
}

function initialize({ model }) {
  if (debug) console.log('[moutils:copy] Initializing copy widget');
}

export default { render, initialize };
