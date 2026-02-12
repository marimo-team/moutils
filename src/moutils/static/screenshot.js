/** @typedef {{ locator: string, filename: string, trigger: boolean }} Model */

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
  if (model.get('trigger')) {
    requestAnimationFrame(async () => {
      try {
        const lib = await loadScreenshotLib();
        const locator = model.get('locator') || 'body';
        const target = document.querySelector(locator);
        if (!target) {
          throw new Error(`Element not found: ${locator}`);
        }
        if (debug) console.log('[moutils:screenshot] Capturing:', locator);
        const dataUrl = await lib.domToPng(target);
        const filename = model.get('filename') || defaultFilename();
        downloadBlob(dataUrl, filename);
      } catch (err) {
        if (debug) console.error('[moutils:screenshot] Capture failed:', err);
      } finally {
        model.set('trigger', false);
        model.save_changes();
      }
    });
  }

  return () => {};
}

function initialize({ model }) {
  if (debug) console.log('[moutils:screenshot] Initializing screenshot widget');
}

export default { render, initialize };
