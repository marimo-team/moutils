function render({ model, el }) {
  const container = document.createElement('div');
  const button = document.createElement('button');
  const output = document.createElement('pre');

  // Styling
  container.style.cssText = `
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;

  button.style.cssText = `
        background: #007acc;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
        font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
        font-size: 13px;
        margin-bottom: 12px;
        transition: background-color 0.2s ease;
    `;

  button.onmouseover = () => (button.style.background = '#005a9e');
  button.onmouseout = () => (button.style.background = '#007acc');

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
    button.textContent = `▶ ${cmd}`;
  };

  updateButtonText();

  container.appendChild(button);
  container.appendChild(output);
  el.appendChild(container);

  // Handle button click
  button.addEventListener('click', () => {
    button.disabled = true;
    button.textContent = '⏳ Running...';
    button.style.background = '#666';
    output.textContent = `$ ${model.get('command')}\n`;
    model.send('execute_command');
  });

  // Handle output updates
  model.on('msg:custom', (msg) => {
    switch (msg.type) {
      case 'output':
        output.textContent += msg.data;
        output.scrollTop = output.scrollHeight;
        break;

      case 'completed':
        button.disabled = false;
        button.style.background = '#007acc';
        updateButtonText();

        const statusMsg =
          msg.returncode === 0
            ? '\n\n✅ Process completed successfully'
            : `\n\n❌ Process exited with code ${msg.returncode}`;
        output.textContent += statusMsg;
        break;

      case 'error':
        button.disabled = false;
        button.style.background = '#d73a49';
        updateButtonText();
        output.textContent += `\n\n💥 Error: ${msg.error}`;
        break;
    }
  });

  // Update button text when command changes
  model.on('change:command', updateButtonText);
}

export default { render };
