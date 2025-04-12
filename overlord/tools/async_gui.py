"""
Asynchronous GUI automation utilities for macOS using safer approaches.
This module provides Mac-specific implementations without using PyObjC's direct
CoreFoundation calls that can lead to CFData assertion errors.
"""

import asyncio
import base64
import os
import subprocess
import tempfile

# Default screen size when we can't detect it
DEFAULT_SCREEN_SIZE = (1366, 768)

async def get_screen_size():
    """
    Get the screen size using system_profiler instead of PyObjC.
    
    Returns:
        Tuple containing (width, height)
    """
    try:
        # Use macOS command line tools instead of PyObjC
        proc = await asyncio.create_subprocess_shell(
            "system_profiler SPDisplaysDataType | grep Resolution",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        
        # Parse the output
        output = stdout.decode().strip()
        if "x" in output and "Retina" not in output:
            # Format typically: "Resolution: 1920 x 1080"
            try:
                parts = output.split("Resolution:")[1].strip().split("x")
                if len(parts) == 2:
                    width = int(parts[0].strip())
                    height = int(parts[1].strip())
                    return width, height
            except (IndexError, ValueError):
                # In case of parsing error, fall back to alternative method
                pass
                
        # If we can't parse or there's a Retina display, use screencapture to check
        # This approach is more reliable for Retina displays
        return await _get_screen_size_from_screenshot()
    except Exception as e:
        print("Error getting screen size: {0}".format(e))
        return DEFAULT_SCREEN_SIZE

async def _get_screen_size_from_screenshot():
    """
    Get screen size by taking a small screenshot and checking its dimensions.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
        
        # Take a small screenshot
        proc = await asyncio.create_subprocess_shell(
            f"screencapture -t png -x {tmp_path}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        
        # Use sips to get the dimensions
        proc = await asyncio.create_subprocess_shell(
            f"sips -g pixelWidth -g pixelHeight {tmp_path}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        
        # Parse the output
        output = stdout.decode().strip()
        width = height = 0
        
        for line in output.splitlines():
            if "pixelWidth" in line:
                width = int(line.split(":")[1].strip())
            elif "pixelHeight" in line:
                height = int(line.split(":")[1].strip())
        
        # Clean up
        os.unlink(tmp_path)
        
        if width > 0 and height > 0:
            return width, height
        return DEFAULT_SCREEN_SIZE
    except Exception as e:
        print("Error getting screen size from screenshot: {0}".format(e))
        return DEFAULT_SCREEN_SIZE

async def get_cursor_position():
    """
    Get the current cursor position using cliclick.
    
    Returns:
        Tuple containing (x, y) coordinates
    """
    try:
        # Use cliclick to get the cursor position
        proc = await asyncio.create_subprocess_shell(
            "cliclick p",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        
        # Parse the output
        output = stdout.decode().strip()
        # Format: "123,456"
        if "," in output:
            parts = output.split(",")
            x = int(parts[0])
            y = int(parts[1])
            return x, y
        return (0, 0)
    except Exception as e:
        print("Error getting cursor position: {0}".format(e))
        return (0, 0)

async def move_mouse(x, y):
    """
    Move the mouse to the specified coordinates using cliclick.
    
    Args:
        x: X coordinate
        y: Y coordinate
        
    Returns:
        True if successful, False otherwise
    """
    try:
        proc = await asyncio.create_subprocess_shell(
            "cliclick m:{0},{1}".format(x, y),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0
    except Exception as e:
        print("Error moving mouse: {0}".format(e))
        return False

async def click_mouse(button="left"):
    """
    Click the mouse at its current position.
    
    Args:
        button: 'left', 'right', or 'middle'
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cmd = "c:."  # Default left click
        if button == "right":
            cmd = "rc:."
        elif button == "middle":
            # cliclick doesn't directly support middle click, so we'll simulate with keyboard
            proc = await asyncio.create_subprocess_shell(
                "osascript -e 'tell application \"System Events\" to key code 3 using {command down}'",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        
        proc = await asyncio.create_subprocess_shell(
            "cliclick {0}".format(cmd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0
    except Exception as e:
        print("Error clicking mouse: {0}".format(e))
        return False

async def double_click():
    """
    Double-click the mouse at its current position.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        proc = await asyncio.create_subprocess_shell(
            "cliclick dc:.",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0
    except Exception as e:
        print("Error double-clicking: {0}".format(e))
        return False

async def drag_mouse(from_x, from_y, to_x, to_y):
    """
    Drag the mouse from one position to another.
    
    Args:
        from_x: Starting X coordinate
        from_y: Starting Y coordinate
        to_x: Ending X coordinate
        to_y: Ending Y coordinate
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # First move to start position
        await move_mouse(from_x, from_y)
        
        # Then drag to end position
        proc = await asyncio.create_subprocess_shell(
            "cliclick dd:{0},{1} du:{2},{3}".format(from_x, from_y, to_x, to_y),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0
    except Exception as e:
        print("Error dragging mouse: {0}".format(e))
        return False

async def type_text(text, delay_ms=10):
    """
    Type text at the current cursor position.
    
    Args:
        text: The text to type
        delay_ms: Delay between keystrokes in milliseconds
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Escape special characters
        escaped_text = text.replace('"', '\\"').replace("'", "\\'")
        
        # Use cliclick for typing with delay
        proc = await asyncio.create_subprocess_shell(
            'cliclick -w {0} t:"{1}"'.format(delay_ms, escaped_text),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0
    except Exception as e:
        print("Error typing text: {0}".format(e))
        return False

async def press_key(key):
    """
    Press a key or key combination.
    
    Args:
        key: Key name (e.g., 'return', 'esc', 'cmd+c')
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Map common key names to cliclick format
        key_map = {
            'return': 'return',
            'enter': 'return',
            'esc': 'esc',
            'escape': 'esc',
            'tab': 'tab',
            'space': 'space',
            'backspace': 'backspace',
            'delete': 'delete',
            'up': 'up',
            'down': 'down',
            'left': 'left',
            'right': 'right',
            'home': 'home',
            'end': 'end',
            'pageup': 'page-up',
            'pagedown': 'page-down',
        }
        
        if '+' in key:
            # Handle key combinations with modifiers
            parts = key.split('+')
            if len(parts) == 2:
                modifier, k = parts
                
                # Map modifiers
                mod_map = {
                    'cmd': 'command',
                    'command': 'command',
                    'ctrl': 'control',
                    'control': 'control',
                    'alt': 'option',
                    'option': 'option',
                    'shift': 'shift'
                }
                
                if modifier.lower() in mod_map and k:
                    # Use AppleScript for complex key combinations
                    osascript_cmd = """
                    osascript -e 'tell application "System Events" to keystroke "{0}" using {{{1} down}}'
                    """.format(k, mod_map[modifier.lower()])
                    proc = await asyncio.create_subprocess_shell(
                        osascript_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    await proc.communicate()
                    return proc.returncode == 0
        
        # Handle single keys
        mapped_key = key_map.get(key.lower(), key)
        
        # Use cliclick for normal keys
        proc = await asyncio.create_subprocess_shell(
            'cliclick kp:{0}'.format(mapped_key),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0
    except Exception as e:
        print("Error pressing key: {0}".format(e))
        return False

async def take_screenshot(path):
    """
    Take a screenshot and save it to the specified path.
    Uses screencapture instead of PyObjC to avoid CoreFoundation errors.
    
    Args:
        path: Path where the screenshot will be saved
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        
        # Use native macOS screencapture utility
        proc = await asyncio.create_subprocess_shell(
            "screencapture -x {0}".format(path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        
        # Verify file exists
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return True
        return False
    except Exception as e:
        print("Error taking screenshot: {0}".format(e))
        return False
