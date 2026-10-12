"""Self-owned Win32 fixture window for UIA acceptance tests.

Creates a real top-level window (unique class 'UcFixtureWnd') containing a
standard EDIT control and a BUTTON. Pressing the button sets the edit text to
'按钮已点击'. This keeps W-series tests fully isolated from any real user
application — zero interference with user sessions.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import threading

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# ---- precise signatures (avoid 64-bit truncation/overflow bugs) -----------
WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_void_p, ctypes.c_uint,
                             ctypes.c_size_t, ctypes.c_ssize_t)
user32.DefWindowProcW.restype = ctypes.c_ssize_t
user32.DefWindowProcW.argtypes = [wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM]
user32.CreateWindowExW.restype = wt.HWND
user32.CreateWindowExW.argtypes = [wt.DWORD, ctypes.c_wchar_p, ctypes.c_wchar_p,
                                   wt.DWORD, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, wt.HWND,
                                   ctypes.c_void_p, wt.HINSTANCE, wt.LPVOID]
user32.RegisterClassW.restype = wt.ATOM
user32.RegisterClassW.argtypes = [ctypes.c_void_p]
user32.GetMessageW.restype = ctypes.c_int
user32.GetMessageW.argtypes = [ctypes.c_void_p, wt.HWND, ctypes.c_uint,
                               ctypes.c_uint]

WND_TITLE = "UniversalComputer Fixture 窗口"
WND_CLASS = "UcFixtureWnd"
EDIT_ID = 1001
BUTTON_ID = 1002
BUTTON_RESULT_TEXT = "按钮已点击"

WM_COMMAND = 0x0111
WM_DESTROY = 0x0002
WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_VISIBLE = 0x10000000
WS_CHILD = 0x40000000
WS_BORDER = 0x00800000
ES_AUTOHSCROLL = 0x0080
CW_USEDEFAULT = 0x80000000


def run_fixture(stop_event: threading.Event) -> None:
    hInstance = kernel32.GetModuleHandleW(None)

    @WNDPROC
    def wnd_proc(hwnd, msg, wparam, lparam):
        if msg == WM_COMMAND and (wparam & 0xFFFF) == BUTTON_ID:
            user32.SetDlgItemTextW(hwnd, EDIT_ID, BUTTON_RESULT_TEXT)
            return 0
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    class WNDCLASSW(ctypes.Structure):
        _fields_ = [("style", ctypes.c_uint),
                    ("lpfnWndProc", WNDPROC),
                    ("cbClsExtra", ctypes.c_int),
                    ("cbWndExtra", ctypes.c_int),
                    ("hInstance", ctypes.c_void_p),
                    ("hIcon", ctypes.c_void_p),
                    ("hCursor", ctypes.c_void_p),
                    ("hbrBackground", ctypes.c_void_p),
                    ("lpszMenuName", ctypes.c_wchar_p),
                    ("lpszClassName", ctypes.c_wchar_p)]

    wc = WNDCLASSW()
    wc.style = 0
    wc.lpfnWndProc = wnd_proc
    wc.hInstance = hInstance
    wc.hbrBackground = 6  # COLOR_WINDOW + 1
    wc.lpszClassName = WND_CLASS
    if not user32.RegisterClassW(ctypes.byref(wc)):
        raise RuntimeError("RegisterClassW failed")

    hwnd = user32.CreateWindowExW(
        0, WND_CLASS, WND_TITLE, WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        CW_USEDEFAULT, CW_USEDEFAULT, 520, 220, None, None, hInstance, None)
    if not hwnd:
        raise RuntimeError("CreateWindowExW failed")

    # child controls: standard Win32 EDIT + BUTTON (UIA-visible)
    user32.CreateWindowExW(0, "EDIT", "初始文本",
                           WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL,
                           20, 30, 460, 28, hwnd, EDIT_ID, hInstance, None)
    user32.CreateWindowExW(0, "BUTTON", "确认按钮",
                           WS_CHILD | WS_VISIBLE,
                           20, 80, 140, 32, hwnd, BUTTON_ID, hInstance, None)

    msg = wt.MSG()
    while not stop_event.is_set():
        r = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
        if r <= 0:
            break
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))
    user32.DestroyWindow(hwnd)


def start_fixture() -> threading.Event:
    stop = threading.Event()
    t = threading.Thread(target=run_fixture, args=(stop,), daemon=True)
    t.start()
    return stop
