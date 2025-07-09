# Install local moutils wheel using top-level await
import micropip

print("🔄 Attempting to install local moutils wheel...")
try:
    await micropip.install("http://localhost:8088/moutils-latest.whl")
    moutils_installed = True
    print("✅ Installed local moutils wheel 🛞")
except Exception as e:
    print(f"⚠️  Failed to install local wheel: {e}")
    print("📦 Falling back to PyPI version")
    try:
        await micropip.install("moutils")
        moutils_installed = True
        print("✅ Installed moutils from PyPI 🌐")
    except Exception as e2:
        print(f"❌ Failed to install from PyPI: {e2}")
        moutils_installed = False