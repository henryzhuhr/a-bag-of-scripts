"""
基于通用任务框架的 RAW 照片重命名任务
"""

from venv import logger

from modules.photograph._enums.photo import PhotographDir
from modules.photograph._types.photo import FileTag
from modules.photograph.tasks.rename_raw_photo import (
    RenameRawPhotoTask,
    RenameRawPhotoTaskConfig,
)
from modules.task.task_manager import TaskManager

TASK_NAME = "rename-raw-photo"


def main():
    BASE_DIR = PhotographDir.ICLOUD_RAW_PHOTO
    FILE_TAG_LIST = [
        FileTag(tag="XXXX", dir=f"{BASE_DIR}/200101-XXXX_副本"),
    ]

    config = RenameRawPhotoTaskConfig(
        name=TASK_NAME,
        file_tag_list=FILE_TAG_LIST,
    )
    manager = TaskManager()
    task = RenameRawPhotoTask(config)
    manager.register_task(task)
    print(task.describe())
    # 执行（模拟）
    try:
        manager.execute(TASK_NAME, dry_run=True)
        manager.execute(TASK_NAME)
    except Exception as e:
        logger.error(f"failed to execute task: {e}")

    # 真正执行
    # manager.execute_task(TASK_NAME)


if __name__ == "__main__":
    main()
