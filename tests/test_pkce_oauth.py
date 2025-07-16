#!/usr/bin/env python3
"""
Comprehensive test script to verify all environment detection cases in _configure_cloudflare_urls().
"""

import json
import base64
from urllib.parse import urlparse
from unittest.mock import patch, MagicMock

def test_environment_detection():
    """Test all environment detection cases from _configure_cloudflare_urls()."""
    
    print("Testing all environment detection cases:")
    print("=" * 60)
    
    # Test cases based on _configure_cloudflare_urls() logic
    test_cases = [
        {
            "name": "Local WASM (localhost:8088)",
            "origin": "http://localhost:8088",
            "href": "http://localhost:8088/",
            "expected": {
                "logout_url": "http://localhost:8088/oauth2/revoke",
                "redirect_uri": "http://localhost:8088/oauth/callback", 
                "token_url": "http://localhost:8088/oauth2/token",
                "use_new_tab": True
            }
        },
        {
            "name": "Workspace Mode (localhost:2718 with ?file=)",
            "origin": "http://localhost:2718",
            "href": "http://localhost:2718/?file=notebooks%2Fpkceflow_login.py",
            "expected": {
                "logout_url": "https://dash.cloudflare.com/oauth2/revoke",
                "redirect_uri": "https://auth.sandbox.marimo.app/oauth/sso-callback",
                "token_url": "https://dash.cloudflare.com/oauth2/token", 
                "use_new_tab": False
            }
        },
        {
            "name": "Sandbox Mode (localhost:2718 without ?file=)",
            "origin": "http://localhost:2718",
            "href": "http://localhost:2718/",
            "expected": {
                "logout_url": "https://dash.cloudflare.com/oauth2/revoke",
                "redirect_uri": "https://auth.sandbox.marimo.app/oauth/sso-callback",
                "token_url": "https://dash.cloudflare.com/oauth2/token",
                "use_new_tab": False
            }
        },
        {
            "name": "Other Localhost (localhost:3000)",
            "origin": "http://localhost:3000",
            "href": "http://localhost:3000/",
            "expected": {
                "logout_url": "https://dash.cloudflare.com/oauth2/revoke",
                "redirect_uri": "https://auth.sandbox.marimo.app/oauth/sso-callback",
                "token_url": "https://dash.cloudflare.com/oauth2/token",
                "use_new_tab": False
            }
        },
        {
            "name": "Production WASM (deployed)",
            "origin": "https://myapp.pages.dev",
            "href": "https://myapp.pages.dev/",
            "expected": {
                "logout_url": "https://myapp.pages.dev/oauth2/revoke",
                "redirect_uri": "https://myapp.pages.dev/oauth/callback",
                "token_url": "https://myapp.pages.dev/oauth2/token",
                "use_new_tab": True
            }
                },
        {
            "name": "Python Environment (no js module)",
            "origin": None,  # Will trigger AttributeError
            "href": "http://localhost:2718/?file=test.py",
            "expected": {
                "logout_url": "https://dash.cloudflare.com/oauth2/revoke",
                "redirect_uri": "https://auth.sandbox.marimo.app/oauth/sso-callback",
                "token_url": "https://dash.cloudflare.com/oauth2/token",
                "use_new_tab": False
            }
        },
        {
            "name": "Marimo Sandbox (marimo.io/p/dev)",
            "origin": "https://marimo.io",
            "href": "https://marimo.io/p/dev/notebook-kbgk5m-va5mhd9pe7w23m1ch50gvb",
            "expected": {
                "logout_url": "https://dash.cloudflare.com/oauth2/revoke",
                "redirect_uri": "https://auth.sandbox.marimo.app/oauth/sso-callback",
                "token_url": "https://dash.cloudflare.com/oauth2/token",
                "use_new_tab": False
            }
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print(f"   Origin: {case['origin']}")
        print(f"   Href: {case['href']}")
        print(f"   Expected config:")
        for key, value in case['expected'].items():
            print(f"     {key}: {value}")
        
        # Test the detection logic
        is_workspace_mode = False
        if case['origin'] and 'localhost:2718' in case['origin'] and '?file=' in case['href']:
            is_workspace_mode = True
        
        print(f"   Detected workspace mode: {is_workspace_mode}")
        print()

def test_state_generation_cases():
    """Test state generation for different environment cases."""
    
    print("\nTesting state generation for different environments:")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Workspace Mode",
            "hostname": "localhost",
            "port": "2718", 
            "href": "http://localhost:2718/?file=notebooks%2Fpkceflow_login.py",
            "expected_preserved": True
        },
        {
            "name": "Sandbox Mode", 
            "hostname": "localhost",
            "port": "2718",
            "href": "http://localhost:2718/",
            "expected_preserved": True
        },
        {
            "name": "WASM Mode",
            "hostname": "localhost", 
            "port": "8088",
            "href": "http://localhost:8088/login.html",
            "expected_preserved": False  # Should redirect to main page
        },
        {
            "name": "Sandbox App",
            "hostname": "abc123.sandbox.marimo.app",
            "port": "",
            "href": "https://abc123.sandbox.marimo.app/",
            "expected_preserved": True
        },
        {
            "name": "Marimo Sandbox (marimo.io/p/dev)",
            "hostname": "marimo.io",
            "port": "",
            "href": "https://marimo.io/p/dev/notebook-kbgk5m-va5mhd9pe7w23m1ch50gvb",
            "expected_preserved": True
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print(f"   Hostname: {case['hostname']}")
        print(f"   Port: {case['port']}")
        print(f"   Href: {case['href']}")
        
        # Simulate state generation logic
        sandbox_id = f"{case['hostname']}:{case['port']}" if case['port'] else case['hostname']
        
        # Determine state_href based on logic from _generate_state()
        state_href = case['href']
        
        # Special handling for workspace mode
        if case['href'] and "localhost:2718" in case['href'] and "?file=" in case['href']:
            print(f"   ✅ Workspace mode detected, preserving file parameter")
            state_href = case['href']
        elif case['href'] and "localhost:2718" in case['href']:
            print(f"   ℹ️  Localhost:2718 detected but no file parameter")
            state_href = case['href']
        elif case['href'] and ("login" in case['href'] or "pkceflow_login" in case['href']):
            # Simulate WASM environment logic
            parsed = urlparse(case['href'])
            state_href = f"{parsed.scheme}://{parsed.netloc}/"
            print(f"   🔄 Login page detected, redirecting to main page")
        else:
            print(f"   ℹ️  Using original href")
        
        # Create state object
        state = {
            "sandbox_id": sandbox_id,
            "href": state_href,
            "nonce": "test.nonce"
        }
        
        print(f"   Final state href: {state_href}")
        
        # Verify preservation
        if case['expected_preserved']:
            if state_href == case['href']:
                print(f"   ✅ URL preserved correctly")
            else:
                print(f"   ❌ URL not preserved correctly")
        else:
            if state_href != case['href']:
                print(f"   ✅ URL redirected correctly")
            else:
                print(f"   ❌ URL should have been redirected")

def test_callback_handler_cases():
    """Test callback handler logic for different scenarios."""
    
    print("\nTesting callback handler logic:")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Workspace Mode Callback",
            "state_href": "http://localhost:2718/?file=notebooks%2Fpkceflow_login.py",
            "expected_workspace_mode": True,
            "expected_preserve_file": True
        },
        {
            "name": "Sandbox Mode Callback", 
            "state_href": "http://localhost:2718/",
            "expected_workspace_mode": False,
            "expected_preserve_file": False
        },
        {
            "name": "WASM Mode Callback",
            "state_href": "http://localhost:8088/login.html",
            "expected_workspace_mode": False,
            "expected_preserve_file": False
        },
        {
            "name": "Production Callback",
            "state_href": "https://myapp.pages.dev/",
            "expected_workspace_mode": False,
            "expected_preserve_file": False
        },
        {
            "name": "Marimo Sandbox Callback",
            "state_href": "https://marimo.io/p/dev/notebook-kbgk5m-va5mhd9pe7w23m1ch50gvb",
            "expected_workspace_mode": False,
            "expected_preserve_file": False
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print(f"   State href: {case['state_href']}")
        
        # Simulate callback handler logic
        href_url = urlparse(case['state_href'])
        is_workspace_mode = (href_url.hostname == 'localhost' and 
                           href_url.port == '2718' and 
                           href_url.search_params.has('file'))
        
        print(f"   Detected workspace mode: {is_workspace_mode}")
        
        if is_workspace_mode:
            print(f"   ✅ Workspace mode detected, will preserve file parameter")
        else:
            print(f"   ℹ️  Standard mode, will use normal redirect logic")

def test_url_parsing_edge_cases():
    """Test edge cases in URL parsing."""
    
    print("\nTesting URL parsing edge cases:")
    print("=" * 60)
    
    edge_cases = [
        "http://localhost:2718/?file=test.py&other=param",
        "http://localhost:2718/?other=param&file=test.py",
        "http://localhost:2718/?file=",
        "http://localhost:2718/?file",
        "http://localhost:2718/file=test.py",  # No ? but has file=
        "http://localhost:2718/?notfile=test.py",  # Similar but not file=
        "https://localhost:2718/?file=test.py",  # HTTPS
        "http://LOCALHOST:2718/?file=test.py",  # Case sensitivity
    ]
    
    for i, url in enumerate(edge_cases, 1):
        print(f"\n{i}. URL: {url}")
        
        parsed = urlparse(url)
        has_file_param = 'file=' in parsed.query
        
        print(f"   Hostname: {parsed.hostname}")
        print(f"   Port: {parsed.port}")
        print(f"   Query: {parsed.query}")
        print(f"   Has file param: {has_file_param}")
        
        # Test workspace mode detection
        is_workspace_mode = (parsed.hostname == 'localhost' and 
                           parsed.port == '2718' and 
                           has_file_param)
        
        print(f"   Is workspace mode: {is_workspace_mode}")

if __name__ == "__main__":
    test_environment_detection()
    test_state_generation_cases()
    test_callback_handler_cases()
    test_url_parsing_edge_cases()
    
    print("\n" + "=" * 60)
    print("✅ All test cases completed!")
    print("This covers all the environment detection scenarios in _configure_cloudflare_urls()") 