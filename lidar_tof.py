#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简易 TOF 激光雷达串口读取封装。

该模块实现最小化的 `ToFLidar` 类，用于通过串口读取 TOF 雷达测距数据。
真实硬件协议可能略有差异，这里采用常见的 0x59 0x59 帧头格式，若解析失败则尝试
读取文本行。即使未连接硬件，也可以在 `simulate_on_error=True` 时退化为模拟数据，
避免上层应用在开发阶段抛出 `ModuleNotFoundError`。
"""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import serial

from app_config import CONFIG

SerialException = getattr(serial, "SerialException", Exception)


def _default_port() -> str:
    """返回默认串口，优先采用配置文件中的设置。"""

    if CONFIG and CONFIG.serial and CONFIG.serial.port:
        return CONFIG.serial.port
    # 常见的 macOS / Linux / Windows 串口名称
    return os.environ.get("LIDAR_DEFAULT_PORT", "/dev/tty.usbserial-1110")


@dataclass
class _Measurement:
    distance_m: float
    strength: int


class ToFLidar:
    """封装 TOF 雷达串口通信与帧解析。"""

    FRAME_HEADER = 0x59
    FRAME_SIZE = 9

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        timeout: float = 1.0,
        *,
        simulate_on_error: bool = True,
    ) -> None:
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._simulate = False
        self._serial: Optional[serial.Serial] = None

        try:
            self._serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
            )
        except SerialException:
            if simulate_on_error:
                self._simulate = True
            else:
                raise

    def close(self) -> None:
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                pass

    def __enter__(self) -> "ToFLidar":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ------------------------------------------------------------------ #
    # 数据读取
    # ------------------------------------------------------------------ #
    def _read_frame(self) -> Optional[bytes]:
        if not self._serial:
            return None

        while True:
            header = self._serial.read(1)
            if not header:
                return None
            if header[0] != self.FRAME_HEADER:
                continue
            second = self._serial.read(1)
            if not second:
                return None
            if second[0] != self.FRAME_HEADER:
                # 帧头不完整，继续查找
                continue
            payload = self._serial.read(self.FRAME_SIZE - 2)
            if len(payload) != self.FRAME_SIZE - 2:
                return None
            return header + second + payload

    @staticmethod
    def _parse_frame(frame: bytes) -> Optional[_Measurement]:
        if len(frame) != ToFLidar.FRAME_SIZE:
            return None
        distance = frame[2] + frame[3] * 256
        strength = frame[4] + frame[5] * 256
        if distance <= 0:
            return None
        return _Measurement(distance_m=distance / 100.0, strength=strength)

    def _read_text_line(self) -> Optional[_Measurement]:
        if not self._serial:
            return None
        line = self._serial.readline()
        if not line:
            return None
        try:
            text = line.decode("utf-8", errors="ignore").strip()
            if not text:
                return None
            # 支持 "distance,strength" 或单个距离
            if "," in text:
                first, second, *_ = text.split(",")
                distance = float(first.strip())
                strength = int(float(second.strip()))
            else:
                distance = float(text)
                strength = 0
        except ValueError:
            return None
        if distance <= 0:
            return None
        return _Measurement(distance_m=distance, strength=strength)

    def read_measurement(self) -> Optional[Tuple[float, int]]:
        """读取一次测量结果，返回 (距离, 强度)。"""

        if self._simulate:
            # 使用简单的正弦波模拟读取，便于 UI 演示
            now = time.time()
            distance = 2.0 + 0.2 * math.sin(now / 3.0)
            strength = 150 + int(30 * math.cos(now / 4.0))
            return round(distance, 3), max(strength, 0)

        measurement = None
        frame = self._read_frame()
        if frame:
            measurement = self._parse_frame(frame)
        if measurement is None:
            measurement = self._read_text_line()

        if measurement is None:
            return None
        return measurement.distance_m, measurement.strength


__all__ = ["ToFLidar", "_default_port", "SerialException"]

