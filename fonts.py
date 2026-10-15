from __future__ import annotations

import pygame

_PREFERRED = "dejavusans"


class _FreeTypeFont:

    def __init__(self, size, bold=False):
        from pygame import _freetype as ft
        ft.init()
        self._ft = ft
        self._font = ft.Font(None, size)
        if bold:
            self._font.style |= ft.STYLE_STRONG

    def render(self, text, antialias, color, background=None):
        surface, _ = self._font.render(
            str(text), fgcolor=color, bgcolor=background
        )
        return surface


def _font_module_available():
    try:
        import pygame.font as pf
        pf.init()
        return pf
    except Exception:
        return None


def load_font(size, bold=False):
    pf = _font_module_available()
    if pf is not None:
        try:
            font = pf.SysFont(_PREFERRED, size, bold=bold)
            if font is not None:
                return font
        except Exception:
            pass
    return _FreeTypeFont(size, bold)
