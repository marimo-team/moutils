/** @typedef {{ storage_type: 'local' | 'session', key: string, data: any }} Model */

const debug = localStorage.getItem('moutils-debug') === 'true';

function isStorageAvailable(storage) {
  try {
    const test = '__storage_test__';
    storage.setItem(test, test);
    storage.removeItem(test);
    return true;
  } catch (e) {
    return false;
  }
}

function getStorageQuota(storage) {
  try {
    let total = 0;
    for (let i = 0; i < storage.length; i++) {
      const key = storage.key(i);
      const value = storage.getItem(key);
      total += (key.length + value.length) * 2; // UTF-16 characters are 2 bytes each
    }
    return {
      used: total,
      max: 5 * 1024 * 1024, // 5MB is a safe estimate for most browsers
      available: Math.max(0, 5 * 1024 * 1024 - total),
    };
  } catch (e) {
    console.error('[moutils:storage] Error calculating storage quota:', e);
    return null;
  }
}

async function getStorageData(model, storage, key) {
  try {
    if (debug) console.log('[moutils:storage] Getting storage data for key', key);

    if (!key) return;

    if (!isStorageAvailable(storage)) {
      console.error('[moutils:storage] Storage is not available');
      return;
    }

    try {
      const value = storage.getItem(key);
      if (value === null) {
        model.set('data', null);
      } else {
        try {
          model.set('data', JSON.parse(value));
        } catch {
          model.set('data', value);
        }
      }
      model.save_changes();
    } catch (error) {
      console.error('[moutils:storage] Storage retrieval failed for key:', key, error);
    }
  } catch (error) {
    console.error('[moutils:storage] Storage retrieval failed:', error);
  }
}

/** @type {import("npm:@anywidget/types").Render<Model>} */
function render({ model, el }) {
  let isUpdating = false;

  async function setStorageData(storage, key, value) {
    if (isUpdating) return; // Prevent race conditions
    isUpdating = true;

    try {
      if (debug) console.log('[moutils:storage] Setting storage data for key', key, value);

      if (!key) return;

      if (!isStorageAvailable(storage)) {
        console.error('[moutils:storage] Storage is not available');
        return;
      }

      if (value === null || value === undefined) {
        storage.removeItem(key);
      } else {
        const serialized = JSON.stringify(value);
        const byteSize = new Blob([serialized]).size;
        const quota = getStorageQuota(storage);

        if (quota && byteSize > quota.available) {
          console.error(
            '[moutils:storage] Insufficient storage space. Available:',
            quota.available,
            'Required:',
            byteSize
          );
          return;
        }

        try {
          storage.setItem(key, serialized);
        } catch (e) {
          if (e.name === 'QuotaExceededError' || e.name === 'NS_ERROR_DOM_QUOTA_REACHED') {
            console.error('[moutils:storage] Storage quota exceeded');
            // Attempt to free up space by removing old items
            const oldKey = storage.key(0);
            if (oldKey) {
              storage.removeItem(oldKey);
              try {
                storage.setItem(key, serialized);
              } catch (e) {
                console.error('[moutils:storage] Still unable to store data after cleanup');
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('[moutils:storage] Storage setting failed:', error);
    } finally {
      isUpdating = false;
    }
  }

  model.on('change:data', () => {
    const storageType = model.get('storage_type');
    const key = model.get('key');
    const data = model.get('data');
    const storage = storageType === 'local' ? localStorage : sessionStorage;

    setStorageData(storage, key, data);
  });

  model.on('change:key', () => {
    const storageType = model.get('storage_type');
    const key = model.get('key');
    const storage = storageType === 'local' ? localStorage : sessionStorage;

    getStorageData(model, storage, key);
  });

  model.on('change:storage_type', () => {
    const storageType = model.get('storage_type');
    const key = model.get('key');
    const storage = storageType === 'local' ? localStorage : sessionStorage;

    getStorageData(model, storage, key);
  });

  return () => {};
}

function initialize({ model }) {
  if (debug) console.log('[moutils:storage] Initializing storage item widget');

  const storageType = model.get('storage_type');
  const key = model.get('key');
  const storage = storageType === 'local' ? localStorage : sessionStorage;

  getStorageData(model, storage, key);
}

export default { render, initialize };
