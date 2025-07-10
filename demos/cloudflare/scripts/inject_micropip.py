#!/usr/bin/env python3
"""
Script to inject micropip installation code into marimo notebooks.
"""

import os
import sys
from pathlib import Path

def inject_micropip_install(notebook_path):
    """Inject micropip installation code into a marimo notebook."""
    
    # Read the wheel filename from export/WHEEL_FILENAME.txt
    wheel_filename_path = Path(__file__).parent.parent / "export" / "WHEEL_FILENAME.txt"
    if not wheel_filename_path.exists():
        print(f"Error: {wheel_filename_path} does not exist. Run make export first.")
        sys.exit(1)
    with open(wheel_filename_path, 'r') as f:
        wheel_filename = f.read().strip()
    wheel_url = f"http://localhost:8088/{wheel_filename}"
    
    # Read the micropip installation code
    script_dir = Path(__file__).parent
    micropip_script = script_dir / "install_local_moutils.py"
    
    with open(micropip_script, 'r') as f:
        micropip_code = f.read().rstrip()
    
    # Replace the install URL in the micropip code
    micropip_code = micropip_code.replace(
        'await micropip.install("http://localhost:8088/moutils-latest.whl")',
        f'await micropip.install("{wheel_url}")'
    )
    
    # Read the notebook
    with open(notebook_path, 'r') as f:
        content = f.read()
    
    # Check if micropip installation is already present
    if "Install local moutils wheel" in content:
        print(f"⚠️  Micropip installation already present in {notebook_path}")
        return
    
    # Find the position after the first cell (after the app definition)
    lines = content.split('\n')
    
    # Look for the app definition line
    app_line_idx = None
    for i, line in enumerate(lines):
        if 'app = marimo.App(' in line:
            app_line_idx = i
            break
    
    if app_line_idx is None:
        print(f"Warning: Could not find app definition in {notebook_path}")
        return
    
    # Find the next cell (look for @app.cell)
    next_cell_idx = None
    for i in range(app_line_idx + 1, len(lines)):
        if lines[i].strip().startswith('@app.cell'):
            next_cell_idx = i
            break
    
    if next_cell_idx is None:
        print(f"Warning: Could not find next cell in {notebook_path}")
        return
    
    # Ensure exactly 2 blank lines before the injected cell
    # Remove blank lines before next_cell_idx
    while next_cell_idx > 0 and lines[next_cell_idx-1].strip() == "":
        next_cell_idx -= 1
    # Insert 2 blank lines
    lines = lines[:next_cell_idx] + ["", ""] + lines[next_cell_idx:]
    next_cell_idx += 2
    
    # Prepare the micropip cell as async def _():
    micropip_lines = [
        "@app.cell(hide_code=True)",
        "async def _():",
    ]
    for l in micropip_code.split('\n'):
        micropip_lines.append(f"    {l.rstrip()}")
    micropip_lines.append("    return moutils_installed")
    
    # Insert the micropip cell before the next cell
    lines = lines[:next_cell_idx] + micropip_lines + lines[next_cell_idx:]

    # Ensure exactly two blank lines after the injected cell
    injected_end = next_cell_idx + len(micropip_lines) - 1
    # Remove any blank lines immediately after the injected cell
    while injected_end + 1 < len(lines) and lines[injected_end + 1].strip() == "":
        lines.pop(injected_end + 1)
    # Insert two blank lines
    lines.insert(injected_end + 1, "")
    lines.insert(injected_end + 2, "")
    
    # Now modify any cells that import moutils to depend on the installation
    i = 0
    while i < len(lines):
        line = lines[i]
        if 'from moutils.' in line or 'import moutils' in line:
            # Find the cell definition above this line
            cell_start = i
            while cell_start > 0 and not lines[cell_start].strip().startswith('@app.cell'):
                cell_start -= 1
            
            if cell_start > 0:
                # Find the function definition line
                func_line = cell_start + 1
                while func_line < len(lines) and not lines[func_line].strip().startswith('def _('):
                    func_line += 1
                
                if func_line < len(lines):
                    func_def = lines[func_line].strip()
                    if func_def.startswith('def _():'):
                        # No parameters, add moutils_installed
                        lines[func_line] = func_def.replace('def _():', 'def _(moutils_installed):')
                    elif func_def.startswith('def _(') and not 'moutils_installed' in func_def:
                        # Has parameters, add moutils_installed to the beginning
                        # Extract existing parameters
                        param_start = func_def.find('(') + 1
                        param_end = func_def.find(')')
                        if param_end > param_start:
                            existing_params = func_def[param_start:param_end].strip()
                            if existing_params:
                                new_params = f"moutils_installed, {existing_params}"
                            else:
                                new_params = "moutils_installed"
                        else:
                            new_params = "moutils_installed"
                        
                        new_func_def = func_def[:param_start] + new_params + func_def[param_end:]
                        lines[func_line] = new_func_def
        i += 1
    
    # Remove consecutive blank lines (max 2 in a row)
    cleaned_lines = []
    blank_count = 0
    for l in lines:
        if l.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                cleaned_lines.append("")
        else:
            blank_count = 0
            cleaned_lines.append(l.rstrip())
    
    # Remove blank lines at the end of the file (W391)
    while cleaned_lines and cleaned_lines[-1].strip() == "":
        cleaned_lines.pop()
    
    # Write back to the file with a single newline at the end (fix W292)
    with open(notebook_path, 'w') as f:
        f.write('\n'.join(cleaned_lines) + '\n')
    
    print(f"✅ Injected micropip installation into {notebook_path}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python inject_micropip.py <notebook_path>")
        sys.exit(1)
    
    notebook_path = sys.argv[1]
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook file {notebook_path} does not exist")
        sys.exit(1)
    
    inject_micropip_install(notebook_path)

if __name__ == "__main__":
    main() 