/** @typedef {{ domain: string, cookies: Record<string, { value: string, options?: { domain?: string, path?: string, expires?: Date | number, secure?: boolean, sameSite?: 'Strict' | 'Lax' | 'None' } }> }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';
const MAX_COOKIE_SIZE = 4096; // Maximum size in bytes for most browsers

function getCookies(model) {
  try {
    const allCookies = document.cookie.split(';').reduce((acc, cookie) => {
      const [key, value] = cookie.trim().split('=').map(decodeURIComponent);
      if (key && value) {
        acc[key] = { value };
      }
      return acc;
    }, {});

    model.set('cookies', allCookies);
    model.save_changes();
  } catch (error) {
    console.error('[moutils:cookies] Cookie retrieval failed:', error);
  }
}

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  function setCookies(cookies) {
    try {
      if (debug) console.log('[moutils:cookies] Setting cookies', cookies);

      for (const [key, cookieData] of Object.entries(cookies)) {
        try {
          const { value, options = {} } = cookieData;
          const encodedKey = encodeURIComponent(key);
          const encodedValue = encodeURIComponent(value);

          // Check cookie size
          const cookieString = `${encodedKey}=${encodedValue}`;
          if (cookieString.length > MAX_COOKIE_SIZE) {
            console.error(`[moutils:cookies] Cookie '${key}' exceeds maximum size of ${MAX_COOKIE_SIZE} bytes`);
            continue;
          }

          const cookieParts = [`${encodedKey}=${encodedValue}`];

          if (options.path) cookieParts.push(`path=${options.path}`);
          if (options.domain) cookieParts.push(`domain=${options.domain}`);
          if (options.expires) {
            const expires =
              typeof options.expires === 'number' ? new Date(Date.now() + options.expires) : options.expires;
            cookieParts.push(`expires=${expires.toUTCString()}`);
          }
          if (options.secure) cookieParts.push('secure');
          if (options.sameSite) cookieParts.push(`samesite=${options.sameSite}`);

          document.cookie = cookieParts.join('; ');
        } catch (error) {
          console.error(`[moutils:cookies] Failed to set cookie '${key}':`, error);
        }
      }
    } catch (error) {
      console.error('[moutils:cookies] Cookie setting failed:', error);
    }
  }

  model.on('change:cookies', () => {
    const cookies = model.get('cookies');
    if (Object.keys(cookies).length > 0) {
      setCookies(cookies);
    }
  });

  return () => {};
}

function initialize({ model }) {
  if (debug) console.log('[moutils:cookies] Initializing cookie manager widget');

  getCookies(model);
}

export default { render, initialize };
