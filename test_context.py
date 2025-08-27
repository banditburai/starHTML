#!/usr/bin/env python
"""Test context menu positioning with debug output"""

import time
import subprocess

# Open the page in browser
print("Opening http://localhost:5015/16-position/ in browser...")
subprocess.run(["open", "http://localhost:5015/16-position/"])

print("\n" + "="*60)
print("MANUAL TEST INSTRUCTIONS:")
print("="*60)
print("1. Open the browser's Developer Console (Cmd+Option+I)")
print("2. Right-click in the gray 'Right-click in this area' box")
print("3. Look for console messages like:")
print("   - '[position] Using virtual anchor for contextMenu'")
print("   - '[position] Using DOM anchor contextArea for contextMenu'")
print("\n4. The context menu should appear at your cursor position")
print("   NOT at the bottom-left of the gray box")
print("\n5. If you see 'Using DOM anchor' instead of 'Using virtual anchor',")
print("   then the virtual element is not being detected properly")
print("="*60)