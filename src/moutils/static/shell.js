function render({ model, el }) {
  const container = document.createElement('div');
  const runBtn = document.createElement('button');
  const output = document.createElement('pre');
  const terminateBtn = document.createElement('button');
  const killBtn = document.createElement('button');

  // Styling
  container.style.cssText = `
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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

  container.appendChild(controls);
  container.appendChild(output);
  el.appendChild(container);

  // Run button
  runBtn.addEventListener('click', () => {
    runBtn.disabled = true;
    runBtn.textContent = '⏳ Running...';
    runBtn.style.background = '#666';
    output.textContent = `$ ${model.get('command')}\n`;
    model.send('execute_command');
  });

  // Terminate button
  terminateBtn.addEventListener('click', () => {
    model.send('terminate_process');
    output.textContent += '\n\n🛑 Terminate requested...';
  });

  // Kill button
  killBtn.addEventListener('click', () => {
    model.send('kill_process');
    output.textContent += '\n\n❌ Kill requested...';
  });

// Handle output updates (best option: robust states + feedback)
model.on('msg:custom', (msg) => {
  switch (msg.type) {
    case 'started':
      // A process just started: enable control buttons
      runBtn.disabled = true;
      terminateBtn.disabled = false;
      killBtn.disabled = false;
      output.textContent += `\n\n🚀 Started (pid=${msg.pid}${msg.pgid ? `, pgid=${msg.pgid}` : ''})`;
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
