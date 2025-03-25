/** @typedef {{ children: string, on_hover: Record<string, any>, on_press: Record<string, any>, on_click: Record<string, any>, on_focus: Record<string, any>, on_blur: Record<string, any> }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

const EVENTS = [
  // Mouse events
  'click',
  'contextmenu',
  'dblclick',
  'mousedown',
  'mouseenter',
  'mouseleave',
  'mousemove',
  'mouseout',
  'mouseover',
  'mouseup',

  // Keyboard events
  'keydown',
  'keypress',
  'keyup',

  // Form events
  'change',
  'input',
  'submit',
  'reset',
  'focus',
  'blur',
  'focusin',
  'focusout',

  // Drag events
  'drag',
  'dragend',
  'dragenter',
  'dragleave',
  'dragover',
  'dragstart',
  'drop',

  // Touch events
  'touchstart',
  'touchmove',
  'touchend',
  'touchcancel',

  // Pointer events
  'pointerdown',
  'pointermove',
  'pointerup',
  'pointercancel',
  'pointerover',
  'pointerout',
  'pointerenter',
  'pointerleave',

  // Scroll events
  'scroll',
  'scrollend',

  // Clipboard events
  'copy',
  'cut',
  'paste',

  // Animation and transition
  'animationstart',
  'animationend',
  'animationiteration',
  'transitionend',
];

function validateHTML(html) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');
  return !doc.querySelector('parsererror');
}

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  if (debug) console.log('[moutils:slot] Initializing slot widget');

  // Set display: contents to not affect layout
  el.style.display = 'contents';

  const abortController = new AbortController();

  // Render children with validation
  const updateChildren = () => {
    try {
      const children = model.get('children');
      if (!validateHTML(children)) {
        console.error('[moutils:slot] Invalid HTML provided');
        return;
      }
      el.innerHTML = children;
    } catch (error) {
      console.error('[moutils:slot] Error updating children:', error);
    }
  };

  model.on('change:children', updateChildren);
  updateChildren();

  // Event handlers with validation
  const events = model.get('events') || [];
  for (const event of events) {
    if (!EVENTS.includes(event)) {
      console.warn(`[moutils:slot] Unsupported event type: ${event}`);
      continue;
    }

    const handler = (event) => {
      if (debug) console.log('[moutils:slot] Event', event);
      try {
        const payload = {
          type: event.type,
          target: {
            tagName: event.target.tagName,
            id: event.target.id,
            className: event.target.className,
          },
          timeStamp: event.timeStamp,
        };
        model.set('last_event', {
          name: event.type,
          payload,
        });
        model.save_changes();
      } catch (error) {
        console.error('[moutils:slot] Error handling event:', error);
        model.set('last_event', {
          name: event.type,
          payload: {},
        });
        model.save_changes();
      }
    };

    el.addEventListener(event, handler, { signal: abortController.signal });
  }

  return () => {
    abortController.abort();
  };
}

function initialize({ model }) {
  if (debug) console.log('[moutils:slot] Initializing slot widget');
}

export default { render, initialize };
