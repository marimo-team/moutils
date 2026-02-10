/** @typedef {{ title: string, body: string, icon: string, permission: string, send: boolean }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  function updatePermission() {
    if (typeof Notification !== 'undefined') {
      model.set('permission', Notification.permission);
      model.save_changes();
    }
  }

  model.on('change:send', () => {
    if (!model.get('send')) return;

    if (typeof Notification === 'undefined') {
      if (debug) console.log('[moutils:notification] Notifications not supported');
      model.set('send', false);
      model.save_changes();
      return;
    }

    const fire = () => {
      const title = model.get('title') || 'Notification';
      const options = {};
      const body = model.get('body');
      const icon = model.get('icon');
      if (body) options.body = body;
      if (icon) options.icon = icon;

      if (debug) console.log('[moutils:notification] Sending:', title, options);
      new Notification(title, options);

      // Reset send flag
      model.set('send', false);
      updatePermission();
    };

    if (Notification.permission === 'granted') {
      fire();
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then((perm) => {
        updatePermission();
        if (perm === 'granted') {
          fire();
        } else {
          model.set('send', false);
          model.save_changes();
        }
      });
    } else {
      if (debug) console.log('[moutils:notification] Permission denied');
      model.set('send', false);
      updatePermission();
    }
  });

  return () => {};
}

function initialize({ model }) {
  if (debug) console.log('[moutils:notification] Initializing notification widget');

  if (typeof Notification !== 'undefined') {
    model.set('permission', Notification.permission);
    model.save_changes();
  }
}

export default { render, initialize };
