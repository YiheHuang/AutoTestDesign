"""提交包中的测试脚本路径初始化。"""

import os
import sys


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_ROOT = os.path.dirname(CURRENT_DIR)
TARGET_APP_ROOT = os.path.join(PACKAGE_ROOT, "target_app")

for path in (PACKAGE_ROOT, TARGET_APP_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)
