import os
import stat
from datetime import datetime

import exifread
import piexif
import pillow_heif

from pkg._enums.format import EXIF_SUPPORTED_FILE_EXT, HEIF_SUPPORTED_FILE_EXT
from pkg._types.photo import ExifData, PhotoInfo


class XExif:
    @staticmethod
    def exif_supported_format(image_file: str) -> bool:
        pass

    @staticmethod
    def get_exif_data(file_path: str) -> dict:
        """获取图片文件的 EXIF 数据

        Args:
            file_path (str): 图片文件路径

        Returns:
            dict: _description_
        """
        # 获取
        file_base, file_ext = os.path.splitext(file_path)

        if file_ext.lower() in EXIF_SUPPORTED_FILE_EXT:
            with open(file_path, "rb") as f:
                exif_data = exifread.process_file(f, details=False, strict=True)
                date_time = exif_data["EXIF DateTimeOriginal"].printable
        elif file_ext.lower() in HEIF_SUPPORTED_FILE_EXT:
            # reference from: https://github.com/bigcat88/pillow_heif/blob/master/examples/heif_dump_info.py
            heif_file = pillow_heif.open_heif(file_path)
            exif_dict = piexif.load(heif_file.info["exif"], key_is_name=True)
            exif_data = exif_dict["Exif"]
            date_time = exif_data["DateTimeOriginal"]
            date_time = str(date_time, "utf-8")


class XPhoto:
    photo_info: PhotoInfo
    """图片信息"""

    def __init__(self, file_path: str):
        self.photo_info = XPhoto.get_photo_info(file_path)

    @staticmethod
    def get_photo_info(file_path: str) -> PhotoInfo:
        """获取图片信息

        Args:
            file_path (str): 图片文件路径

        Returns:
            PhotoInfo: 图片信息
        """
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1]

        exif_data = XPhoto.get_exif_data(file_path)

        return PhotoInfo(
            file_name=file_name,
            file_ext=file_ext,
            file_path=file_path,
            exif_data=exif_data,
        )

    @staticmethod
    def get_exif_data(file_path: str) -> dict:
        """获取图片文件的 EXIF 数据
        Args:
            file_path (str): 图片文件路径
        Returns:
            dict: EXIF 数据
        """
        file_base, file_ext = os.path.splitext(file_path)

        if file_ext.lower() in EXIF_SUPPORTED_FILE_EXT:
            with open(file_path, "rb") as f:
                exif_data = exifread.process_file(f, details=False, strict=True)
                exif_date_time_original = exif_data["EXIF DateTimeOriginal"].printable
                # print(exif_data.keys())
                date_time_original = datetime.strptime(
                    exif_date_time_original, "%Y:%m:%d %H:%M:%S"
                )
        elif file_ext.lower() in HEIF_SUPPORTED_FILE_EXT:
            # reference from: https://github.com/bigcat88/pillow_heif/blob/master/examples/heif_dump_info.py
            heif_file = pillow_heif.open_heif(file_path)
            exif_dict = piexif.load(heif_file.info["exif"], key_is_name=True)
            exif_data = exif_dict["Exif"]
            date_time_original = exif_data["DateTimeOriginal"]
            date_time_original = str(date_time_original, "utf-8")
        else:
            raise ValueError(f"Unsupported file({file_path}) format: {file_ext}")

        return ExifData(
            date_time_original=date_time_original,
        )
