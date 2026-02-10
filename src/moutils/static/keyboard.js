/** @typedef {{ shortcut: string, pressed: boolean, event: object }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

function parseShortcut(shortcut) {
  const parts = shortcut.toLowerCase().split('+').map((s) => s.trim());
  const key = parts.pop();
  const modifiers = {
    ctrl: parts.includes('ctrl') || parts.includes('control'),
    shift: parts.includes('shift'),
    alt: parts.includes('alt'),
    meta: parts.includes('meta') || parts.includes('cmd') || parts.includes('command'),
  };
  return { key, modifiers };
}

function matchesShortcut(e, parsed) {
  const keyMatch = e.key.toLowerCase() === parsed.key;
  const ctrlMatch = e.ctrlKey === parsed.modifiers.ctrl;
  const shiftMatch = e.shiftKey === parsed.modifiers.shift;
  const altMatch = e.altKey === parsed.modifiers.alt;
  const metaMatch = e.metaKey === parsed.modifiers.meta;

  return keyMatch && ctrlMatch && shiftMatch && altMatch && metaMatch;
}

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  let parsed = parseShortcut(model.get('shortcut') || '');

  function onKeyDown(e) {
    if (!model.get('shortcut')) return;

    if (matchesShortcut(e, parsed)) {
      if (debug) console.log('[moutils:keyboard] Shortcut matched:', model.get('shortcut'));
      e.preventDefault();

      model.set('pressed', true);
      model.set('event', {
        key: e.key,
        code: e.code,
        ctrlKey: e.ctrlKey,
        shiftKey: e.shiftKey,
        altKey: e.altKey,
        metaKey: e.metaKey,
      });
      model.save_changes();

      // Reset pressed after a tick
      setTimeout(() => {
        model.set('pressed', false);
        model.save_changes();
      }, 100);
    }
  }

  model.on('change:shortcut', () => {
    parsed = parseShortcut(model.get('shortcut') || '');
    if (debug) console.log('[moutils:keyboard] Shortcut updated:', model.get('shortcut'));
  });

  document.addEventListener('keydown', onKeyDown);

  return () => {
    document.removeEventListener('keydown', onKeyDown);
  };
}

function initialize({ model }) {
  if (debug) console.log('[moutils:keyboard] Initializing keyboard shortcut widget');
}

export default { render, initialize };
