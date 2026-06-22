"""Authentication-aware screen helpers for the realtime agent."""

from .login_screen_detector import LoginScreenDetection, detect_login_screen

__all__ = ["LoginScreenDetection", "detect_login_screen"]
