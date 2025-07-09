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
 *   hostname: string,
 *   port: string,
 *   proxy: string,
 *   use_new_tab: boolean
 * }} Model
 */

const debug = localStorage.getItem('moutils-debug') === 'true';

/**
 * Store OAuth token data in localStorage with expiration
 * @param {string} token - The access token
 * @param {string} tokenType - The token type (e.g., 'bearer')
 * @param {string} refreshToken - The refresh token (optional)
 * @param {number} expiresIn - Token expiration time in seconds
 * @param {string} provider - The OAuth provider name
 * @param {string[]} scopes - The authorized scopes
 */
function storeOAuthToken(token, tokenType, refreshToken, expiresIn, provider, scopes) {
  const tokenData = {
    access_token: token,
    token_type: tokenType,
    refresh_token: refreshToken || '',
    expires_at: expiresIn ? Date.now() + (expiresIn * 1000) : null,
    provider: provider,
    scopes: scopes || [],
    stored_at: Date.now()
  };
  
  localStorage.setItem('__pkce_token_data', JSON.stringify(tokenData));
  if (debug) console.log('[moutils:pkce_flow] Stored OAuth token data with expiration:', tokenData.expires_at);
}

/**
 * Get stored OAuth token data from localStorage
 * @returns {Object|null} The token data or null if not found/invalid
 */
function getStoredOAuthToken() {
  try {
    const tokenDataStr = localStorage.getItem('__pkce_token_data');
    if (!tokenDataStr) return null;
    
    const tokenData = JSON.parse(tokenDataStr);
    
    // Check if token has expired
    if (tokenData.expires_at && Date.now() > tokenData.expires_at) {
      if (debug) console.log('[moutils:pkce_flow] Stored token has expired, removing');
      localStorage.removeItem('__pkce_token_data');
      return null;
    }
    
    // Check if token is too old (more than 24 hours without expiration)
    if (!tokenData.expires_at && (Date.now() - tokenData.stored_at) > 24 * 60 * 60 * 1000) {
      if (debug) console.log('[moutils:pkce_flow] Stored token is too old (24h), removing');
      localStorage.removeItem('__pkce_token_data');
      return null;
    }
    
    if (debug) console.log('[moutils:pkce_flow] Found valid stored OAuth token for provider:', tokenData.provider);
    return tokenData;
  } catch (error) {
    if (debug) console.error('[moutils:pkce_flow] Error parsing stored token:', error);
    localStorage.removeItem('__pkce_token_data');
    return null;
  }
}

/**
 * Clear stored OAuth token data
 */
function clearStoredOAuthToken() {
  localStorage.removeItem('__pkce_token_data');
  if (debug) console.log('[moutils:pkce_flow] Cleared stored OAuth token data');
}

/**
 * Check for OAuth token in URL parameters first, then localStorage
 */
function checkForOAuthToken() {
  // Check URL parameters first (for same-tab flows)
  const urlParams = new URLSearchParams(window.location.search);
  const tokenFromUrl = urlParams.get('__pkce_value');
  
  if (tokenFromUrl) {
    if (debug) console.log('[moutils:pkce_flow] Found OAuth token in URL parameters:', tokenFromUrl.substring(0, 20) + '...');
    
    // Store token in localStorage for future use (legacy format for backward compatibility)
    localStorage.setItem('__pkce_token', tokenFromUrl);
    
    // Dispatch event to notify the widget
    window.dispatchEvent(new CustomEvent('oauth-token', {
      detail: { token: tokenFromUrl }
    }));
    
    // Clear the token from URL
    urlParams.delete('__pkce_value');
    const newUrl = window.location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
    window.history.replaceState({}, document.title, newUrl);
    return;
  }
  
  // If no token in URL, check localStorage (for new-tab flows)
  const storedToken = localStorage.getItem('__pkce_token');
  if (storedToken) {
    if (debug) console.log('[moutils:pkce_flow] Found OAuth token in localStorage (legacy):', storedToken.substring(0, 20) + '...');
    window.dispatchEvent(new CustomEvent('oauth-token', {
      detail: { token: storedToken }
    }));
    // Optional: clear it if you don't want to persist it
    // localStorage.removeItem('__pkce_token');
  }
}

/**
 * Check for and restore valid stored OAuth token on page load
 * @param {any} model - The widget model
 * @returns {boolean} True if a token was restored, false otherwise
 */
