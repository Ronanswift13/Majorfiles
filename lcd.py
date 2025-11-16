#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""桌面环境的 MaixPy lcd 模块占位实现."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


_initialized: bool = False
_config: Optional[dict[str, Any]] = None


def init(**kwargs: Any) -> None:
    """模拟初始化 CANMV LCD，桌面环境仅打印日志。"""

    global _initialized, _config
    _initialized = True
    _config = kwargs or {}
    print(f"[lcd-stub] init called with {_config}")


def deinit() -> None:
    """释放 LCD 资源（模拟）。"""

    global _initialized, _config
    _initialized = False
    _config = None
    print("[lcd-stub] deinit called")


def rotation(value: int) -> None:
    """设置旋转角度（模拟，仅记录日志）。"""

    print(f"[lcd-stub] rotation set to {value}")


def clear(color: int = 0x000000) -> None:
    """清屏操作（模拟）。"""

    print(f"[lcd-stub] clear screen with color #{color:06x}")


def display(image: Any) -> None:
    """显示一帧图像（模拟，输出尺寸等信息）。"""

    if not _initialized:
        raise RuntimeError("lcd not initialized (stub)")
    size = getattr(image, "size", None)
    print(f"[lcd-stub] display frame; size={size}")


def width() -> int:
    """返回 LCD 宽度（若配置缺省则返回 0）。"""

    if isinstance(_config, dict):
        return int(_config.get("width", 0))
    return 0


def height() -> int:
    """返回 LCD 高度（若配置缺省则返回 0）。"""

    if isinstance(_config, dict):
        return int(_config.get("height", 0))
    return 0


__all__ = [
    "init",
    "deinit",
    "rotation",
    "clear",
    "display",
    "width",
    "height",
]
