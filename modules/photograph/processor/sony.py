"""索尼文件处理器"""

import typing
from datetime import datetime
from pathlib import Path

import exifread
import piexif
import pillow_heif
from loguru import logger

from .._enums.format import FilenameRule
from .._enums.photo import ExifImageMake
from ..task_manager.task import BaseTask
from ..utils._exif import ExifInfo


class RenameSonyRawPhotoTask(BaseTask):
    """重命名索尼RAW照片任务，用于处理单个 .ARW 文件及其对应的 .XMP 文件"""

    _file_path: Path
    """文件路径"""

    _album_name: str
    """相册名称"""

    def __init__(self, file_path: typing.Union[Path, str], album_name: str):
        """
        初始化索尼原始照片任务

        Args:
          file_path (Union[Path, str]): 文件路径，可以是字符串或 Path 实例
          album_name (str): 相册名称，用于标识照片所属的相册
        """
        super().__init__()

        if isinstance(file_path, str):
            self._file_path = Path(file_path)
        elif isinstance(file_path, Path):
            self._file_path = file_path
        else:
            raise TypeError("file_path must be a str or Path instance")

        self._album_name = album_name

        self.set_rename_rule()

        # 默认规则
        self.rename_rule = "{date}-{album}-{time}"

    @classmethod
    def must_match(cls, obj: Path):
        """检查文件是否是索尼的RAW文件"""
        try:
            # 「检查点」 检查输入对象是否是 Path 实例，且是否存
            if not isinstance(obj, Path) or not obj.exists():
                raise FileExistsError(f"file does not exist: {obj}")

            # 「检查点」 检查文件后缀是否为 .ARW / .arw
            if obj.suffix.lower() != ".arw":
                raise TypeError(f"file extension must be .ARW / .arw, got {obj.suffix}")

            # 「检查点」 使用exif 读取照片，检查
            exif_info = ExifInfo(obj)
            if exif_info.camera_make != ExifImageMake.SONY:
                raise ValueError(
                    f"file {obj} is not a Sony RAW photo, camera make is {exif_info.camera_make}"
                )
        except Exception as e:
            raise ValueError(f"reading EXIF data from file '{obj}' error: {e}")

    def create(self) -> None:
        try:
            self.must_match(self._file_path)
        except Exception as e:
            logger.warning(f"file '{self._file_path}' does not match this task: {e}")
            return

        try:
            exif_info = ExifInfo(self._file_path)
            # 获取拍摄时间
            shot_time = exif_info.original_datetime
            print(shot_time)
        except Exception as e:
            logger.warning(f"获取 EXIF 时间失败: {e}")
            # 如果获取 EXIF 时间失败，使用文件修改时间
            shot_time = datetime.fromtimestamp(self._file_path.stat().st_mtime)

        self._ready = True

    def description(self, dry_run: bool = True) -> str:
        """返回任务描述"""
        try:
            new_name = self._generate_new_filename()
            return f"重命名 {self._file_path.name} -> {new_name}.ARW"
        except Exception as e:
            raise RuntimeError(f"生成新文件名失败: {e}") from e

    def execute(self, dry_run: bool = True) -> None:
        """
        执行当前任务
        :param  : 是否为模拟执行
        """
        logger.info(
            f"Executing task for {self._file_path} in album {self._album_name}, dry_run={dry_run}"
        )
        # 这里可以添加执行任务的逻辑
        if not self._ready:
            raise RuntimeError("task not generated yet.")
        if dry_run:
            logger.info(self.description(dry_run=True))
        else:
            # 实际执行重命名或其他操作
            pass

    def _get_exif_datetime(self) -> datetime:
        """
        使用 exiftool 获取照片的拍摄时间
        :return: 格式化的时间字符串 HHMMSS
        """

        logger.debug(f"获取文件 {self._file_path} 的 EXIF 时间")

        # 检查文件后缀
        file_suffix = self._file_path.suffix.lower()

        # 对 RAW 和 HEIF 文件使用不同的处理方式
        EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"
        if file_suffix in [".arw", ".dng"]:
            with open(self._file_path, "rb") as f:
                exif_data = exifread.process_file(f, details=False, strict=True)
                # logger.debug(f"EXIF data of '{self._file_path}': {exif_data}")
            date_time = exif_data["EXIF DateTimeOriginal"].printable
            if isinstance(date_time, str):
                date_time = datetime.strptime(date_time, EXIF_DATETIME_FORMAT)
            else:
                raise ValueError(
                    f"EXIF DateTimeOriginal of ARW file is type {type(date_time)}, expected str"
                )
        elif file_suffix in [".heif", ".heic", ".hif"]:
            # reference from: https://github.com/bigcat88/pillow_heif/blob/master/examples/heif_dump_info.py
            heif_file = pillow_heif.open_heif(self._file_path)
            exif_dict = piexif.load(heif_file.info["exif"], key_is_name=True)
            exif_data = exif_dict["Exif"]
            date_time = exif_data["DateTimeOriginal"]
            date_time = str(date_time, "utf-8")
            date_time = datetime.strptime(date_time, EXIF_DATETIME_FORMAT)
        else:
            raise ValueError(f"Unsupported file type: {file_suffix}")
        logger.debug(f"获取到的 EXIF 时间: {date_time}")
        return date_time

    def _generate_new_filename(self) -> str:
        """
        生成新的文件名
        :return: 新文件名（不含扩展名）
        """
        datestr = self._get_exif_datetime()
        print(f"获取到的时间字符串: {datestr}")
        exit()
        pass

    def set_rename_rule(self, rule: FilenameRule = FilenameRule.DEFAULT):
        """设置重命名规则"""
        self.rename_rule = rule


def _test():
    """测试函数，用于演示如何使用 RenameSonyRawPhotoTask"""

    logger.debug("Debugging RenameSonyRawPhotoTask")

    album_dir: Path = Path(".cache/Photograph-local") / "YYMMDD-相册名"
    album_name = "相册名"
    dry_run: bool = True

    if not album_dir.exists():
        logger.error(f"album_dir does not exist: {album_dir}")
        return

    raw_files = list(album_dir.glob("*.ARW"))
    if not raw_files:
        logger.error(f"No ARW files found in {album_dir}")
        return

    for raw_file in raw_files:
        task = RenameSonyRawPhotoTask(raw_file, album_name)
        task.create()
        task.execute(dry_run)
        break  # for testing, remove this break to process all files


if __name__ == "__main__":
    _test()
