/**
 * @typedef {{
 *   provider: string,
 *   provider_name: string,
 *   client_id: string,
 *   icon: string,
 *   authorization_url: string,
 *   token_url: string,
 *   redirect_uri: string,
 *   scopes: string,
 *   logout_url: string,
 *   code_verifier: string,
 *   code_challenge: string,
 *   state: string,
 *   authorization_code: string,
 *   access_token: string,
 *   token_type: string,
 *   refresh_token: string,
 *   refresh_token_expires_in: number,
 *   authorized_scopes: string[],
 *   status: 'not_started' | 'initiating' | 'pending' | 'success' | 'error',
 *   error_message: string,
 *   start_auth: boolean,
 *   handle_callback: string,
 *   logout_requested: boolean,
 *   hostname: string
 * }} Model
 */

const debug = localStorage.getItem('moutils-debug') === 'true';

/**
 * Get the current origin and set it as the redirect URI
 * @param {any} model
 */
function setRedirectUri(model) {
  const redirectUri = window.top.location.origin + '/oauth/callback';
  if (debug) console.log('[moutils:pkce_flow] Setting redirect URI:', redirectUri);
  model.set('redirect_uri', redirectUri);
  model.save_changes();
}

/**
 * Safely set display style on an element
 * @param {HTMLElement | null} element
 * @param {string} display
 */
function setDisplayStyle(element, display) {
  if (element) {
    element.style.display = display;
  }
}

/**
 * Safely set text content on an element
 * @param {HTMLElement | null} element
 * @param {string} text
 */
function setTextContent(element, text) {
  if (element) {
    element.innerText = text;
  }
}

/**
 * Safely set HTML content on an element
 * @param {HTMLElement | null} element
 * @param {string} html
 */
function setHtmlContent(element, html) {
  if (element) {
    element.innerHTML = html;
  }
}

/**
 * Render function for the PKCEFlow widget
 * @param {{ model: any, el: HTMLElement }} options
 */
