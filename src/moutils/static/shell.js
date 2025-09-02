function render({ model, el }) {
  const container = document.createElement('div');
  const runBtn = document.createElement('button');
  const output = document.createElement('pre');
  const terminateBtn = document.createElement('button');
  const killBtn = document.createElement('button');

  const toolbar = document.createElement('div');
  const menuBtn = document.createElement('button');
  const menuPanel = document.createElement('div');
  const terminalWrapper = document.createElement('div');

  // a11y + base UI
  terminalWrapper.style.cssText = `
    position: relative; /* anchors toolbar absolutely without taking space */
  `;
  toolbar.style.cssText = `
    position: absolute; /* overlay inside the terminal */
    top: 0px;          /* lower the button inside the terminal */
    right: 0px;        /* keep it in the top-right corner */
    display: inline-flex;
    align-items: center;
    z-index: 2;         /* above terminal content */
  `;

  menuBtn.type = 'button';
  menuBtn.setAttribute('aria-haspopup', 'menu');
  menuBtn.setAttribute('aria-label', 'Toggle command menu');
  menuBtn.textContent = '☰';

  menuBtn.style.cssText = `
    background:#2d2d2d;color:#fff;border:none;
    width:28px;height:28px; /* compact */
    padding:0; border-radius:8px;
    cursor:pointer;font-size:14px;line-height:1;
    display:inline-flex;align-items:center;justify-content:center;
  `;

  menuBtn.onmouseover = () => (menuBtn.style.background = '#444');
  menuBtn.onmouseout  = () => (menuBtn.style.background = '#2d2d2d');

  // Make the panel a Popover (top layer avoids clipping/overflow)
  menuPanel.setAttribute('popover', 'manual'); // manual to avoid reopen-on-click race
  menuPanel.style.cssText = `
    position: fixed;
    background:#1f1f1f; border:1px solid #333; border-radius:10px;
    padding:10px; min-width:200px; /* compact menu */
    box-shadow:0 8px 24px rgba(0,0,0,.3);
    z-index: 1000;
  `;

  // Input field and send button
  const inputWrapper = document.createElement('div');
  inputWrapper.style.cssText = 'display: flex; gap: 8px; margin-bottom: 8px;';

  const inputField = document.createElement('input');
  inputField.type = 'text';
  inputField.placeholder = 'Send input to process...';
  inputField.style.cssText = `
    flex: 1;
    padding: 6px 10px;
    border-radius: 6px;
    border: 1px solid #333;
    font-size: 12px;
    background: #222;
    color: #fff;
  `;

  const sendBtn = document.createElement('button');
  sendBtn.textContent = 'Send';
  sendBtn.style.cssText = `
    background: #28a745;
    color: white;
    border: none;
    padding: 6px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    font-family: 'SF Mono', monospace;
    transition: background-color 0.2s ease;
  `;
  sendBtn.onmouseover = () => (sendBtn.style.background = '#218838');
  sendBtn.onmouseout = () => (sendBtn.style.background = '#28a745');


  sendBtn.onclick = () => {
    const text = inputField.value;
    if (text.trim() !== "") {
      model.send({type: "input", data: text});
      inputField.value = "";
    }
  };

  // Allow sending input with Enter key for better UX
  inputField.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      sendBtn.click();
    }
  });

  inputWrapper.appendChild(inputField);
  inputWrapper.appendChild(sendBtn);

  // mount toolbar (panel vacío por ahora)
  toolbar.appendChild(menuBtn);
  toolbar.appendChild(menuPanel);

  // Styling
  container.style.cssText = `
        font-family: -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        Roboto, sans-serif;
    `;

  const styleButton = (btn, bg, hover) => {
    btn.style.cssText = `
      background: ${bg};
      color: white;
      border: none;
      padding: 6px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-family: 'SF Mono', monospace;
      font-size: 12px;
      margin-right: 8px;
      margin-bottom: 12px;
      transition: background-color 0.2s ease;
    `;
    btn.onmouseover = () => (btn.style.background = hover);
    btn.onmouseout = () => (btn.style.background = bg);
  };

  styleButton(runBtn, '#007acc', '#005a9e');
  styleButton(terminateBtn, '#253a97ff', '#152158ff');
  styleButton(killBtn, '#d73a49', '#a52a32');

  terminateBtn.textContent = '🛑 Terminate';
  killBtn.textContent = '❌ Kill';

  output.style.cssText = `
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 12px;
        border-radius: 6px;
        font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
        font-size: 12px;
        line-height: 1.4;
        max-height: 400px;
        overflow-y: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        border: 1px solid #333;
        min-height: 40px;
    `;

  const updateButtonText = () => {
    const cmd = model.get('command');
    runBtn.textContent = `▶ Execute`;
  };

  updateButtonText();

  const controls = document.createElement('div');
  controls.appendChild(runBtn);
  controls.appendChild(terminateBtn);
  controls.appendChild(killBtn);

  

  // Move action buttons into the dropdown panel instead of showing them inline
  menuPanel.appendChild(runBtn);
  menuPanel.appendChild(inputWrapper);
  menuPanel.appendChild(terminateBtn);
  menuPanel.appendChild(killBtn);

  [runBtn, terminateBtn, killBtn].forEach(btn => {
    btn.style.width = '100%'; btn.style.margin = '0 0 8px 0'; btn.style.textAlign = 'left';
  });

  // Mount terminal view first to occupy the top space; toolbar overlays inside it
  terminalWrapper.appendChild(output);
  terminalWrapper.appendChild(toolbar);
  container.appendChild(terminalWrapper);
  el.appendChild(container);


  const positionPopoverNearButton = () => {
    const r = menuBtn.getBoundingClientRect();

    const panelWidth = measurePanelWidth(menuPanel);

    let left = r.right - panelWidth;

    const style = window.getComputedStyle(menuPanel);
    const isFixed = style.position === 'fixed';

    const margin = 8;
    const maxLeft = window.innerWidth - panelWidth - margin;
    if (left < margin) left = margin;
    if (left > maxLeft) left = maxLeft;

    let top = r.bottom;

    menuPanel.style.left = `${Math.round(left)}px`;
    menuPanel.style.top  = `${Math.round(top)}px`;
  };
  
