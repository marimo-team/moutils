# Install local moutils wheel using top-level await
import micropip
try:
    await micropip.install("http://localhost:8088/moutils-latest.whl")
    print("✅ Installed local moutils wheel")
    moutils_installed = True
except Exception as e:
    print(f"⚠️  Failed to install local wheel: {e}")
    print("📦 Falling back to PyPI version")
    moutils_installed = False 