function render({ model, el }) {
  // Set the redirect URI based on the current origin
  // setRedirectUri(model);

  // Initialize UI elements
  el.innerHTML = createPKCEFlowHTML(
    model.get('provider'),
    model.get('provider_name'),
    model.get('client_id'),
    model.get('icon')
  );

  // Get UI elements with JSDoc type casts
  const startAuthBtn = /** @type {HTMLButtonElement | null} */ (el.querySelector('#startAuthBtn'));
  const initialSection = /** @type {HTMLElement | null} */ (el.querySelector('#initialSection'));
  const pendingSection = /** @type {HTMLElement | null} */ (el.querySelector('#pendingSection'));
  const tokenSection = /** @type {HTMLElement | null} */ (el.querySelector('#tokenSection'));
  const statusMessage = /** @type {HTMLElement | null} */ (el.querySelector('#statusMessage'));
  const logoutBtn = /** @type {HTMLButtonElement | null} */ (el.querySelector('#logoutBtn'));

  if (!startAuthBtn || !initialSection || !pendingSection || !tokenSection || !statusMessage) {
    throw new Error('Missing required UI elements');
  }

  // Set up event listeners
  if (startAuthBtn) {
    startAuthBtn.addEventListener('click', startPKCEFlow);
  }

  if (logoutBtn) {
    logoutBtn.addEventListener('click', logout);
  }

  // Update UI based on model changes
  model.on('change:status', () => {
    const status = model.get('status');
    if (debug) console.log('[moutils:pkce_flow] Status changed:', status);

    // Reset all sections and button states first
    setDisplayStyle(initialSection, 'none');
    setDisplayStyle(pendingSection, 'none');
    setDisplayStyle(tokenSection, 'none');
    if (startAuthBtn) startAuthBtn.disabled = true;

    if (status === 'error') {
      setDisplayStyle(initialSection, 'block');
      if (startAuthBtn) {
        startAuthBtn.disabled = false;
      }
      return;
    }

    if (status === 'not_started') {
      setDisplayStyle(initialSection, 'block');
      if (startAuthBtn) {
        setHtmlContent(startAuthBtn, `<span class="btn-text">Sign in with ${model.get('provider_name')}</span>`);
        startAuthBtn.disabled = false;
      }
    } else if (status === 'initiating') {
      setDisplayStyle(initialSection, 'block');
      if (startAuthBtn) {
        setHtmlContent(startAuthBtn, '<span class="spinner"></span> <span class="btn-text">Starting...</span>');
      }
    } else if (status === 'pending') {
      setDisplayStyle(pendingSection, 'block');
      setHtmlContent(statusMessage, '<p>Waiting for authorization...</p>');
    } else if (status === 'success') {
      setDisplayStyle(tokenSection, 'block');
    }
  });

  model.on('change:error_message', () => {
    const errorMessage = model.get('error_message');
    if (debug) console.log('[moutils:pkce_flow] Error message changed:', errorMessage);
    if (statusMessage && errorMessage) {
      setHtmlContent(statusMessage, `<p class="error">${errorMessage}</p>`);
    }
  });

  // Store the authorization URL
  let currentAuthUrl = model.get('authorization_url');

  // Listen for changes to the authorization URL
  model.on('change:authorization_url', () => {
    const newAuthUrl = model.get('authorization_url');
    if (debug) console.log('[moutils:pkce_flow] Authorization URL changed:', newAuthUrl);
    if (newAuthUrl) {
      currentAuthUrl = newAuthUrl;
    }
  });

  // Add copy token functionality
  const copyTokenBtn = el.querySelector('#copyTokenBtn');
  if (copyTokenBtn) {
    copyTokenBtn.addEventListener('click', () => {
      const token = model.get('access_token');
      if (token) {
        navigator.clipboard.writeText(token).then(() => {
          const originalText = copyTokenBtn.querySelector('.btn-text').textContent;
          copyTokenBtn.querySelector('.btn-text').textContent = 'Copied!';
          setTimeout(() => {
            copyTokenBtn.querySelector('.btn-text').textContent = originalText;
          }, 2000);
        });
      }
    });
  }

  /**
   * Start the PKCE flow authentication process
   */
  function startPKCEFlow() {
    if (debug) console.log('[moutils:pkce_flow] Starting PKCE flow');
    model.set('start_auth', true);
    model.save_changes();

    // Wait for the authorization URL to be updated with parameters
    const checkAuthUrl = setInterval(() => {
      const authUrl = model.get('authorization_url');
      if (debug) console.log('[moutils:pkce_flow] Checking authorization URL:', authUrl);

      // Check if the URL has parameters (contains a ?)
      if (authUrl && authUrl.includes('?')) {
        clearInterval(checkAuthUrl);
        if (debug) console.log('[moutils:pkce_flow] Opening authorization URL:', authUrl);

        // Store the state and code verifier in localStorage before redirecting
        const url = new URL(authUrl);
        const state = url.searchParams.get('state');
        const codeVerifier = model.get('code_verifier');
        if (state) {
          if (debug) console.log('[moutils:pkce_flow] Storing state in localStorage:', state);
          localStorage.setItem('pkce_state', state);
        }
        if (codeVerifier) {
          if (debug) console.log('[moutils:pkce_flow] Storing code verifier in localStorage:', codeVerifier);
          localStorage.setItem('pkce_code_verifier', codeVerifier);
        }

        window.location.href = authUrl; // Open in same window instead of new tab
      }
    }, 100); // Check every 100ms

    // Stop checking after 5 seconds to prevent infinite loop
    setTimeout(() => {
      clearInterval(checkAuthUrl);
      if (debug) console.log('[moutils:pkce_flow] Timed out waiting for authorization URL');
    }, 5000);
  }

  // Listen for URL changes to handle the callback
  window.addEventListener('popstate', handleUrlChange);
  handleUrlChange();

  function handleUrlChange() {
    const url = window.location.href;
    if (debug) console.log('[moutils:pkce_flow] Checking URL:', url);

    // Check if we have a callback URL with code and state
    if (url.includes('code=') && url.includes('state=')) {
      if (debug) console.log('[moutils:pkce_flow] Found callback URL:', url);

      // Get the stored state and code verifier from localStorage
      const storedState = localStorage.getItem('pkce_state');
      const storedCodeVerifier = localStorage.getItem('pkce_code_verifier');
      if (debug) {
        console.log('[moutils:pkce_flow] Retrieved state from localStorage:', storedState);
        console.log('[moutils:pkce_flow] Retrieved code verifier from localStorage:', storedCodeVerifier);
      }

      // Set the callback URL and code verifier in the model to trigger Python processing
      model.set('handle_callback', url);
      if (storedCodeVerifier) {
        model.set('code_verifier', storedCodeVerifier);
      }
      model.save_changes();

      // Clear the URL parameters to prevent re-processing
      const baseUrl = url.split('?')[0];
      window.history.replaceState({}, document.title, baseUrl);

      // Clear the stored state and code verifier
      localStorage.removeItem('pkce_state');
      localStorage.removeItem('pkce_code_verifier');
    }
  }

  /**
   * Logout the user
   */
  async function logout() {
    if (debug) {
      console.log('[moutils:pkce_flow] Logging out');
    }

    const accessToken = model.get('access_token');
    const logoutUrl = model.get('logout_url');

    if (accessToken && logoutUrl) {
      try {
        // Call the provider's OAuth revocation endpoint
        const response = await fetch(logoutUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({
            token: accessToken,
            client_id: model.get('client_id'),
          }),
        });

        if (debug) {
          console.log('[moutils:pkce_flow] Revocation response:', response.status);
        }

        if (!response.ok) {
          console.error('[moutils:pkce_flow] Failed to revoke token:', response.status);
        }
      } catch (error) {
        console.error('[moutils:pkce_flow] Error revoking token:', error);
      }
    }

    // Set logout flag to trigger Python handler
    model.set('logout_requested', true);
    model.save_changes();
  }
}

