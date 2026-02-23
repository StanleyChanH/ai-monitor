#!/usr/bin/env python3
"""Termux 环境设置脚本"""
import os
import pathlib
import stat

# 创建 tmp 目录
tmp_dir = pathlib.Path(os.path.expanduser("~/tmp"))
tmp_dir.mkdir(parents=True, exist_ok=True)
print(f"✓ 创建目录: {tmp_dir}")

# 设置 run.sh 可执行权限
run_sh = pathlib.Path(__file__).parent / "run.sh"
if run_sh.exists():
    run_sh.chmod(run_sh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"✓ 设置执行权限: {run_sh}")

print("\n环境设置完成！")
print("可以运行: ./run.sh")
