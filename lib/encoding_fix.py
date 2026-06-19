"""
UTF-8 Encoding Fix for Windows
This module ensures all file operations use UTF-8 encoding, not the Windows default (cp1252/charmap)
"""

import sys
import os
import io
import builtins

# CRITICAL: Set environment variable FIRST
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Fix stdout/stderr immediately
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def patch_builtin_open():
    """Patch the builtin open() to use UTF-8 by default on Windows"""
    original_open = builtins.open
    
    def utf8_open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        """Wrapper around builtin open that defaults to UTF-8 encoding"""
        # On Windows, if no encoding specified and we're opening in text mode, use UTF-8
        if sys.platform == 'win32' and 'b' not in mode and encoding is None:
            encoding = 'utf-8'
        
        return original_open(file, mode=mode, buffering=buffering, 
                            encoding=encoding, errors=errors, newline=newline)
    
    builtins.open = utf8_open


def ensure_utf8_environment():
    """
    Ensure UTF-8 encoding is used throughout the application
    """
    # Environment variable
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Patch the builtin open() function to default to UTF-8
    patch_builtin_open()
    
    if sys.platform == 'win32':
        # Additional Windows-specific fixes
        try:
            import locale
            # Try to set locale to UTF-8
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except Exception:
            try:
                # Fallback for Windows
                locale.setlocale(locale.LC_ALL, '')
            except Exception:
                pass


# Apply UTF-8 fixes IMMEDIATELY when this module is imported
os.environ['PYTHONIOENCODING'] = 'utf-8'
patch_builtin_open()
ensure_utf8_environment()
