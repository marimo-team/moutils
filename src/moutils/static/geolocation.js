/** @typedef {{ latitude: number, longitude: number, accuracy: number, error: string, enabled: boolean }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  let watchId = null;

  function startWatching() {
    if (!navigator.geolocation) {
      model.set('error', 'Geolocation is not supported by this browser');
      model.save_changes();
      return;
    }

    watchId = navigator.geolocation.watchPosition(
      (position) => {
        if (debug) console.log('[moutils:geolocation] position:', position.coords);
        model.set('latitude', position.coords.latitude);
        model.set('longitude', position.coords.longitude);
        model.set('accuracy', position.coords.accuracy);
        model.set('error', '');
        model.save_changes();
      },
      (err) => {
        if (debug) console.log('[moutils:geolocation] error:', err.message);
        model.set('error', err.message);
        model.save_changes();
      },
      { enableHighAccuracy: true }
    );
  }

  function stopWatching() {
    if (watchId !== null) {
      navigator.geolocation.clearWatch(watchId);
      watchId = null;
    }
  }

  model.on('change:enabled', () => {
    if (model.get('enabled')) {
      startWatching();
    } else {
      stopWatching();
    }
  });

  // Start if already enabled
  if (model.get('enabled')) {
    startWatching();
  }

  return () => {
    stopWatching();
  };
}

function initialize({ model }) {
  if (debug) console.log('[moutils:geolocation] Initializing geolocation widget');
}

export default { render, initialize };
