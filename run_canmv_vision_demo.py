#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print(">>> run_canmv_vision_demo.py started")
import sys
print(">>> __file__ =", __file__)
print(">>> sys.argv =", sys.argv)

from pprint import pprint

from vision_realtime_canmv import CanMVVisionSource


def main() -> None:
    print(">>> inside main()")
    source = CanMVVisionSource()
    print(">>> 开始接收来自 CanMV 的视觉状态 (Ctrl+C 退出)：")
    for state in source.stream():
        pprint(state)


if __name__ == "__main__":
    print(">>> __name__ is __main__, calling main()")
    main()
else:
    print(">>> run_canmv_vision_demo.py 被当成模块导入，没有自动运行 main()")