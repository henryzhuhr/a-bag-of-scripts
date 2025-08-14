"""
基于通用任务框架的 RAW 照片重命名任务
"""

import os
from typing import Any, Dict, List, Optional

import exifread
import piexif
import pillow_heif
from loguru import logger

from modules.photograph._enums.photo import PhotographDir
from modules.task.task import BaseTask
from modules.task.task_manager import TaskManager


class FileTag:
    def __init__(self, tag: str, dir: str):
        self.tag = tag
        self.dir = os.path.expanduser(os.path.expandvars(dir))


class ProcessTask:
    def __init__(self, parent_dir: str, origin_file: str, update_file: str, skip=False):
        self.parent_dir = parent_dir
        self.origin_file = origin_file
        self.update_file = update_file
        self.skip = skip


class RenameRawPhotoTask(BaseTask):
    """
    RAW照片重命名任务
    config参数:
        - file_tag_list: List[FileTag]
        - exif_supported_ext: List[str]
        - heif_supported_ext: List[str]
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.file_tag_list: List[FileTag] = []
        self.exif_supported_ext: List[str] = []
        self.heif_supported_ext: List[str] = []
        self.process_task_list: List[ProcessTask] = []
        if config:
            self.file_tag_list = config.get("file_tag_list", [])
            self.exif_supported_ext = config.get("exif_supported_ext", [])
            self.heif_supported_ext = config.get("heif_supported_ext", [])

    def generate(self) -> None:
        self.process_task_list.clear()
        for file_tag in self.file_tag_list:
            for file in os.listdir(file_tag.dir):
                if file.startswith("."):
                    continue
                file_base, file_ext = os.path.splitext(file)
                file_path = os.path.join(file_tag.dir, file)
                date_time = None
                if file_ext.lower() in self.exif_supported_ext:
                    with open(file_path, "rb") as f:
                        exif_data = exifread.process_file(f, details=False, strict=True)
                        date_time = exif_data["EXIF DateTimeOriginal"].printable
                elif file_ext.lower() in self.heif_supported_ext:
                    heif_file = pillow_heif.open_heif(file_path)
                    exif_dict = piexif.load(heif_file.info["exif"], key_is_name=True)
                    exif_data = exif_dict["Exif"]
                    date_time = exif_data["DateTimeOriginal"]
                    date_time = str(date_time, "utf-8")
                else:
                    continue
                file_date, file_time = date_time.split(" ")
                file_date = file_date.replace(":", "")[2:]
                file_time = file_time.replace(":", "")
                second_id = self.get_second_id_from_file_base(file_base)
                if second_id is None:
                    continue
                file_identification = f"{file_time}_{second_id}"
                update_name = f"{file_date}-{file_tag.tag}-{file_identification}"
                update_file = f"{update_name}{file_ext}"
                self.process_task_list.append(
                    ProcessTask(
                        parent_dir=file_tag.dir,
                        origin_file=file,
                        update_file=update_file,
                        skip=(file_base == update_name),
                    )
                )
                xmp_file = f"{file_base}.xmp"
                xmp_file_path = os.path.join(file_tag.dir, xmp_file)
                if os.path.exists(xmp_file_path):
                    self.process_task_list.append(
                        ProcessTask(
                            parent_dir=file_tag.dir,
                            origin_file=xmp_file,
                            update_file=f"{update_name}.xmp",
                            skip=(xmp_file == f"{update_name}.xmp"),
                        )
                    )

    def describe(self) -> str:
        return f"RAW照片重命名任务，共 {len(self.process_task_list)} 个待处理文件。"

    def execute(self, dry_run: bool = False) -> List[str]:
        results = []
        logger.info(f"开始执行 RAW 照片重命名任务，dry_run={dry_run}")
        for i, task in enumerate(self.process_task_list):
            logger.debug(
                f"处理文件: {task.parent_dir} / {task.origin_file} -> {task.update_file}, skip={task.skip}"
            )
            if not task.skip:
                info = (
                    f"{i}: {task.parent_dir} / {task.origin_file} -> {task.update_file}"
                )
                results.append(info)
                if not dry_run:
                    try:
                        os.rename(
                            os.path.join(task.parent_dir, task.origin_file),
                            os.path.join(task.parent_dir, task.update_file),
                        )
                        logger.info(info)
                        print(info)
                    except Exception as e:
                        results.append(f"    重命名失败: {e}")
        return results

    @staticmethod
    def get_second_id_from_file_base(file_base: str):
        if file_base.startswith("DJI"):
            second_id = file_base[-4:-2]
        elif file_base.startswith("PANO"):
            second_id = f"PANO~{file_base[-2:]}"
        elif file_base[-7:-3] == "PANO":
            second_id = f"PANO~{file_base[-2:]}"
        elif file_base.startswith("DSC"):
            second_id = file_base[-2:]
        elif file_base.startswith("IMG_"):
            second_id = file_base[-2:]
        else:
            second_id = file_base[-2:]
        return second_id


def main():
    BASE_DIR = PhotographDir.ICLOUD_RAW_PHOTO
    FILE_TAG_LIST = [
        FileTag(
            tag="CAN广州白云国际机场", dir=f"{BASE_DIR}/250727-CAN广州白云国际机场_副本"
        ),
    ]
    EXIF_SUPPORTED_FILE_EXT = [".arw", ".dng", ".raf", ".jpg", ".jpeg"]
    HEIF_SUPPORTED_FILE_EXT = [".heif", ".heic", ".hif"]

    config = {
        "file_tag_list": FILE_TAG_LIST,
        "exif_supported_ext": EXIF_SUPPORTED_FILE_EXT,
        "heif_supported_ext": HEIF_SUPPORTED_FILE_EXT,
    }
    manager = TaskManager()
    manager.register_task_type("rename_raw_photo", RenameRawPhotoTask)
    task = manager.create_task("rename_raw_photo", config)
    task.generate()
    print(task.describe())
    # 执行（模拟）
    results = manager.execute_task("rename_raw_photo", dry_run=True)
    for info in results:
        print(info)
    # 真正执行
    manager.execute_task("rename_raw_photo")


if __name__ == "__main__":
    main()
