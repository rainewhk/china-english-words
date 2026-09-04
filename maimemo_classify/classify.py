import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent
SENIOR_OLD_FILE = BASE_DIR / "senoir_old.txt"

# 预加载高中文件名单
SENIOR_OLD_SET = set()
if SENIOR_OLD_FILE.exists():
    with open(SENIOR_OLD_FILE, "r", encoding="utf-8") as f:
        SENIOR_OLD_SET = {line.strip() for line in f if line.strip()}


def get_target_dir(filename: str) -> str | None:
    """根据文件名判断目标文件夹名称，方便后续随时加 if 规则"""
    if filename in SENIOR_OLD_SET:
        return "高中（旧）"
    if "选修" in filename:
        return "高中（选）"
    if (
        "高中" in filename
        or "初中" in filename
        or "年级" in filename
        or "高一" in filename
        or "高二" in filename
        or "高三" in filename
        or "高考" in filename
    ):
        return "高中（新）"

    if "雅思" in filename or "IELTS" in filename:
        return "雅思"
    if "托福" in filename or "TOEFL" in filename:
        return "托福"


    if "考研" in filename or "研究生" in filename:
        return "研究生英语"
    if "考博" in filename or "博士" in filename:
        return "博士生英语"

    if (
        "专四" in filename
        or "专八" in filename
        or "专4" in filename
        or "专8" in filename
    ):
        return "专业英语"

    if "四级" in filename or "4级" in filename:
        return "大学英语四级"

    if "六级" in filename or "6级" in filename:
        return "大学英语六级"

    if "大学" in filename or "等级" in filename:
        return "大学英语"

    # return "其他"
    return None


def classify_exported_files():
    exported_dir = BASE_DIR / "exported"
    if not exported_dir.exists():
        print(f"目录不存在: {exported_dir}")
        return

    for file_path in exported_dir.iterdir():
        if not file_path.is_file():
            continue

        target_name = get_target_dir(file_path.name)
        if target_name:
            target_dir = BASE_DIR / target_name
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file_path), str(target_dir / file_path.name))


if __name__ == "__main__":
    classify_exported_files()
