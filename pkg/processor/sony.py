"""索尼文件处理器"""

import typing
from abc import ABC, abstractmethod
from pathlib import Path

from loguru import logger

from pkg._enums.format import FilenameRule
from pkg._enums.photo import PhotographDir


class BaseTask(ABC):
    """任务基类"""

    @abstractmethod
    def generate(self) -> None:
        """生成任务方法，子类需要实现此方法"""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def description(self) -> str:
        """返回任务描述、，模拟执行时使用"""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def execute(self, dry_run: bool = True) -> None:
        """
        执行当前任务
        :param dry_run: 是否为模拟执行
        """
        raise NotImplementedError("Subclasses must implement this method")


class TaskManager:
    """任务管理器，用于注册和管理处理器任务"""

    task_list: typing.List[BaseTask]
    """任务列表，存储所有注册的处理器"""

    def __init__(self):
        self.task_list = []


class RenameSonyRawPhotoTask(BaseTask):
    """索尼相机原始照片任务，用于处理单个 .ARW 文件及其对应的 .XMP 文件"""

    file_path: Path
    """文件路径"""

    album_name: str
    """相册名称"""

    def __init__(self, file_path: typing.Union[Path, str], album_name: str):
        """
        初始化索尼原始照片处理器

        Args:
          file_path (Union[Path, str]): 文件路径，可以是字符串或 Path 实例
          album_name (str): 相册名称，用于标识照片所属的相册
        """
        super().__init__()

        if isinstance(file_path, str):
            self.file_path = Path(file_path)
        elif isinstance(file_path, Path):
            self.file_path = file_path
        else:
            raise TypeError("file_path must be a str or Path instance")

        self.album_name = album_name

        self.set_rename_rule()

    def set_rename_rule(self, rule: FilenameRule = FilenameRule.DEFAULT):
        """设置重命名规则"""
        self.rename_rule = rule

    def generate(self) -> None:
        """生成重命名任务"""
        logger.debug(f"Generating task for {self.file_path} in album {self.album_name}")
        # 这里可以添加生成任务的逻辑

    def execute(self, dry_run: bool = True) -> None:
        """
        执行当前任务
        :param dry_run: 是否为模拟执行
        """
        logger.info(
            f"Executing task for {self.file_path} in album {self.album_name}, dry_run={dry_run}"
        )
        # 这里可以添加执行任务的逻辑
        if dry_run:
            logger.info("This is a dry run, no changes will be made.")
        else:
            # 实际执行重命名或其他操作
            pass


if __name__ == "__main__":
    # 示例用法
    file_path = Path(PhotographDir.LOCAL_RAW_PHOTO) / "YYMMDD-相册名称/DSC00001.ARW"
    processor = RenameSonyRawPhotoTask(file_path=file_path, album_name="相册名称")
    logger.info(
        f"Processing file: {processor.file_path}, Album: {processor.album_name}"
    )

    task_manager = TaskManager()
