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

from modules.photograph._enums.format import PhotoFormat, XMPFormat
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
        self.process_tasks: List[ProcessTask] = self._find_all_files()
        """处理任务列表"""

    def name(self) -> str:
        return self.config.name

    def describe(self) -> str:
        return f"task [{self.config.name}] with {len(self.process_tasks)} files to process."

    def execute(self, dry_run: bool = False):
        logger.info(f"start executing task [{self.config.name}]，dry_run={dry_run}")

        class RenameItem:
            def __init__(self, parent_dir: str, origin_file: str, update_file: str):
                self.origin_file = os.path.join(parent_dir, origin_file)
                self.update_file = os.path.join(parent_dir, update_file)

        rename_list: List[RenameItem] = []
        for _, task in enumerate(self.process_tasks):
            if task.skip:
                # {task.parent_dir}/
                logger.info(f"file '{task.origin_file}' has been renamed, skip")
                continue
            logger.info(
                f"file is to be renamed: '{task.origin_file}'->'{task.update_file}'"
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
        class FileTagItem:
            def __init__(self, file: str, tag: FileTag):
                self.file = file
                self.tag = tag

        file_tag_items: List[FileTagItem] = []
        # 遍历文件夹
        for file_tag in self.config.file_tag_list:
            # 遍历文件
            for file in os.listdir(file_tag.dir):
                file_tag_items.append(FileTagItem(file, file_tag))

        # 拆开两个逻辑的目的是为了避免文件夹不存在或者其他文件系统的错误
        # 所以先获取全部文件，再生成处理任务

        process_tasks: List[ProcessTask] = []
        for item in file_tag_items:
            tasks = self._generat_task(item.file, item.tag)
            process_tasks.extend(tasks)
        return process_tasks

    def _generat_task(self, file: str, file_tag: FileTag) -> List[ProcessTask]:
        if file.startswith("."):
            return []

        # 分割文件名和后缀(后缀包含 .)
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
                raise ValueError("metadata 'Exif' not found in file '{file_path}'")
            date_time = exif_data["DateTimeOriginal"]
            date_time = str(date_time, "utf-8")
        elif file_ext.lower() in [
            XMPFormat.XMP,
        ]:
            return []
        elif file_ext.lower() in [
            PhotoFormat.JPG,
            PhotoFormat.JPEG,
        ]:
            with open(file_path, "rb") as f:
                exif_data = exifread.process_file(f, details=False, strict=True)
                date_time = exif_data["EXIF DateTimeOriginal"].printable
        else:
            raise ValueError(
                f"unsupported file type '{file_ext}' for file '{file_path}'"
            )

        file_date, file_time = date_time.split(" ")
        file_date = file_date.replace(":", "")  # 年月日
        file_time = file_time.replace(":", "")  # 时分秒

        # 获取文件名中的秒级标识
        # 文件标识
        fileid = self._get_fileid(file_base, file_time)
        if fileid is None:
            logger.info(
                f"unknown filename format or already named: {file_tag.dir} / {file}, skip"
            )
            raise ValueError(
                f"unknown filename format or already named, file='{file_tag.dir}/{file_base}'"
            )

        # 更新文件名
        update_name = f"{file_date}-{file_tag.tag}-{fileid}"
        update_file = f"{update_name}{file_ext}"

        file_tasks = [
            ProcessTask(
                parent_dir=file_tag.dir,
                origin_file=file,
                update_file=update_file,
                skip=(file_base == update_name),
            )
        ]

        # 检查 RAW 文件是否存在附属文件(xmp)
        if self._may_have_xmp(file):
            ext = XMPFormat.XMP.value
            attached_file = f"{file_base}{ext}"
            file_path = os.path.join(file_tag.dir, attached_file)
            if os.path.exists(file_path) and (
                # 这个判断条件是为了确保严格校验文件后缀，因为在 mac 系统中不区分文件后缀的大小写
                # 同时，这也是为什么要重新生成一个 extensions 包含 attached_file_exts 中大小写两种形式
                os.path.basename(file_path) in os.listdir(os.path.dirname(file_path))
            ):
                task = ProcessTask(
                    parent_dir=file_tag.dir,
                    origin_file=attached_file,
                    update_file=f"{update_name}{ext}",
                    skip=(attached_file == f"{update_name}{ext}"),
                )
                file_tasks.append(task)
        return file_tasks

    def _may_have_xmp(self, file: str) -> bool:
        """判断文件是否可能包含 xmp 文件"""
        raw_list: List[str] = []
        for e in SupportedPhotoRawExt:
            # DNG 不需要 xmp 文件，其中包含所有信息
            # if e.value == SupportedPhotoRawExt.DNG:
            #     continue
            raw_list.append(str(e.value))
        return any(file.lower().endswith(ext) for ext in raw_list)

    def _get_fileid(self, file_base: str, file_time: str):
        file_base_list = str(file_base).split("-")
        if len(file_base_list) == 3:
            return file_base_list[-1]

        if len(file_base_list) == 1:
            return f"{file_time}_{file_base_list[0]}"
        return None

        # name = file_base_list[-1]
        # print(file_base, file_base_list, name)
        # if file_base.startswith("DJI"):
        #     name = file_base[-4:-2]
        # elif file_base.startswith("PANO"):
        #     name = f"PANO~{file_base[-2:]}"
        # elif file_base[-7:-3] == "PANO":
        #     name = f"PANO~{file_base[-2:]}"
        # elif file_base.startswith("IMG_"):
        #     name = file_base[-2:]
        return id
