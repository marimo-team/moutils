/** @typedef {{ }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  el.innerHTML = `
    <div style="display: contents">
      <button>Print Page</button>
    </div>
  `;

  const button = el.querySelector('button');
  const handleClick = () => {
    if (debug) console.log('[moutils:print_page_button] Printing page');
    window.print();
  };
  button.addEventListener('click', handleClick);

  return () => {
    button.removeEventListener('click', handleClick);
  };
}

function initialize({ model }) {
  if (debug) console.log('[moutils:print_page_button] Initializing print page button widget');
}

export default { render, initialize };
