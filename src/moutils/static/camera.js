/** @typedef {{ image_data: string, width: number, height: number, enabled: boolean }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  let stream = null;

  const container = document.createElement('div');
  container.className = 'moutils-camera';

  const video = document.createElement('video');
  video.autoplay = true;
  video.playsInline = true;
  video.muted = true;

  const canvas = document.createElement('canvas');
  canvas.style.display = 'none';

  const captureBtn = document.createElement('button');
  captureBtn.textContent = 'Capture';
  captureBtn.className = 'moutils-camera-btn';
  captureBtn.disabled = true;

  const status = document.createElement('div');
  status.className = 'moutils-camera-status';

  container.appendChild(video);
  container.appendChild(canvas);
  container.appendChild(captureBtn);
  container.appendChild(status);
  el.appendChild(container);

  async function startCamera() {
    try {
      const w = model.get('width') || 640;
      const h = model.get('height') || 480;

      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: w }, height: { ideal: h } },
      });
      video.srcObject = stream;
      video.style.display = 'block';
      captureBtn.disabled = false;
      status.textContent = '';
      if (debug) console.log('[moutils:camera] Camera started');
    } catch (err) {
      if (debug) console.error('[moutils:camera] Error:', err);
      status.textContent = 'Camera error: ' + err.message;
      captureBtn.disabled = true;
    }
  }

  function stopCamera() {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    video.srcObject = null;
    video.style.display = 'none';
    captureBtn.disabled = true;
    if (debug) console.log('[moutils:camera] Camera stopped');
  }

  function capture() {
    const w = model.get('width') || 640;
    const h = model.get('height') || 480;
    canvas.width = w;
    canvas.height = h;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, w, h);

    const dataUrl = canvas.toDataURL('image/png');
    if (debug) console.log('[moutils:camera] Captured image, length:', dataUrl.length);
    model.set('image_data', dataUrl);
    model.save_changes();
  }

  captureBtn.addEventListener('click', capture);

  model.on('change:enabled', () => {
    if (model.get('enabled')) {
      startCamera();
    } else {
      stopCamera();
    }
  });

  if (model.get('enabled')) {
    startCamera();
  }

  return () => {
    captureBtn.removeEventListener('click', capture);
    stopCamera();
  };
}

function initialize({ model }) {
  if (debug) console.log('[moutils:camera] Initializing camera widget');
}

export default { render, initialize };
