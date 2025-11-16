#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""命令行版安全监控应用：账号登录 + 机位控制 + 告警仿真。"""

from __future__ import annotations

import time
from typing import Optional

from user_auth import (
    User,
    authenticate,
    user_can_set_target_cabinet,
    user_can_view_logs,
    user_is_admin,
)
from safety_logic import AlarmResult, alarm_level_to_color, format_alarm_for_log
from controller_stub import CameraSource, LidarSource, SafetyController

# 这里使用静态序列生成模拟数据源；后续可替换为真实硬件采集
DEFAULT_CABINET_SEQUENCE = [None, 1, 1, 2, 2, 3, 3, None]
DEFAULT_CROSS_LINE_SEQUENCE = [False, False, True, False, False, True, False, False]


def create_default_controller() -> SafetyController:
    """基于模拟数据源创建主控对象，初始 target_cabinet 为空。"""

    lidar_source = LidarSource(DEFAULT_CABINET_SEQUENCE)
    camera_source = CameraSource(DEFAULT_CROSS_LINE_SEQUENCE)
    return SafetyController(lidar_source=lidar_source, camera_source=camera_source, target_cabinet=None)


def show_user_info(user: User) -> None:
    """打印当前用户信息与权限，方便确认账号能力。"""

    role_names = ", ".join(role.name for role in user.roles)
    print("=== 当前用户 ===")
    print(f"用户名: {user.username}")
    print(f"显示名: {user.display_name}")
    print(f"角色: {role_names or '无'}")
    print(f"管理员: {user_is_admin(user)}")
    print(f"可设置机位: {user_can_set_target_cabinet(user)}")
    print(f"可查看日志: {user_can_view_logs(user)}")


def prompt_target_cabinet(user: User, controller: SafetyController) -> None:
    """询问并更新目标机位，仅在拥有权限时生效。"""

    if not user_can_set_target_cabinet(user):
        print("当前账号无权设置机位。")
        return

    raw = input("请输入目标机位编号（如 1/2/3），或输入 none 清空: ").strip().lower()
    if raw == "none":
        controller.set_target_cabinet(None)
        print("已清空当前目标机位。")
        return

    try:
        cabinet = int(raw)
    except ValueError:
        print("输入无效，请输入整数或 none。")
        return

    controller.set_target_cabinet(cabinet)
    print(f"当前目标机位已设置为 {cabinet}。")


def run_simulation_steps(
    user: User,
    controller: SafetyController,
    steps: int = 10,
    interval_sec: float = 1.0,
) -> None:
    """运行若干步安全状态仿真，打印日志结果。"""

    if not user_can_view_logs(user):
        print("当前账号无权查看日志。")
        return

    print(f"开始仿真，共 {steps} 步，间隔 {interval_sec:.1f}s。")
    for _ in range(steps):
        result: AlarmResult = controller.step()
        log_line = format_alarm_for_log(result)
        color = alarm_level_to_color(result.level)
        print(f"[{color}] {log_line}")
        time.sleep(interval_sec)


def login() -> Optional[User]:
    """简单的用户名/密码登录流程。"""

    username = input("用户名: ").strip()
    password = input("密码: ")
    user = authenticate(username, password)
    if user is None:
        print("用户名或密码错误。")
        return None
    print(f"登录成功，欢迎 {user.display_name}！")
    return user


def main() -> None:
    """程序入口：登录后提供主菜单，串联控制器操作。"""

    print("=== 变电站安全监控命令行应用 ===")
    controller = create_default_controller()
    current_user = login()
    if current_user is None:
        return

    while True:
        print(
            "\n=== 主菜单 ===\n"
            "1) 查看当前用户与权限\n"
            "2) 设置/修改目标机位\n"
            "3) 启动安全状态仿真（运行若干步）\n"
            "4) 退出"
        )
        choice = input("请选择操作 [1-4]: ").strip()

        if choice == "1":
            show_user_info(current_user)
        elif choice == "2":
            prompt_target_cabinet(current_user, controller)
        elif choice == "3":
            steps_input = input("请输入需要运行的步数（默认 10）: ").strip()
            if steps_input:
                try:
                    steps = int(steps_input)
                    if steps <= 0:
                        print("步数须为正整数。")
                        continue
                except ValueError:
                    print("请输入有效的整数。")
                    continue
            else:
                steps = 10
            run_simulation_steps(current_user, controller, steps=steps, interval_sec=1.0)
        elif choice == "4":
            print("退出程序。")
            break
        else:
            print("无效选项，请重新选择。")


if __name__ == "__main__":
    main()
