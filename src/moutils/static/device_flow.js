/**
 * @typedef {{
 *   provider: string,
 *   provider_name: string,
 *   client_id: string,
 *   icon: string,
 *   verification_uri: string,
 *   device_code: string,
 *   user_code: string,
 *   poll_interval: number,
 *   expires_in: number,
 *   access_token: string,
 *   token_type: string,
 *   refresh_token: string,
 *   scopes: string[],
 *   status: 'not_started' | 'initiating' | 'pending' | 'success' | 'error',
 *   error_message: string,
 *   device_code_url: string,
 *   token_url: string,
 *   start_auth: boolean,
 *   check_token: boolean
 * }} Model
 */

const debug = localStorage.getItem('moutils-debug') === 'true';

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
 * Safely set href on an anchor element
 * @param {HTMLAnchorElement | null} element
 * @param {string} href
 */
function setHref(element, href) {
  if (element) {
    element.href = href;
  }
}

/**
 * Render function for the DeviceFlow widget
 * @param {{ model: any, el: HTMLElement }} options
 */
function render({ model, el }) {
  // Variables to store flow data
  let expiryTimer = null;
  let pollTimer = null;

  // Initialize UI elements
  el.innerHTML = createDeviceFlowHTML(
    model.get('provider'),
    model.get('provider_name'),
    model.get('client_id'),
    model.get('icon'),
    model.get('verification_uri')
  );

  // Get UI elements with JSDoc type casts
  const startAuthBtn = /** @type {HTMLButtonElement | null} */ (el.querySelector('#startAuthBtn'));
  const initialSection = /** @type {HTMLElement | null} */ (el.querySelector('#initialSection'));
  const verificationSection = /** @type {HTMLElement | null} */ (el.querySelector('#verificationSection'));
  const tokenSection = /** @type {HTMLElement | null} */ (el.querySelector('#tokenSection'));
  const userCodeElement = /** @type {HTMLElement | null} */ (el.querySelector('#userCode'));
  const verificationLink = /** @type {HTMLAnchorElement | null} */ (el.querySelector('#verificationLink'));
  const statusMessage = /** @type {HTMLElement | null} */ (el.querySelector('#statusMessage'));
  const startNewAuthBtn = /** @type {HTMLButtonElement | null} */ (el.querySelector('#tokenSection #startNewAuthBtn'));

  if (
    !startAuthBtn ||
    !initialSection ||
    !verificationSection ||
    !tokenSection ||
    !userCodeElement ||
    !verificationLink ||
    !statusMessage ||
    !startNewAuthBtn
  ) {
    throw new Error('Missing required UI elements');
  }

  // Set up event listeners
  if (startAuthBtn) {
    startAuthBtn.addEventListener('click', startDeviceFlow);
  }

  if (startNewAuthBtn) {
    startNewAuthBtn.addEventListener('click', startDeviceFlow);
  }

  const copyCodeBtn = /** @type {HTMLButtonElement | null} */ (el.querySelector('#copyCodeBtn'));
  if (copyCodeBtn) {
    copyCodeBtn.addEventListener('click', copyUserCode);
  }

  // Update UI based on model changes
  model.on('change:status', () => {
    const status = model.get('status');
    if (debug) console.log('[moutils:device_flow] Status changed:', status);

    // Clear polling timer on status change
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }

    if (status === 'error') {
      // If status is 'error', we assume the UI (which section is visible, button states)
      // has been appropriately set by the function that encountered the error.
      // The 'change:error_message' listener will handle displaying the error text.
      // This block intentionally does not change section visibility for 'error' status.
      return;
    }

    // For non-error states, manage section visibility and button states.
    setDisplayStyle(initialSection, 'none');
    setDisplayStyle(verificationSection, 'none');
    setDisplayStyle(tokenSection, 'none');
    if (startAuthBtn) startAuthBtn.disabled = true; // Disable by default, enable specifically for relevant states

    if (status === 'not_started') {
      setDisplayStyle(initialSection, 'block');
      if (startAuthBtn) {
        setHtmlContent(
          startAuthBtn,
          `<span class="btn-text">Connect</span> ${model.get('icon') ? `<i class="${model.get('icon')}"></i>` : ''}`
        );
        startAuthBtn.disabled = false;
      }
    } else if (status === 'initiating') {
      setDisplayStyle(initialSection, 'block');
      if (startAuthBtn) {
        setHtmlContent(startAuthBtn, '<span class="spinner"></span> <span class="btn-text">Initiating...</span>');
        // Button remains disabled (as per default a few lines above)
      }
    } else if (status === 'pending') {
      setDisplayStyle(verificationSection, 'block');
      // Start countdown timer for expiry
      startExpiryCountdown(model.get('expires_in'));
      // Update user code and verification URI
      setTextContent(userCodeElement, model.get('user_code'));
      setHref(verificationLink, model.get('verification_uri'));
      setHtmlContent(statusMessage, '<p>Waiting for authorization...</p>');

      // Start polling for token status
      startPollingForToken();
    } else if (status === 'success') {
      // Clear any timers
      if (expiryTimer) clearInterval(expiryTimer);
      setDisplayStyle(tokenSection, 'block');
    }
  });

  model.on('change:user_code', () => {
    setTextContent(userCodeElement, model.get('user_code'));
  });

  model.on('change:error_message', () => {
    const errorMessage = model.get('error_message');
    if (debug) console.log('[moutils:device_flow] Error message changed:', errorMessage);
    if (statusMessage && errorMessage) {
      setHtmlContent(statusMessage, `<p class="error">${errorMessage}</p>`);
    }
  });

  /**
   * Start the device flow authentication process
   */
  function startDeviceFlow() {
    if (debug) console.log('[moutils:device_flow] Starting device flow');

    // Reset UI
    model.set('error_message', ''); // Clear previous errors

    // Clear any existing timers
    if (expiryTimer) clearInterval(expiryTimer);
    if (pollTimer) clearInterval(pollTimer);

    // Trigger Python-side flow by setting start_auth to true
    model.set('start_auth', true);
    model.save_changes();
  }

  /**
   * Copy the user code to the clipboard
   */
  function copyUserCode() {
    const userCode = model.get('user_code');
    if (!userCode) return;

    navigator.clipboard
      .writeText(userCode)
      .then(() => {
        const copyBtn = el.querySelector('#copyCodeBtn');
        if (copyBtn) {
          copyBtn.classList.add('copied');
          setTimeout(() => {
            copyBtn.classList.remove('copied');
          }, 1500);
        }
      })
      .catch((err) => {
        if (debug) console.error('[moutils:device_flow] Failed to copy:', err);
      });
  }

  /**
   * Start polling for token status
   */
  function startPollingForToken() {
    // Clear any existing polling timer
    if (pollTimer) clearInterval(pollTimer);

    // Start polling at the interval specified by the server
    const interval = (model.get('poll_interval') || 5) * 1000;

    // Poll immediately once
    checkTokenStatus();

    // Then set up interval polling
    pollTimer = setInterval(checkTokenStatus, interval);

    // Also update polling interval when it changes
    model.on('change:poll_interval', () => {
      if (pollTimer) {
        clearInterval(pollTimer);
        const newInterval = model.get('poll_interval') * 1000;
        pollTimer = setInterval(checkTokenStatus, newInterval);
      }
    });
  }

  /**
   * Check token status by signaling the Python backend
   */
  function checkTokenStatus() {
    // Only check if we're still in 'pending' status
    if (model.get('status') === 'pending') {
      // Tell the Python side to check token status by incrementing the counter
      model.set('check_token', model.get('check_token') + 1);
      model.save_changes();
    } else {
      // If not pending, stop polling
      if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
      }
    }
  }

  /**
   * Start the countdown timer for code expiration
   * @param {number} seconds
   */
  function startExpiryCountdown(seconds) {
    // Clear any existing timer
    if (expiryTimer) clearInterval(expiryTimer);

    const expiryElement = /** @type {HTMLElement | null} */ (el.querySelector('#expiryTimer'));
    if (!expiryElement) return;

    // Update timer text
    function updateTimer(secondsLeft) {
      const minutes = Math.floor(secondsLeft / 60);
      const secs = secondsLeft % 60;
      setTextContent(expiryElement, `Code expires in: ${minutes}:${secs < 10 ? '0' : ''}${secs}`);

      if (secondsLeft <= 0) {
        clearInterval(expiryTimer);
        setTextContent(expiryElement, 'Code expired. Please try again.');
      }
    }

    // Initial update
    updateTimer(seconds);

    // Start countdown
    let remainingSeconds = seconds;
    expiryTimer = setInterval(() => {
      remainingSeconds--;
      updateTimer(remainingSeconds);
    }, 1000);
  }

  // Return cleanup function
  return () => {
    if (expiryTimer) clearInterval(expiryTimer);
    if (pollTimer) clearInterval(pollTimer);

    if (startAuthBtn) {
      startAuthBtn.removeEventListener('click', startDeviceFlow);
    }

    if (startNewAuthBtn) {
      startNewAuthBtn.removeEventListener('click', startDeviceFlow);
    }

    if (copyCodeBtn) {
      copyCodeBtn.removeEventListener('click', copyUserCode);
    }

    // Clean up listeners
    model.off('change:poll_interval');
  };
}

