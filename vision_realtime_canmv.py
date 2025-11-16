#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 CanMV 摄像头串口读取视觉状态，并转换为 VisionState（带调试打印版）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from queue import Empty, Queue
from threading import Event, Thread
import time
from typing import Iterator, Optional

import serial  # 需要 pyserial

from vision_logic import (
    VisionState,
    LinePosition,
    BodyOrientation,
    GestureCode,
)

# ======== 串口默认配置 ========

DEFAULT_PORT = "/dev/tty.usbserial-110"
DEFAULT_BAUDRATE = 115200
DEFAULT_TIMEOUT = 1.0  # 秒


def parse_vision_line(line: str) -> Optional[VisionState]:
    """解析一行 'VISION ...' 文本，成功则返回 VisionState，失败返回 None。"""
    line = line.strip()
    if not line:
        return None

    parts = line.split()
    if len(parts) != 5 or parts[0] != "VISION":
        # 调试时可以观察到收到的原始行
        print(">>> [parse] 非VISION行:", repr(line))
        return None

    _, person_str, line_str, orient_str, gesture_str = parts

    try:
        person_present = (person_str == "1")
        line_position = LinePosition[line_str]
        orientation = BodyOrientation[orient_str]
        gesture = GestureCode[gesture_str]
    except KeyError as e:
        print(">>> [parse] 枚举解析失败:", e, "原始行:", repr(line))
        return None

    return VisionState(
        person_present=person_present,
        line_position=line_position,
        orientation=orientation,
        gesture=gesture,
        timestamp=datetime.now(),
    )



@dataclass
class CanMVVisionSource:
    """
    从 CanMV 串口持续读取 VisionState 的数据源。

    VisionSafetyController 之前依赖的 stream() 仍旧可用，
    新增 stream_states() 与 get_latest_frame_base64()。
    """

    port: str = DEFAULT_PORT
    baudrate: int = DEFAULT_BAUDRATE
    timeout: float = DEFAULT_TIMEOUT
    auto_start: bool = True
    _latest_state: VisionState = field(
        default_factory=lambda: VisionState(
            person_present=False,
            line_position=LinePosition.UNKNOWN,
            orientation=BodyOrientation.UNKNOWN,
            gesture=GestureCode.NONE,
            timestamp=datetime.now(),
        )
    )

    def __post_init__(self) -> None:
        # 最近一帧的 Base64 图片缓存
        self._latest_frame_base64: Optional[str] = None

        self._serial: Optional[serial.Serial] = None
        self._states_queue: Queue[VisionState] = Queue()
        self._stop_event = Event()
        self._reader_thread: Optional[Thread] = None
        self._open_serial()
        if self.auto_start:
            self._start_reader_thread()

    def _open_serial(self) -> None:
        """尝试打开串口，如果失败则记录日志但不中断主线程。"""

        print(f">>> [CanMVVisionSource] 准备打开串口: {self.port}, {self.baudrate}bps")
        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        except Exception as exc:  # pragma: no cover - 依赖硬件
            self._serial = None
            print(">>> [CanMVVisionSource] 打开串口失败:", repr(exc))
        else:
            print(">>> [CanMVVisionSource] 串口打开成功:", self._serial)

    def _start_reader_thread(self) -> None:
        if self._serial is None:
            print(">>> [CanMVVisionSource] 串口未打开，无法启动读取线程")
            return
        if self._reader_thread and self._reader_thread.is_alive():
            return
        self._reader_thread = Thread(target=self._reader_loop, name="CanMVVisionReader", daemon=True)
        self._reader_thread.start()
        print(">>> [CanMVVisionSource] 后台读取线程已启动")

    def _reader_loop(self) -> None:
        assert self._serial is not None  # 在启动线程前已检查
        while not self._stop_event.is_set():
            try:
                raw = self._serial.readline()
            except serial.SerialException as exc:  # type: ignore[attr-defined]
                print(">>> [CanMVVisionSource] 串口读取异常:", exc)
                try:
                    self._serial.close()
                except Exception:
                    pass
                time.sleep(1.0)
                self._open_serial()
                if self._serial is None:
                    break
                continue
            except Exception as exc:
                print(">>> [CanMVVisionSource] 串口未知异常:", exc)
                break

            if not raw:
                continue
            try:
                text = raw.decode("utf-8", errors="ignore").strip()
            except Exception as exc:
                print(">>> [CanMVVisionSource] 解码失败:", repr(exc), "原始raw:", raw)
                continue

            if not text:
                continue

                          # 优先处理图像帧
            if text.startswith("FRAME_BASE64"):
                # 允许三种形式：
                # "FRAME_BASE64 xxx"
                # "FRAME_BASE64: xxx"
                # "FRAME_BASE64\txxx"
                parts = text.split(None, 1)  # 按空白字符拆一次
                if len(parts) == 2:
                    self._latest_frame_base64 = parts[1].strip()
                    print(">>> [CanMVVisionSource] 收到 FRAME_BASE64，长度:", len(self._latest_frame_base64))
                else:
                    print(">>> [CanMVVisionSource] 收到 FRAME_BASE64 行但没有数据:", repr(text))
                continue

            if text.startswith("FRAME_BASE64_ERROR"):
                print(">>> [CanMVVisionSource] FRAME_BASE64_ERROR:", text)
                continue

            state = parse_vision_line(text)
            if state:
                print(">>> [CanMVVisionSource] 收到 VISION 状态，当前是否有缓存图像帧:", bool(self._latest_frame_base64))
                self._latest_state = state
                self._states_queue.put(state)

    def stream_states(self) -> Iterator[VisionState]:
        """
        持续返回解析得到的 VisionState。

        如果串口未能打开，则立即结束生成器。
        """

        if self._serial is None or self._reader_thread is None:
            print(">>> [CanMVVisionSource] 没有活跃串口连接，无法提供状态流")
            return

        while True:
            if self._stop_event.is_set() and self._states_queue.empty():
                break
            try:
                state = self._states_queue.get(timeout=0.2)
            except Empty:
                continue
            yield state

    def stream(self) -> Iterator[VisionState]:
        """兼容旧接口，等价于 stream_states()."""

        return self.stream_states()

    def get_latest_frame_base64(self) -> Optional[str]:
        """返回最近一次收到的 FRAME_BASE64 数据。"""

        return self._latest_frame_base64

    def get_latest_state(self) -> VisionState:
        """提供最新状态快照，供同步轮询使用。"""

        return self._latest_state

    def close(self) -> None:
        """停止后台线程并关闭串口。"""

        self._stop_event.set()
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=1.0)
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except Exception as exc:  # pragma: no cover
                print(">>> [CanMVVisionSource] 关闭串口失败:", exc)

    def __del__(self) -> None:  # pragma: no cover - 防御性清理
        try:
            self.close()
        except Exception:
            pass


def main() -> None:
    """独立测试入口：从串口读并打印 VisionState。"""
    from pprint import pprint

    print(">>> vision_realtime_canmv.main() 启动")
    source = CanMVVisionSource()
    for state in source.stream_states():
        print(">>> [main] 解析得到 VisionState：")
        pprint(state)


if __name__ == "__main__":
    main()
