/** @typedef {{ locator: string, filename: string }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

let libPromise = null;

function loadScreenshotLib() {
  if (!libPromise) {
    libPromise = import('https://esm.sh/modern-screenshot');
  }
  return libPromise;
}

function defaultFilename() {
  return `screenshot-${new Date().toISOString().replace(/[:.]/g, '-')}.png`;
}

function downloadBlob(dataUrl, filename) {
  const a = document.createElement('a');
  a.href = dataUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  // Eagerly preload the library
  loadScreenshotLib();

  el.innerHTML = `
    <div style="display: contents">
      <button>Screenshot</button>
    </div>
  `;

  const button = el.querySelector('button');
  const handleClick = async () => {
    const originalText = button.textContent;
    button.textContent = 'Capturing...';
    button.disabled = true;

    try {
      const lib = await loadScreenshotLib();
      const locator = model.get('locator') || 'body';
      const target = document.querySelector(locator);
      if (!target) {
        throw new Error(`Element not found: ${locator}`);
      }
      if (debug) console.log('[moutils:screenshot_button] Capturing:', locator);
      const dataUrl = await lib.domToPng(target);
      const filename = model.get('filename') || defaultFilename();
      downloadBlob(dataUrl, filename);
    } catch (err) {
      if (debug) console.error('[moutils:screenshot_button] Capture failed:', err);
    } finally {
      button.textContent = originalText;
      button.disabled = false;
    }
  };
  button.addEventListener('click', handleClick);

  return () => {
    button.removeEventListener('click', handleClick);
  };
}

function initialize({ model }) {
  if (debug) console.log('[moutils:screenshot_button] Initializing screenshot button widget');
}

export default { render, initialize };
