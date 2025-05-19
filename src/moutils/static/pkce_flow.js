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
 *   handle_callback: string
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
  const startNewAuthBtn = /** @type {HTMLButtonElement | null} */ (el.querySelector('#tokenSection #startNewAuthBtn'));

  if (!startAuthBtn || !initialSection || !pendingSection || !tokenSection || !statusMessage || !startNewAuthBtn) {
    throw new Error('Missing required UI elements');
  }

  // Set up event listeners
  if (startAuthBtn) {
    startAuthBtn.addEventListener('click', startPKCEFlow);
  }

  if (startNewAuthBtn) {
    startNewAuthBtn.addEventListener('click', startPKCEFlow);
  }

  // Update UI based on model changes
  model.on('change:status', () => {
    const status = model.get('status');
    if (debug) console.log('[moutils:pkce_flow] Status changed:', status);

    if (status === 'error') {
      return;
    }

    // For non-error states, manage section visibility and button states
    setDisplayStyle(initialSection, 'none');
    setDisplayStyle(pendingSection, 'none');
    setDisplayStyle(tokenSection, 'none');
    if (startAuthBtn) startAuthBtn.disabled = true;

    if (status === 'not_started') {
      setDisplayStyle(initialSection, 'block');
      if (startAuthBtn) {
        setHtmlContent(
          startAuthBtn,
          `<span class="btn-text">Sign in with ${model.get('provider_name')}</span>`
        );
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

  /**
   * Start the PKCE flow authentication process
   */
  function startPKCEFlow() {
    if (debug) console.log('[moutils:pkce_flow] Starting PKCE flow');
    model.set('start_auth', true);
    model.save_changes();

    // Get the authorization URL from the model
    const authUrl = model.get('authorization_url');
    
    if (authUrl) {
      if (debug) console.log('[moutils:pkce_flow] Opening authorization URL:', authUrl);
      window.open(authUrl, '_blank');
    }
  }

  // Listen for URL changes to handle the callback
  window.addEventListener('popstate', handleUrlChange);
  handleUrlChange();

  function handleUrlChange() {
    const url = window.location.href;
    if (url.includes('code=') && url.includes('state=')) {
      if (debug) console.log('[moutils:pkce_flow] Handling callback URL:', url);
      model.set('handle_callback', url);
      model.save_changes();
    }
  }
}

/**
 * Initialize the widget
 * @param {{ model: any }} options
 */
function initialize({ model }) {
  if (debug) console.log('[moutils:pkce_flow] Initializing widget');
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
          <button class="button" id="startNewAuthBtn">
            <span class="btn-text">Sign in with a different account</span>
          </button>
        </div>
      </div>
    </div>
  `;
}

export default { render, initialize };
