# -*- coding: utf-8 -*-
"""ASCII 行格式 TOF 激光雷达读取脚本。"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Optional, Tuple

try:
    import serial  # type: ignore
except ModuleNotFoundError as exc:
    raise RuntimeError("未安装 pyserial，请先执行 `pip install pyserial`.") from exc

if not hasattr(serial, "Serial"):
    raise RuntimeError(
        "检测到非 pyserial 的 `serial` 模块，请执行 `pip uninstall serial && pip install pyserial`."
    )

try:
    SerialException = serial.SerialException  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    class SerialException(Exception):
        pass


SERIAL_PORT = "/dev/tty.usbserial-1110"
BAUDRATE = 115200
TIMEOUT_S = 1.0


def _default_port() -> str:
    if sys.platform.startswith("win"):
        return SERIAL_PORT
    if sys.platform.startswith("linux"):
        return "/dev/ttyUSB0"
    if sys.platform.startswith("darwin"):
        return "/dev/tty.usbserial-0001"
    return SERIAL_PORT


class AsciiLidar:
    """解析形如 \"<distance_mm>, <strength>\" 的 ASCII 文本行。"""

    def __init__(self, port: str, baudrate: int = BAUDRATE, timeout: float = TIMEOUT_S):
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self.ser = self._open_serial()

    def _open_serial(self) -> serial.Serial:
        ser = serial.Serial(
            port=self._port,
            baudrate=self._baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self._timeout,
        )
        ser.reset_input_buffer()
        return ser

    def _reset_serial(self) -> None:
        """尝试在串口异常后自动重连。"""

        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass
        time.sleep(0.1)
        try:
            self.ser = self._open_serial()
            print("串口已自动重连")
        except Exception as exc:
            # 交由上层定时重试
            print(f"串口重连失败：{exc}")
            self.ser = None

    def close(self) -> None:
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass
        self.ser = None

    def read_measurement(self) -> Optional[Tuple[float, int]]:
        """
        读取一行 ASCII 文本，格式为 \"<distance_mm>, <strength>\".
        返回 (distance_m, strength)，若当前行无法解析则返回 None。
        """
        if not self.ser or not self.ser.is_open:
            return None

        try:
            line = self.ser.readline()
        except SerialException as exc:  # type: ignore[attr-defined]
            print(f"串口读取异常：{exc}")
            # "device reports readiness..." 通常意味着连接断开或被其他进程占用
            if "device reports readiness to read" in str(exc).lower():
                self._reset_serial()
            time.sleep(0.05)
            return None
        if not line:
            return None

        text = line.decode("ascii", errors="ignore").strip()
        if not text:
            return None

        parts = [p.strip() for p in text.split(",")]
        if len(parts) < 2:
            return None

        try:
            dist_raw = int(parts[0])
            strength = int(parts[1])
        except ValueError:
            return None

        distance_m = dist_raw / 1000.0
        return distance_m, strength


ToFLidar = AsciiLidar


def main() -> None:
    parser = argparse.ArgumentParser(description="ASCII TOF 激光雷达命令行测距")
    parser.add_argument("--port", default=_default_port(), help="串口名，例如 COM5 / /dev/ttyUSB0")
    parser.add_argument("--baudrate", type=int, default=BAUDRATE, help="波特率，默认 115200")
    parser.add_argument("--timeout", type=float, default=TIMEOUT_S, help="串口读超时（秒）")
    args = parser.parse_args()

    lidar: Optional[AsciiLidar] = None
    try:
        print(f"打开串口 {args.port}，波特率 {args.baudrate} ...")
        lidar = AsciiLidar(args.port, baudrate=args.baudrate, timeout=args.timeout)
        print("开始读取 ASCII 行数据（Ctrl+C 退出）")

        while True:
            meas = lidar.read_measurement() if lidar else None
            if meas is None:
                print("未读取到有效数据行")
            else:
                distance_m, strength = meas
                print(f"距离: {distance_m:.3f} m | 强度: {strength}")
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n收到中断，准备退出..")
    except SerialException as exc:
        print(f"串口错误：{exc}")
    except Exception as exc:
        print(f"运行时错误：{exc}")
    finally:
        if lidar is not None:
            lidar.close()
        print("串口已关闭")


if __name__ == "__main__":
    main()
