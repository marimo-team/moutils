/** @typedef {{
 *   protocol: string,
 *   hostname: string,
 *   port: string,
 *   pathname: string,
 *   search: string,
 *   hash: string,
 *   username: string,
 *   password: string,
 *   href: string
 * }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

function parseURL(url) {
  try {
    const parsed = new URL(url, window.location.origin);
    return {
      protocol: parsed.protocol,
      hostname: parsed.hostname,
      port: parsed.port,
      pathname: parsed.pathname,
      search: parsed.search,
      hash: parsed.hash,
      username: parsed.username,
      password: parsed.password,
      href: parsed.href,
    };
  } catch (e) {
    // Fallback to current location
    return {
      protocol: window.location.protocol,
      hostname: window.location.hostname,
      port: window.location.port,
      pathname: window.location.pathname,
      search: window.location.search,
      hash: window.location.hash,
      username: '',
      password: '',
      href: window.location.href,
    };
  }
}

function buildURL(components) {
  try {
    const url = new URL(window.location.href);

    if (components.protocol) url.protocol = components.protocol;
    if (components.hostname) url.hostname = components.hostname;
    if (components.port) url.port = components.port;
    if (components.pathname) url.pathname = components.pathname;
    if (components.search) url.search = components.search;
    if (components.hash) url.hash = components.hash;
    if (components.username) url.username = components.username;
    if (components.password) url.password = components.password;

    return url.href;
  } catch (e) {
    if (debug) console.error('[moutils:urlinfo] Error building URL:', e);
    return window.location.href;
  }
}

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  const handleLocationChange = () => {
    if (debug) console.log('[moutils:urlinfo] Location changed');

    const urlInfo = parseURL(window.location.href);

    model.set('protocol', urlInfo.protocol);
    model.set('hostname', urlInfo.hostname);
    model.set('port', urlInfo.port);
    model.set('pathname', urlInfo.pathname);
    model.set('search', urlInfo.search);
    model.set('hash', urlInfo.hash);
    model.set('username', urlInfo.username);
    model.set('password', urlInfo.password);
    model.set('href', urlInfo.href);
    model.save_changes();
  };

  // Listen for various navigation events
  window.addEventListener('popstate', handleLocationChange);
  window.addEventListener('hashchange', handleLocationChange);

  // Listen for programmatic navigation
  const originalPushState = history.pushState;
  const originalReplaceState = history.replaceState;

  history.pushState = function (...args) {
    originalPushState.apply(history, args);
    setTimeout(handleLocationChange, 0);
  };

  history.replaceState = function (...args) {
    originalReplaceState.apply(history, args);
    setTimeout(handleLocationChange, 0);
  };

  let isUpdating = false;

  // Watch for changes to any URL component
  const urlComponents = ['protocol', 'hostname', 'port', 'pathname', 'search', 'hash', 'username', 'password'];

  urlComponents.forEach((component) => {
    model.on(`change:${component}`, () => {
      if (isUpdating) return;
      isUpdating = true;

      try {
        if (debug) console.log(`[moutils:urlinfo] ${component} changed to:`, model.get(component));

        const components = {};
        urlComponents.forEach((comp) => {
          components[comp] = model.get(comp);
        });

        const newHref = buildURL(components);

        // Update href in model
        model.set('href', newHref);

        // Navigate to new URL if it's different
        if (window.location.href !== newHref) {
          window.history.pushState({}, '', newHref);
        }

        model.save_changes();
      } catch (error) {
        console.error(`[moutils:urlinfo] Error updating ${component}:`, error);
      } finally {
        isUpdating = false;
      }
    });
  });

  return () => {
    window.removeEventListener('popstate', handleLocationChange);
    window.removeEventListener('hashchange', handleLocationChange);
    history.pushState = originalPushState;
    history.replaceState = originalReplaceState;
  };
}

function initialize({ model }) {
  if (debug) console.log('[moutils:urlinfo] Initializing URLInfo widget');

  const urlInfo = parseURL(window.location.href);

  model.set('protocol', urlInfo.protocol);
  model.set('hostname', urlInfo.hostname);
  model.set('port', urlInfo.port);
  model.set('pathname', urlInfo.pathname);
  model.set('search', urlInfo.search);
  model.set('hash', urlInfo.hash);
  model.set('username', urlInfo.username);
  model.set('password', urlInfo.password);
  model.set('href', urlInfo.href);
  model.save_changes();
}

export default { render, initialize };
