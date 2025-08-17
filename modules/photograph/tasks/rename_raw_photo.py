"""
基于通用任务框架的 RAW 照片重命名任务
"""

import os
from typing import List

import exifread
import piexif
import pillow_heif
from loguru import logger
from pydantic import ConfigDict, Field

from modules.photograph._enums.photo import SupportedPhotoHeifExt, SupportedPhotoRawExt
from modules.photograph._types.photo import FileTag
from modules.task.task import BaseTask, BaseTaskConfig


class ProcessTask:
    def __init__(self, parent_dir: str, origin_file: str, update_file: str, skip=False):
        self.parent_dir = parent_dir
        self.origin_file = origin_file
        self.update_file = update_file
        self.skip = skip


class RenameRawPhotoTaskConfig(BaseTaskConfig):
    file_tag_list: List[FileTag] = Field(
        default_factory=list, description="文件标签列表"
    )
    """文件标签列表"""

    exif_supported_ext: List[str] = Field(
        default_factory=lambda: [e.value for e in SupportedPhotoRawExt],
        description="支持的 EXIF 文件扩展名",
    )
    """支持的 EXIF 文件扩展名"""

    heif_supported_ext: List[str] = Field(
        default_factory=lambda: [e.value for e in SupportedPhotoHeifExt],
        description="支持的 HEIF 文件扩展名",
    )
    """支持的 HEIF 文件扩展名"""

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RenameRawPhotoTask(BaseTask):
    """
    RAW照片重命名任务
    """

    config: RenameRawPhotoTaskConfig
    """任务配置"""

    def __init__(self, config: RenameRawPhotoTaskConfig):
        super().__init__(config)
        self.config = config
        self.process_task_list: List[ProcessTask] = self._find_all_files()
        """处理任务列表"""

    def name(self) -> str:
        return self.config.name

    def describe(self) -> str:
        return f"task [{self.config.name}] with {len(self.process_task_list)} files to process."

    def execute(self, dry_run: bool = False):
        logger.info(f"start executing task [{self.config.name}]，dry_run={dry_run}")

        class RenameItem:
            def __init__(self, parent_dir: str, origin_file: str, update_file: str):
                self.origin_file = os.path.join(parent_dir, origin_file)
                self.update_file = os.path.join(parent_dir, update_file)

        rename_list: List[RenameItem] = []
        for _, task in enumerate(self.process_task_list):
            if task.skip:
                logger.info(
                    f"file '{task.parent_dir}/{task.origin_file}' has been renamed, skip"
                )
                continue
            logger.info(
                f"file is to be renamed: {task.parent_dir} / '{task.origin_file}' -> '{task.update_file}'"
            )
            rename_list.append(
                RenameItem(task.parent_dir, task.origin_file, task.update_file)
            )
        if len(rename_list) == 0:
            logger.info(f"no files to rename for task [{self.config.name}]")
            return
        if not dry_run and self.confirm():
            for item in rename_list:
                try:
                    # 检查源文件是否存在
                    if not os.path.exists(item.origin_file):
                        raise FileNotFoundError(
                            f"源文件不存在，跳过: '{item.origin_file}'"
                        )

                    logger.info(f"rename '{item.origin_file}' to '{item.update_file}'")
                    os.rename(item.origin_file, item.update_file)
                except Exception as e:
                    raise RuntimeError(
                        f"rename '{item.origin_file}' to '{item.update_file}' error: {e}"
                    )

    def _find_all_files(self) -> List[ProcessTask]:
        process_task_list: List[ProcessTask] = []
        # 遍历文件夹
        for file_tag in self.config.file_tag_list:
            # 遍历文件
            for file in os.listdir(file_tag.dir):
                if file.startswith("."):
                    continue

                # 分割文件名和后缀
                file_base, file_ext = os.path.splitext(file)
                file_path = os.path.join(file_tag.dir, file)

                # 检查文件类型是否支持
                # 解析 exif 信息
                date_time = None
                if file_ext.lower() in self.config.exif_supported_ext:
                    with open(file_path, "rb") as f:
                        exif_data = exifread.process_file(f, details=False, strict=True)
                        date_time = exif_data["EXIF DateTimeOriginal"].printable
                elif file_ext.lower() in self.config.heif_supported_ext:
                    # reference from: https://github.com/bigcat88/pillow_heif/blob/master/examples/heif_dump_info.py
                    heif_file = pillow_heif.open_heif(file_path)
                    exif_dict = piexif.load(heif_file.info["exif"], key_is_name=True)
                    exif_data = exif_dict["Exif"]
                    if exif_data is None:
                        raise ValueError(
                            "metadata 'Exif' not found in file '{file_path}'"
                        )
                    date_time = exif_data["DateTimeOriginal"]
                    date_time = str(date_time, "utf-8")
                else:
                    continue

                file_date, file_time = date_time.split(" ")
                file_date = file_date.replace(":", "")[2:]
                file_time = file_time.replace(":", "")

                # 获取文件名中的秒级标识
                second_id = self._get_second_id_from_file_base(file_base)
                if second_id is None:
                    logger.info(
                        f"unknown filename format or already named: {file_tag.dir} / {file}, skip"
                    )
                    continue
                # 文件标识
                file_identification = f"{file_time}_{second_id}"

                # 更新文件名
                update_name = f"{file_date}-{file_tag.tag}-{file_identification}"
                update_file = f"{update_name}{file_ext}"

                process_task_list.append(
                    ProcessTask(
                        parent_dir=file_tag.dir,
                        origin_file=file,
                        update_file=update_file,
                        skip=(file_base == update_name),
                    )
                )

                # 检查是否存在 xmp 文件，只有 RAW 格式才有 xmp
                if not self._may_have_xmp(file):
                    continue

                xmp_file = f"{file_base}.xmp"
                xmp_file_path = os.path.join(file_tag.dir, xmp_file)
                if os.path.exists(xmp_file_path):
                    process_task_list.append(
                        ProcessTask(
                            parent_dir=file_tag.dir,
                            origin_file=xmp_file,
                            update_file=f"{update_name}.xmp",
                            skip=(xmp_file == f"{update_name}.xmp"),
                        )
                    )
        return process_task_list

    def _may_have_xmp(self, file: str) -> bool:
        """判断文件是否可能包含 xmp 文件"""
        raw_list: List[str] = []
        for e in SupportedPhotoRawExt:
            # DNG 不需要 xmp 文件，其中包含所有信息
            if e.value == SupportedPhotoRawExt.DNG:
                continue
            raw_list.append(str(e.value))
        return any(file.lower().endswith(ext) for ext in raw_list)

    def _get_second_id_from_file_base(self, file_base: str):
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