/**
 * Initialize the widget
 * @param {{ model: any }} options
 */
function initialize({ model }) {
  if (debug) console.log('[moutils:pkce_flow] Initializing widget');

  // Set the hostname from the current location
  const hostname = window.location.hostname;
  if (debug) {
    console.log('[moutils:pkce_flow] Current location:', window.location.href);
    console.log('[moutils:pkce_flow] Raw hostname:', hostname);
    console.log('[moutils:pkce_flow] Setting hostname traitlet to:', hostname);
  }
  model.set('hostname', hostname);
  model.save_changes();
}

/**
 * Create the HTML for the PKCE flow widget
 * @param {string} provider
 * @param {string} providerName
 * @param {string} clientId
 * @param {string} icon
 * @returns {string}
 */
function createPKCEFlowHTML(provider, providerName, clientId, icon) {
  return `
    <div class="pkce-flow">
      <div id="initialSection" class="section">
        <div class="container">
          <div class="description">
            You will be redirected to ${providerName}'s login page.
          </div>
          <button class="button" id="startAuthBtn">
            <span class="btn-text">Sign in with ${providerName}</span>
          </button>
          <div id="statusMessage"></div>
        </div>
      </div>

      <div id="pendingSection" class="section" style="display: none;">
        <div class="container">
          <div class="title">Waiting for Authorization</div>
          <div class="description">
            Please complete the sign-in process in your browser.
          </div>
          <div class="spinner"></div>
          <div id="statusMessage"></div>
        </div>
      </div>

      <div id="tokenSection" class="section" style="display: none;">
        <div class="container">
          <div class="title">Successfully Signed In</div>
          <div class="description">
            You have successfully signed in with ${providerName}.
          </div>
          <button class="button logout-button" id="logoutBtn">
            <span class="btn-text">Logout</span>
          </button>
        </div>
      </div>
    </div>
  `;
}

export default { render, initialize };
