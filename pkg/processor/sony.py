"""索尼文件处理器"""

import json
import re
import subprocess
import typing
from datetime import datetime
from pathlib import Path

import exifread
import piexif
import pillow_heif
from loguru import logger

from pkg._enums.format import FilenameRule
from pkg._enums.photo import ExifImageMake
from pkg.task_manager.task import BaseTask
from pkg.utils._exif import ExifInfo


class RenameSonyRawPhotoTask(BaseTask):
    """索尼相机原始照片任务，用于处理单个 .ARW 文件及其对应的 .XMP 文件"""

    file_path: Path
    """文件路径"""

    album_name: str
    """相册名称"""

    @classmethod
    def must_match(cls, obj: Path):
        """检查文件是否是索尼的RAW文件"""
        try:
            # 检查输入对象是否是 Path 实例，且是否存
            if not isinstance(obj, Path) or not obj.exists():
                raise FileExistsError(f"file does not exist: {obj}")

            # 检查文件后缀是否为 .ARW / .arw
            if obj.suffix.lower() != ".arw":
                raise TypeError(f"file extension must be .ARW / .arw, got {obj.suffix}")

            # 使用exif 读取照片，检查
            exif_info = ExifInfo(obj)
            if exif_info.camera_make != ExifImageMake.SONY:
                raise ValueError(
                    f"file {obj} is not a Sony RAW photo, camera make is {exif_info.camera_make}"
                )
        except Exception as e:
            raise ValueError(f"reading EXIF data from file '{obj}' error: {e}")

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

    def generate(self) -> None:
        """生成重命名任务"""
        try:
            self.must_match(self.file_path)
        except Exception as e:
            logger.warning(f"file '{self.file_path}' does not match this task: {e}")
            return

    def description(self, dry_run: bool = True) -> str:
        """返回任务描述"""
        try:
            new_name = self._generate_new_filename()
            return f"重命名 {self.file_path.name} -> {new_name}.ARW"
        except Exception as e:
            return f"重命名 {self.file_path.name} (错误: {e})"

    def execute(self, dry_run: bool = True) -> None:
        """
        执行当前任务
        :param dry_run: 是否为模拟执行
        """
        # logger.info(
        #     f"Executing task for {self.file_path} in album {self.album_name}, dry_run={dry_run}"
        # )
        # 这里可以添加执行任务的逻辑
        if dry_run:
            logger.info(self.description(dry_run=True))
        else:
            # 实际执行重命名或其他操作
            pass

    def _get_exif_datetime(self) -> str:
        """
        使用 exiftool 获取照片的拍摄时间
        :return: 格式化的时间字符串 HHMMSS
        """
        try:
            # 使用 exiftool 获取 EXIF 数据
            result = subprocess.run(
                ["exiftool", "-json", "-DateTimeOriginal", str(self.file_path)],
                capture_output=True,
                text=True,
                check=True,
            )

            exif_data = json.loads(result.stdout)[0]
            date_time_original = exif_data.get("DateTimeOriginal")

            if not date_time_original:
                raise ValueError("无法获取拍摄时间")

            # 解析时间格式 "YYYY:MM:DD HH:MM:SS"
            dt = datetime.strptime(date_time_original, "%Y:%m:%d %H:%M:%S")
            return dt.strftime("%H%M%S")

        except (
            subprocess.CalledProcessError,
            json.JSONDecodeError,
            ValueError,
            KeyError,
        ) as e:
            print(f"获取 EXIF 时间失败: {e}")
            # 如果无法获取 EXIF 时间，使用文件修改时间
            mtime = datetime.fromtimestamp(self.file_path.stat().st_mtime)
            return mtime.strftime("%H%M%S")

    def _generate_new_filename(self) -> str:
        """
        生成新的文件名
        :return: 新文件名（不含扩展名）
        """
        date_part = self._extract_date_from_album_name()
        time_part = self._get_exif_datetime()

        # 去掉日期前缀，获取纯相册名称
        album_only = re.sub(r"^\d{6}-", "", self.album_name)

        return f"{date_part}-{album_only}-{time_part}"

    def set_rename_rule(self, rule: FilenameRule = FilenameRule.DEFAULT):
        """设置重命名规则"""
        self.rename_rule = rule

    def _extract_date_from_album_name(self) -> str:
        """
        从相册名称中提取日期部分
        :return: YYMMDD 格式的日期
        """
        # 匹配 YYMMDD-相册名称 格式
        match = re.match(r"^(\d{6})-", self.album_name)
        if match:
            return match.group(1)
        else:
            raise ValueError(f"无法从相册名称 '{self.album_name}' 中提取日期")


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
        processor = RenameSonyRawPhotoTask(raw_file, album_name)
        logger.info(
            f"Processing file: {processor.file_path}, Album: {processor.album_name}"
        )
        processor.generate()
        processor.execute(dry_run)
        break  # for testing, remove this break to process all files


if __name__ == "__main__":
    _test()
