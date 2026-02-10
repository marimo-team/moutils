// shell.js — interactive shell widget with rAF-batched streaming output

function render({ model, el }) {
  // === Build DOM ===
  const container = document.createElement("div");
  container.className = "shell-widget";
  container.dataset.theme = model.get("theme") || "dark";

  const terminal = document.createElement("div");
  terminal.className = "shell-terminal";

  const output = document.createElement("pre");
  output.className = "shell-output";

  // Toolbar (overlays top-right of terminal)
  const toolbar = document.createElement("div");
  toolbar.className = "shell-toolbar";

  const runIconBtn = document.createElement("button");
  runIconBtn.className = "shell-btn shell-btn-run";
  runIconBtn.textContent = "\u25B6";
  runIconBtn.setAttribute("aria-label", "Run command");

  const menuBtn = document.createElement("button");
  menuBtn.className = "shell-btn shell-btn-menu";
  menuBtn.textContent = "\u2630";
  menuBtn.setAttribute("aria-haspopup", "menu");
  menuBtn.setAttribute("aria-label", "Toggle command menu");

  // Dropdown menu panel
  const menu = document.createElement("div");
  menu.className = "shell-menu";
  menu.setAttribute("popover", "manual");

  const menuRunBtn = document.createElement("button");
  menuRunBtn.className = "shell-menu-item";
  menuRunBtn.textContent = "\u25B6 Execute";

  const sep = document.createElement("div");
  sep.className = "shell-menu-sep";

  const inputRow = document.createElement("div");
  inputRow.className = "shell-input-row";

  const inputField = document.createElement("input");
  inputField.type = "text";
  inputField.className = "shell-input";
  inputField.placeholder = "stdin\u2026";

  const sendBtn = document.createElement("button");
  sendBtn.className = "shell-btn-send";
  sendBtn.textContent = "Send";

  const terminateBtn = document.createElement("button");
  terminateBtn.className = "shell-menu-item shell-btn-terminate";
  terminateBtn.textContent = "\uD83D\uDED1 Terminate";

  const killBtn = document.createElement("button");
  killBtn.className = "shell-menu-item shell-btn-kill";
  killBtn.textContent = "\u274C Kill";

  // Assemble
  inputRow.append(inputField, sendBtn);
  menu.append(menuRunBtn, sep, inputRow, terminateBtn, killBtn);
  toolbar.append(runIconBtn, menuBtn, menu);
  terminal.append(output, toolbar);
  container.append(terminal);
  el.appendChild(container);

  // === Theme sync ===
  model.on("change:theme", () => {
    container.dataset.theme = model.get("theme") || "dark";
  });

  // === Stream buffer (rAF batching for smooth output) ===
  const buf = [];
  let scheduled = false;

  function write(chunk) {
    buf.push(chunk);
    if (!scheduled) {
      scheduled = true;
      requestAnimationFrame(() => {
        scheduled = false;
        output.textContent += buf.join("");
        buf.length = 0;
        output.scrollTop = output.scrollHeight;
      });
    }
  }

  // === UI state helper ===
  function setRunning(running) {
    runIconBtn.disabled = running;
    menuRunBtn.disabled = running;
    terminateBtn.disabled = !running;
    killBtn.disabled = !running;
  }
  setRunning(false);

  // === Popover menu ===
  function positionMenu() {
    const r = menuBtn.getBoundingClientRect();
    const w = menu.offsetWidth || 200;
    const margin = 8;
    let left = Math.max(margin, Math.min(r.right - w, window.innerWidth - w - margin));
    menu.style.left = `${Math.round(left)}px`;
    menu.style.top = `${Math.round(r.bottom + 4)}px`;
  }

  function closeMenu() {
    if (menu.matches(":popover-open")) menu.hidePopover();
  }

  menuBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    if (menu.matches(":popover-open")) {
      menu.hidePopover();
    } else {
      positionMenu();
      menu.showPopover();
    }
  });

  document.addEventListener("mousedown", (e) => {
    if (
      menu.matches(":popover-open") &&
      !menu.contains(e.target) &&
      e.target !== menuBtn
    ) {
      closeMenu();
    }
  });

  menu.addEventListener("mousedown", (e) => e.stopPropagation());

  // === Actions (Frontend -> Backend) ===
  function execute() {
    closeMenu();
    output.textContent = "";
    setRunning(true);
    model.send({ type: "execute" });
  }

  function sendInput() {
    const text = inputField.value.trim();
    if (!text) return;
    model.send({ type: "input", data: inputField.value });
    inputField.value = "";
  }

  runIconBtn.addEventListener("click", execute);
  menuRunBtn.addEventListener("click", execute);

  terminateBtn.addEventListener("click", () => {
    closeMenu();
    model.send({ type: "terminate" });
  });

  killBtn.addEventListener("click", () => {
    closeMenu();
    model.send({ type: "kill" });
  });

  sendBtn.addEventListener("click", sendInput);
  inputField.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendInput();
  });

  // === Messages (Backend -> Frontend) ===
  model.on("msg:custom", (msg) => {
    switch (msg.type) {
      case "started":
        setRunning(true);
        write(`$ ${model.get("command")}\n`);
        write(`pid=${msg.pid}${msg.pgid ? ` pgid=${msg.pgid}` : ""}\n\n`);
        break;

      case "output":
        write(msg.data);
        break;

      case "completed":
        setRunning(false);
        write(
          msg.returncode === 0
            ? "\n\u2705 Done"
            : `\n\u274C Exit code ${msg.returncode}`
        );
        break;

      case "terminated":
        setRunning(false);
        write("\n\uD83D\uDED1 Terminated (SIGTERM)");
        break;

      case "killed":
        setRunning(false);
        write("\n\u274C Killed (SIGKILL)");
        break;

      case "error":
        setRunning(false);
        write(`\n\uD83D\uDCA5 Error: ${msg.error}`);
        break;

      case "not_running":
        write("\n\u26A0\uFE0F No running process");
        break;
    }
  });
}

export default { render };
