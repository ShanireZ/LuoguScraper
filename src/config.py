import os
import pathlib

# 使用 pathlib 处理路径，具有更好的跨平台性和可读性
# .resolve() 确保获取绝对路径，避免符号链接问题
_BASE_PATH = pathlib.Path(__file__).resolve().parent.parent

# 导出为 str 类型，最大限度兼容 os.path 和字符串拼接操作
BASE_DIR: str = str(_BASE_PATH)
JSON_DIR: str = str(_BASE_PATH / "json")
OPT_DIR: str = str(_BASE_PATH / "opt")

# 文件路径配置
UIDS_FILE: str = str(_BASE_PATH / "uids.xlsx")
OUTPUT_FILE: str = str(_BASE_PATH / "opt" / "luogu_analysis.xlsx")

# Luogu Config
# 允许通过环境变量覆盖 URL，便于测试或应对 API 变更
LUOGU_BASE_URL: str = (
    os.getenv("LUOGU_BASE_URL", "https://www.luogu.com.cn/record/list")
    or "https://www.luogu.com.cn/record/list"
)

# 注意：
# 此配置文件不应包含副作用（如创建目录）。
# 目录的创建应由具体使用该目录的业务代码（如 utils.ensure_dir）负责。

if __name__ == "__main__":
    # 快速调试配置信息
    print(f"Configuration loaded from: {__file__}")
    print("-" * 40)
    print(f"{'BASE_DIR:':<15} {BASE_DIR}")
    print(f"{'JSON_DIR:':<15} {JSON_DIR}")
    print(f"{'OPT_DIR:':<15} {OPT_DIR}")
    print("-" * 40)
    print(f"{'UIDS_FILE:':<15} {UIDS_FILE}")
    print(f"{'OUTPUT_FILE:':<15} {OUTPUT_FILE}")
    print(f"{'API URL:':<15} {LUOGU_BASE_URL}")
