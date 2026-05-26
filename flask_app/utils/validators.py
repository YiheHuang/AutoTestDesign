"""验证函数"""

import re
from flask_app.config import TASK_PRIORITIES, TASK_STATUSES


def validate_username(username):
    if not username or not isinstance(username, str):
        return False, "用户名为空"
    if len(username) < 3:
        return False, "用户名长度不能少于3个字符"
    if len(username) > 20:
        return False, "用户名长度不能超过20个字符"
    if not re.match(r'^[a-zA-Z0-9]+$', username):
        return False, "用户名只能包含字母和数字"
    return True, ""


def validate_password(password):
    if not password or not isinstance(password, str):
        return False, "密码不能为空"
    if len(password) < 8:
        return False, "密码长度不能少于8个字符"
    if len(password) > 32:
        return False, "密码长度不能超过32个字符"
    categories = 0
    if re.search(r'[A-Z]', password):
        categories += 1
    if re.search(r'[a-z]', password):
        categories += 1
    if re.search(r'[0-9]', password):
        categories += 1
    if re.search(r'[^a-zA-Z0-9]', password):
        categories += 1
    if categories < 3:
        return False, "密码需包含大写字母、小写字母、数字和特殊字符中的至少三种"
    return True, ""


def validate_email(email):
    if not email or not isinstance(email, str):
        return False, "邮箱不能为空"
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "请输入有效的邮箱地址"
    return True, ""


def validate_age(age):
    if age is None:
        return False, "年龄不能为空"
    try:
        age_int = int(age)
    except (ValueError, TypeError):
        return False, "年龄必须为整数"
    if age_int < 18:
        return False, "未成年不可注册（需年满18岁）"
    if age_int > 120:
        return False, "请输入有效年龄（18-120）"
    return True, ""


def validate_task_title(title):
    if not title or not isinstance(title, str):
        return False, "任务标题为空"
    if len(title.strip()) < 1:
        return False, "任务标题不能为空"
    if len(title) > 200:
        return False, "任务标题不能超过200个字符"
    return True, ""


def validate_task_priority(priority):
    # BUG #4: 未做严格枚举校验，错误输入静默设为 Medium
    if not priority or priority not in TASK_PRIORITIES:
        return "Medium"
    return priority


def validate_task_status(status):
    # BUG #8: 状态非法值时没有拒绝，而是静默设为todo。需求规定应拒绝非法状态值
    if not status or status not in TASK_STATUSES:
        return "todo"
    return status


def validate_project_name(name):
    if not name or not isinstance(name, str):
        return False, "项目名称为空"
    # BUG #9: 未检查纯空格名称。需求规定名称不能为空，但 "   " (空格) 通过验证
    if len(name) > 100:
        return False, "项目名称不能超过100个字符"
    return True, ""
