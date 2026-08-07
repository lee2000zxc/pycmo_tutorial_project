from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def title_matches(window_title: str, expected_fragment: str) -> bool:
    expected = _normalized(expected_fragment)
    return bool(expected) and expected in _normalized(window_title)


def dismiss_window_with_enter(expected_title: str) -> bool:
    """Find a visible top-level Windows dialog and send Enter once."""
    if sys.platform != "win32" or not expected_title.strip():
        return False

    user32 = ctypes.windll.user32
    found: list[int] = []
    enum_proc_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HWND,
        wintypes.LPARAM,
    )

    @enum_proc_type
    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        if title_matches(buffer.value, expected_title):
            found.append(int(hwnd))
            return False
        return True

    user32.EnumWindows(callback, 0)
    if not found:
        return False

    hwnd = found[0]
    wm_keydown = 0x0100
    wm_keyup = 0x0101
    vk_return = 0x0D
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.05)
    user32.PostMessageW(hwnd, wm_keydown, vk_return, 0)
    user32.PostMessageW(hwnd, wm_keyup, vk_return, 0)
    time.sleep(0.2)
    return True


def close_window(expected_title: str) -> bool:
    """Find a visible top-level window and request that it close."""
    if sys.platform != "win32" or not expected_title.strip():
        return False

    user32 = ctypes.windll.user32
    found: list[int] = []
    enum_proc_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HWND,
        wintypes.LPARAM,
    )

    @enum_proc_type
    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        if title_matches(buffer.value, expected_title):
            found.append(int(hwnd))
            return False
        return True

    user32.EnumWindows(callback, 0)
    if not found:
        return False

    wm_close = 0x0010
    user32.PostMessageW(found[0], wm_close, 0, 0)
    time.sleep(0.2)
    return True