function checkForStoredToken(model) {
  const tokenData = getStoredOAuthToken();
  if (tokenData) {
    if (debug) console.log('[moutils:pkce_flow] Restoring stored OAuth token for provider:', tokenData.provider);
    
    // Set the token data in the model to trigger Python processing
    model.set('access_token', tokenData.access_token);
    model.set('token_type', tokenData.token_type);
    model.set('refresh_token', tokenData.refresh_token);
    model.set('authorized_scopes', tokenData.scopes);
    model.set('status', 'success');
    model.save_changes();
    
    // Dispatch event to notify any listeners
    window.dispatchEvent(new CustomEvent('oauth-token-restored', {
      detail: { tokenData: tokenData }
    }));
    
    return true;
  }
  return false;
}

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
 * Update the UI based on the current status
 * @param {any} model
 * @param {HTMLElement} initialSection
 * @param {HTMLElement} pendingSection
 * @param {HTMLElement} tokenSection
 * @param {HTMLButtonElement} startAuthBtn
 * @param {HTMLElement} statusMessage
 */
function updateUIForStatus(model, initialSection, pendingSection, tokenSection, startAuthBtn, statusMessage) {
  const status = model.get('status');
  if (debug) console.log('[moutils:pkce_flow] updateUIForStatus:', status);

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

  // Check for OAuth token in localStorage on initialization (legacy)
  checkForOAuthToken();
  
  // Check for and restore valid stored OAuth token on page load
  const tokenRestored = checkForStoredToken(model);
  
  // Check if there's an auth code in localStorage (for page refresh scenarios)
  const authCode = localStorage.getItem('__pkce_auth_code');
  const authState = localStorage.getItem('__pkce_state');
  if (authCode && authState && !tokenRestored) {
    if (debug) console.log('[moutils:pkce_flow] Found auth code in localStorage on page load, setting status to pending');
    model.set('status', 'pending');
    model.save_changes();
  }

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
    updateUIForStatus(model, initialSection, pendingSection, tokenSection, startAuthBtn, statusMessage);
  });

  // Immediately update UI after restoring token (in case status is already 'success')
  // Use a small delay to ensure model changes are processed
  if (tokenRestored) {
    setTimeout(() => {
      updateUIForStatus(model, initialSection, pendingSection, tokenSection, startAuthBtn, statusMessage);
    }, 100);
  }

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
          localStorage.setItem('__pkce_state', state);
        }
        if (codeVerifier) {
          if (debug) console.log('[moutils:pkce_flow] Storing code verifier in localStorage:', codeVerifier);
          localStorage.setItem('__pkce_code_verifier', codeVerifier);
        }

        // Determine the environment and handle accordingly
        const origin = window.location.origin;
        const useNewTab = model.get('use_new_tab');
        if (debug) console.log('[moutils:pkce_flow] Current origin:', origin);
        if (debug) console.log('[moutils:pkce_flow] Use new tab:', useNewTab);

        if (useNewTab) {
          // Use new tab flow
          if (debug) console.log('[moutils:pkce_flow] Using new tab flow');
          window.open(authUrl, '_blank');
        } else {
          // Use same tab flow
          if (debug) console.log('[moutils:pkce_flow] Using same tab flow');
          window.location.href = authUrl;
        }
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

  // Listen for OAuth token events from localStorage
  if (debug) console.log('[moutils:pkce_flow] Setting up oauth-token event listener');
  window.addEventListener('oauth-token', (event) => {
    if (debug) console.log('[moutils:pkce_flow] Received oauth-token event:', event.detail);
    const token = event.detail.token;
    if (token) {
      if (debug) console.log('[moutils:pkce_flow] Processing oauth-token with token:', token.substring(0, 20) + '...');
      // Set the token in the model to trigger Python processing
      model.set('access_token', token);
      model.set('status', 'success');
      model.save_changes();
    }
  });
  
  // Fallback: Check for auth code in localStorage periodically (for WASM builds where events don't cross window boundaries)
  const checkForAuthCode = () => {
    const code = localStorage.getItem('__pkce_auth_code');
    const state = localStorage.getItem('__pkce_state');
    
    if (code && state && model.get('status') === 'pending') {
      if (debug) console.log('[moutils:pkce_flow] Found auth code in localStorage (fallback check):', code.substring(0, 20) + '...');
      
      // Update URL with OAuth parameters to trigger handleUrlChange
      const currentUrl = window.location.pathname;
      const newUrl = currentUrl + '?code=' + encodeURIComponent(code) + '&state=' + encodeURIComponent(state);
      window.history.pushState({}, '', newUrl);
      window.dispatchEvent(new PopStateEvent('popstate'));
    }
  };
  
  // Enhanced fallback for WASM environments: Listen for storage events
  const handleStorageEvent = (event) => {
    if (debug) console.log('[moutils:pkce_flow] Storage event detected:', event.key);
    
    if (event.key === '__pkce_auth_code' || event.key === '__pkce_state') {
      if (debug) console.log('[moutils:pkce_flow] OAuth data storage event detected');
      
      // Small delay to ensure both code and state are stored
      setTimeout(() => {
        const code = localStorage.getItem('__pkce_auth_code');
        const state = localStorage.getItem('__pkce_state');
        
        if (code && state && model.get('status') === 'pending') {
          if (debug) console.log('[moutils:pkce_flow] Processing OAuth callback from storage event');
          
          // Trigger URL change to process the callback
          const currentUrl = window.location.pathname;
          const newUrl = currentUrl + '?code=' + encodeURIComponent(code) + '&state=' + encodeURIComponent(state);
          window.history.pushState({}, '', newUrl);
          window.dispatchEvent(new PopStateEvent('popstate'));
        }
      }, 100);
    }
  };
  
  // Add storage event listener for cross-window communication
  window.addEventListener('storage', handleStorageEvent);
  
  // Check every 1 second for auth code (only while in pending state)
  if (debug) console.log('[moutils:pkce_flow] Starting periodic auth code check (every 1000ms)');
  const authCodeInterval = setInterval(() => {
    if (model.get('status') === 'pending') {
      checkForAuthCode();
    } else {
      clearInterval(authCodeInterval);
      if (debug) console.log('[moutils:pkce_flow] Stopping periodic auth code check');
    }
  }, 1000);
  
  // Listen for token expiration time to trigger storage
  model.on('change:token_expires_in', () => {
    const expiresIn = model.get('token_expires_in');
    const accessToken = model.get('access_token');
    const tokenType = model.get('token_type');
    const refreshToken = model.get('refresh_token');
    const provider = model.get('provider');
    const scopes = model.get('authorized_scopes');
    
    if (accessToken && expiresIn > 0) {
      if (debug) console.log('[moutils:pkce_flow] Storing token with expiration:', expiresIn);
      storeOAuthToken(accessToken, tokenType, refreshToken, expiresIn, provider, scopes);
    }
  });

  function handleUrlChange() {
    const url = window.location.href;
    const urlParams = new URLSearchParams(window.location.search);
    let authCode = urlParams.get('code');
    let state = urlParams.get('state');

    if (debug) {
      console.log('[moutils:pkce_flow] handleUrlChange called');
      console.log('[moutils:pkce_flow] URL:', url);
      console.log('[moutils:pkce_flow] URL params - code:', authCode ? authCode.substring(0, 20) + '...' : 'none');
      console.log('[moutils:pkce_flow] URL params - state:', state ? state.substring(0, 20) + '...' : 'none');
    }

    // PATCH: If not in URL, check localStorage (for popup/new tab flows)
    if ((!authCode || !state)) {
      authCode = localStorage.getItem('__pkce_auth_code');
      state = localStorage.getItem('__pkce_state');
      if (authCode && state) {
        if (debug) console.log('[moutils:pkce_flow] Found code/state in localStorage (popup flow)');
        if (debug) console.log('[moutils:pkce_flow] localStorage code:', authCode.substring(0, 20) + '...');
        if (debug) console.log('[moutils:pkce_flow] localStorage state:', state.substring(0, 20) + '...');
      }
    }

    if (authCode && state) {
      if (debug) {
        console.log('[moutils:pkce_flow] Authorization code:', authCode ? authCode.substring(0, 20) + '...' : 'none');
        console.log('[moutils:pkce_flow] State:', state);
      }

      // Store the authorization code in localStorage as backup
      localStorage.setItem('__pkce_auth_code', authCode);
      localStorage.setItem('__pkce_state', state);

      // Get the stored code verifier from localStorage
      const storedCodeVerifier = localStorage.getItem('__pkce_code_verifier');
      if (debug) {
        console.log('[moutils:pkce_flow] Retrieved code verifier from localStorage:', storedCodeVerifier ? storedCodeVerifier.substring(0, 20) + '...' : 'none');
      }

      // Set the callback URL and code verifier in the model to trigger Python processing
      // If code/state were from localStorage, synthesize a callback URL
      let callbackUrl = url;
      if (!url.includes('code=') && !url.includes('state=')) {
        callbackUrl = window.location.pathname + '?code=' + encodeURIComponent(authCode) + '&state=' + encodeURIComponent(state);
        if (debug) console.log('[moutils:pkce_flow] Synthesized callback URL:', callbackUrl);
      }
      
      if (debug) console.log('[moutils:pkce_flow] Setting handle_callback to:', callbackUrl);
      model.set('handle_callback', callbackUrl);
      
      if (storedCodeVerifier) {
        if (debug) console.log('[moutils:pkce_flow] Setting code_verifier from localStorage');
        model.set('code_verifier', storedCodeVerifier);
      } else {
        if (debug) console.log('[moutils:pkce_flow] No code_verifier found in localStorage');
      }
      
      model.save_changes();
      
      if (debug) console.log('[moutils:pkce_flow] Model changes saved, waiting for Python processing...');

      // Wait a moment for the Python side to process, then clear URL/localStorage
      setTimeout(() => {
        // Check if the Python side processed the callback successfully
        const currentStatus = model.get('status');
        const currentToken = model.get('access_token');
        
        if (debug) console.log('[moutils:pkce_flow] After 1 second - status:', currentStatus, 'token:', currentToken ? currentToken.substring(0, 20) + '...' : 'none');
        
        // If Python side didn't process it, try a fallback approach
        if (currentStatus === 'pending' && !currentToken) {
          if (debug) console.log('[moutils:pkce_flow] Python side didn\'t process callback, trying fallback...');
          // Set the auth code directly in the model
          model.set('authorization_code', authCode);
          model.save_changes();
          
          // Wait another moment and check again
          setTimeout(() => {
            const finalStatus = model.get('status');
            const finalToken = model.get('access_token');
            if (debug) console.log('[moutils:pkce_flow] After fallback - status:', finalStatus, 'token:', finalToken ? finalToken.substring(0, 20) + '...' : 'none');
          }, 1000);
        }
        
        // Clear the URL parameters to prevent re-processing
        const baseUrl = url.split('?')[0];
        window.history.replaceState({}, document.title, baseUrl);
        if (debug) console.log('[moutils:pkce_flow] Cleared URL parameters');

        // Clear the stored state and code verifier
        localStorage.removeItem('__pkce_state');
        localStorage.removeItem('__pkce_code_verifier');
        localStorage.removeItem('__pkce_auth_code');
        if (debug) console.log('[moutils:pkce_flow] Cleared localStorage items');
      }, 1000); // Wait 1 second for Python processing
    } else {
      if (debug) console.log('[moutils:pkce_flow] No auth code or state found in URL or localStorage');
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
      } catch (error) {
        console.error('[moutils:pkce_flow] Error revoking token:', error);
      }
    }

    // Clear stored token data
    clearStoredOAuthToken();
    localStorage.removeItem('__pkce_token'); // Clear legacy token too
    
    // PATCH: Always set hostname after logout
    model.set('hostname', window.location.hostname);
    model.save_changes();
    
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

  // Set the hostname and port from the current location
  const hostname = window.location.hostname;
  const port = window.location.port;
  const href = window.location.href;
  
  if (debug) {
    console.log('[moutils:pkce_flow] Current location:', window.location.href);
    console.log('[moutils:pkce_flow] Raw hostname:', hostname);
    console.log('[moutils:pkce_flow] Raw port:', port);
    console.log('[moutils:pkce_flow] Setting hostname traitlet to:', hostname);
    console.log('[moutils:pkce_flow] Setting port traitlet to:', port);
    console.log('[moutils:pkce_flow] Setting href traitlet to:', href);
  }
  model.set('hostname', hostname);
  model.set('port', port);
  model.set('href', href);
  model.save_changes();
  
  // Check for OAuth callbacks immediately on initialization (for WASM environments)
  setTimeout(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    
    if (code && state) {
      if (debug) console.log('[moutils:pkce_flow] Found OAuth callback on initialization');
      // Trigger URL change handling
      window.dispatchEvent(new PopStateEvent('popstate'));
    } else {
      // Check localStorage for OAuth data (for popup flows)
      const storedCode = localStorage.getItem('__pkce_auth_code');
      const storedState = localStorage.getItem('__pkce_state');
      
      if (storedCode && storedState) {
        if (debug) console.log('[moutils:pkce_flow] Found OAuth data in localStorage on initialization');
        // Trigger URL change handling with synthesized URL
        const newUrl = window.location.pathname + '?code=' + encodeURIComponent(storedCode) + '&state=' + encodeURIComponent(storedState);
        window.history.pushState({}, '', newUrl);
        window.dispatchEvent(new PopStateEvent('popstate'));
      }
    }
  }, 100); // Small delay to ensure model is fully initialized
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
            Redirect to ${providerName}'s login page
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