/**
 * Measure the panel's rendered width even if it's hidden with display:none.
 * Returns a number in CSS pixels.
 */
function measurePanelWidth(el) {
  // If visible and laid out, use offsetWidth
  if (el.offsetWidth) return el.offsetWidth;

  // Temporarily reveal to measure without flashing
  const prevDisplay = el.style.display;
  const prevVisibility = el.style.visibility;

  // Ensure it renders offscreen without affecting layout
  el.style.visibility = 'hidden';
  el.style.display = 'block';

  const w = el.offsetWidth;

  // Restore previous styles
  el.style.display = prevDisplay;
  el.style.visibility = prevVisibility;

  return w;
}

  menuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    if (menuPanel.matches(':popover-open')) {
      menuPanel.hidePopover();
    } else {
      positionPopoverNearButton();
      menuPanel.showPopover();
    }
  });

  document.addEventListener('mousedown', (e) => {
    if (
      menuPanel.matches(':popover-open') &&
      !menuPanel.contains(e.target) &&
      e.target !== menuBtn
    ) {
      menuPanel.hidePopover();
    }
  });

  // Prevent clicks inside the menu from bubbling to the document handler (which closes the menu)
  ['pointerdown', 'mousedown', 'click', 'touchstart'].forEach((evt) => {
    menuPanel.addEventListener(
      evt,
      (e) => { e.stopPropagation(); },
      false
    );
  });


  // Run button
  runBtn.addEventListener('click', () => {
    if (menuPanel.matches(':popover-open')) menuPanel.hidePopover();
    runBtn.disabled = true;
    runBtn.textContent = '⏳ Running...';
    runBtn.style.background = '#666';
    output.textContent = `$ ${model.get('command')}\n`;
    model.send('execute_command');
  });

  // Terminate button
  terminateBtn.addEventListener('click', () => {
    if (menuPanel.matches(':popover-open')) menuPanel.hidePopover();
    model.send('terminate_process');
    output.textContent += '\n\n🛑 Terminate requested...';
  });

  // Kill button
  killBtn.addEventListener('click', () => {
    if (menuPanel.matches(':popover-open')) menuPanel.hidePopover();
    model.send('kill_process');
    output.textContent += '\n\n❌ Kill requested...';
  });

// Handle output updates (best option: robust states + feedback)
model.on('msg:custom', (msg) => {
  switch (msg.type) {
    case 'started':
      // Process just started: enable/disable controls accordingly and show header
      runBtn.disabled = true;
      terminateBtn.disabled = false;
      killBtn.disabled = false;
      output.textContent += `Started in (pid=${msg.pid}${msg.pgid ? `, pgid=${msg.pgid}` : ''})\n\n`;
      output.scrollTop = output.scrollHeight;
      break;

    case 'output':
      output.textContent += msg.data;
      output.scrollTop = output.scrollHeight;
      break;

    case 'terminated':
      // Process terminated via SIGTERM
      terminateBtn.disabled = true;
      killBtn.disabled = true;
      runBtn.disabled = false;
      runBtn.style.background = '#007acc';
      updateButtonText();
      output.textContent += '\n\n🛑 Process terminated (SIGTERM)';
      break;

    case 'killed':
      // Process killed via SIGKILL
      terminateBtn.disabled = true;
      killBtn.disabled = true;
      runBtn.disabled = false;
      runBtn.style.background = '#007acc';
      updateButtonText();
      output.textContent += '\n\n❌ Process killed (SIGKILL)';
      break;

    case 'completed':
      // Natural completion
      terminateBtn.disabled = true;
      killBtn.disabled = true;
      runBtn.disabled = false;
      runBtn.style.background = '#007acc';
      updateButtonText();
      {
        const statusMsg =
          msg.returncode === 0
            ? '\n\n✅ Process completed successfully'
            : `\n\n❌ Process exited with code ${msg.returncode}`;
        output.textContent += statusMsg;
      }
      break;


    case 'error':
      // Error path
      terminateBtn.disabled = true;
      killBtn.disabled = true;
      runBtn.disabled = false;
      runBtn.style.background = '#d73a49';
      updateButtonText();
      output.textContent += `\n\n💥 Error: ${msg.error}`;
      break;
  }


  // Always keep the output scrolled to bottom
  output.scrollTop = output.scrollHeight;
});

  // Update button text when command changes
  model.on('change:command', updateButtonText);
}

export default { render };
