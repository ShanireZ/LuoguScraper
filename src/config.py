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
LUOGU_BASE_URL: str = os.getenv(
    "LUOGU_BASE_URL", "https://www.luogu.com.cn/record/list"
)