/**
 * Initialize the widget
 * @param {{ model: any }} options
 */
function initialize({ model }) {
  if (debug) console.log('[moutils:device_flow] Initializing device flow widget');

  // Add Font Awesome kit
  const url = 'https://kit.fontawesome.com/29a456ae19.js';
  const alreadyAdded = document.querySelector(`script[src="${url}"]`);
  if (!alreadyAdded) {
    const fontAwesomeScript = document.createElement('script');
    fontAwesomeScript.src = url;
    fontAwesomeScript.crossOrigin = 'anonymous';
    document.head.appendChild(fontAwesomeScript);
  }
}

/**
 * Create the HTML for the device flow
 * @param {string} provider
 * @param {string} providerName
 * @param {string} clientId
 * @param {string} icon
 * @param {string} verificationUri
 * @returns {string}
 */
function createDeviceFlowHTML(provider, providerName, clientId, icon, verificationUri) {
  return `
    <div class="mo-device-flow" data-provider="${provider}">
      <div class="container">
        <h1 class="title">${providerName} Authentication</h1>

        <div id="initialSection" class="section">
          <button id="startAuthBtn" class="btn btn-primary">
            <span class="btn-text">Connect</span>
            ${icon ? `<i class="${icon}"></i>` : ''}
          </button>
        </div>

        <div id="verificationSection" class="section verification-section">
          <h2 class="section-title">Verify your device</h2>
          <p class="instruction-text">Enter this code on ${providerName}:</p>
          <div class="user-code-container">
            <div id="userCode" class="user-code"></div>
            <button id="copyCodeBtn" class="copy-btn" title="Copy to clipboard">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15V5a2 2 0 0 1 2-2h8"></path>
              </svg>
            </button>
          </div>
          <div id="expiryTimer" class="expiry-timer"></div>

          <div class="instructions">
            <ol class="steps">
              <li>Go to <a id="verificationLink" href="${verificationUri}" target="_blank" class="verify-link">${verificationUri}</a></li>
              <li>Enter the code shown above</li>
              <li>Complete authorization</li>
            </ol>
          </div>

          <div id="statusMessage" class="status-message"></div>
        </div>

        <div id="tokenSection" class="section token-section">
          <div class="success-container">
            <h2 class="section-title success">Authentication Successful</h2>
            <p class="success-text">Your device is now connected to ${providerName}.</p>
            <button id="startNewAuthBtn" class="link-button">
              Logout ${icon ? `<i class="${icon}"></i>` : ''}
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
}

export default { render, initialize };
