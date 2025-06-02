from datetime import datetime
from pathlib import Path

import exifread

from pkg._enums.photo import ExifImageMake


class ExifInfo:
    def __init__(self, file_path: Path):
        self._exifdata = self.get_exifdata(file_path)

    def get_exifdata(self, file_path: Path):
        """
        获取图片的 EXIF 数据
        :return: 包含 EXIF 数据的字典
        """
        # 获取全部的 EXIF 数据

        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist.")
        if not file_path.is_file():
            raise TypeError(f"Expected a file, but got a directory: {file_path}")
        with open(file_path, "rb") as f:
            try:
                # 使用 exifread 读取 EXIF 数据
                # details=False 只返回基本信息，strict=True 确保严格解析
                # 如果需要更多详细信息，可以将 details 设置为 True
                # strict=True 确保严格解析，避免不符合规范的数据
                exif_data = exifread.process_file(f, details=False, strict=True)
            except Exception as e:
                raise ValueError(f"Error reading EXIF data from file {file_path}: {e}")
            return exif_data

    @property
    def exifdata(self) -> dict:
        """
        获取 EXIF 数据
        :return: 包含 EXIF 数据的字典
        """
        return self._exifdata

    @property
    def camera_make(self) -> ExifImageMake:
        """
        获取相机制造商
        :return: 相机制造商字符串
        """
        make = self._exifdata.get("Image Make", None)
        if make is None:
            return ExifImageMake.UNKNOWN

        try:
            return ExifImageMake.from_string(str(make))
        except Exception as e:
            raise ValueError(f"Error parsing camera make from EXIF data: {e}")

    @property
    def original_datetime(self) -> datetime:
        """
        获取原始拍摄时间
        :return: 拍摄时间
        """
        datetime_str = self._exifdata.get("EXIF DateTimeOriginal", None)
        if datetime_str is None:
            raise ValueError("EXIF DateTimeOriginal not found in EXIF data")

        print(datetime_str)
        try:
            return datetime.strptime(str(datetime_str), "%Y:%m:%d %H:%M:%S")
        except ValueError as e:
            raise ValueError(f"Error parsing original datetime from EXIF data: {e}")
