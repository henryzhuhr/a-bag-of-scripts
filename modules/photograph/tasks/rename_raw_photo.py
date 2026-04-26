"""
基于通用任务框架的 RAW 照片重命名任务
"""

import os
from typing import List, Optional

from loguru import logger
from pydantic import ConfigDict, Field

from modules.photograph._enums.format import SidecarFormat, XMPFormat
from modules.photograph._enums.photo import SupportedPhotoHeifExt, SupportedPhotoRawExt
from modules.photograph.plugins.metadata import (
    DEFAULT_ENTRY_POINT_GROUP,
    PhotoMetadataPlugin,
    PhotoMetadataPluginRegistry,
    default_metadata_plugins,
    load_plugins_from_entry_points,
    load_plugins_from_module_paths,
    normalize_extension,
)
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

    metadata_plugins: Optional[List[PhotoMetadataPlugin]] = Field(
        default=None,
        description="显式传入的元数据插件。为空时使用内置默认插件",
    )
    """显式传入的元数据插件"""

    metadata_plugin_modules: List[str] = Field(
        default_factory=list,
        description="显式加载的元数据插件模块路径",
    )
    """显式加载的元数据插件模块路径"""

    load_entry_point_plugins: bool = Field(
        default=False,
        description="是否加载 Python entry points 中的元数据插件",
    )
    """是否加载 Python entry points 中的元数据插件"""

    metadata_plugin_entry_point_group: str = Field(
        default=DEFAULT_ENTRY_POINT_GROUP,
        description="元数据插件 entry point group",
    )
    """元数据插件 entry point group"""

    ignored_extensions: List[str] = Field(
        default_factory=lambda: [SidecarFormat.XMP.value, SidecarFormat.ACR.value],
        description="扫描时忽略的附属文件扩展名",
    )
    """扫描时忽略的附属文件扩展名"""

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
        self._metadata_plugin_registry = self._build_metadata_plugin_registry()
        self.process_tasks: List[ProcessTask] = self._find_all_files()
        """处理任务列表"""

    def name(self) -> str:
        return self.config.name

    def describe(self) -> str:
        return f"task [{self.config.name}] with {len(self.process_tasks)} files to process."

    @property
    def process_task_list(self) -> List[ProcessTask]:
        """兼容旧调用方，内部统一使用 process_tasks。"""
        return self.process_tasks

    def _build_metadata_plugin_registry(self) -> PhotoMetadataPluginRegistry:
        metadata_plugins = self.config.metadata_plugins
        if metadata_plugins is None:
            metadata_plugins = default_metadata_plugins(
                self.config.exif_supported_ext,
                self.config.heif_supported_ext,
            )
        else:
            metadata_plugins = list(metadata_plugins)

        metadata_plugins.extend(
            load_plugins_from_module_paths(self.config.metadata_plugin_modules)
        )
        if self.config.load_entry_point_plugins:
            metadata_plugins.extend(
                load_plugins_from_entry_points(
                    self.config.metadata_plugin_entry_point_group
                )
            )

        return PhotoMetadataPluginRegistry(
            metadata_plugins,
            ignored_extensions=self.config.ignored_extensions,
        )

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
            for file in sorted(os.listdir(file_tag.dir)):
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

        normalized_ext = normalize_extension(file_ext)
        if self._metadata_plugin_registry.is_ignored(normalized_ext):
            return []

        metadata_plugin = self._metadata_plugin_registry.find(normalized_ext)
        if metadata_plugin is None:
            raise ValueError(
                f"unsupported file type '{file_ext}' for file '{file_path}'"
            )
        date_time = metadata_plugin.read_original_datetime(file_path)

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

        for ext in metadata_plugin.sidecar_extensions:
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
        """兼容旧内部逻辑：判断文件是否可能包含 xmp 文件。"""
        _, file_ext = os.path.splitext(file)
        metadata_plugin = self._metadata_plugin_registry.find(file_ext)
        if metadata_plugin is None:
            return False
        return XMPFormat.XMP.value in metadata_plugin.sidecar_extensions

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
