import argparse
import os
import typing

from pkg._types.photo import FileTag
from pkg.task_manager.task import Processor, Task, TaskManager

# ================== 目录路径设置 ==================
ICLOUD_DIR = r"$HOME/Library/Mobile Documents/com~apple~CloudDocs"  # iCloud 目录
BASE_DIR = f"{ICLOUD_DIR}/Photograph-local"
# BASE_DIR = f"{ICLOUD_DIR}/Panorama-local"
FILE_TAG_LIST: typing.List[FileTag] = [
    # fmt: off
    FileTag(tag="珠海长隆海洋王国", dir=f"{BASE_DIR}/250524-珠海长隆海洋王国"),
    # fmt: on
]


class RenameSonyPhotoProcessor(Processor):
    def __init__(self) -> None:
        super().__init__()


class RenameDJIPhotoProcessor(Task):
    def __init__(self) -> None:
        super().__init__()


def main():
    task_manager = TaskManager()
    task_manager.register_processor(RenameSonyPhotoProcessor())
    task_manager.register_processor(RenameDJIPhotoProcessor())


if __name__ == "__main__":
    main()
