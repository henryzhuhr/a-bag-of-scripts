from enum import StrEnum


class PhotoFormat(StrEnum):
    """文件格式"""

    JPG = ".jpg"
    """JPEG 图片格式"""

    JPEG = ".jpeg"
    """JPEG 图片格式"""

    PNG = ".png"

    TIFF = ".tiff"

    DNG = ".dng"

    SONY_RAW = ".arw"
    """索尼 RAW"""


EXIF_SUPPORTED_FILE_EXT = [
    PhotoFormat.SONY_RAW,
    PhotoFormat.DNG,
    # ".raf",# 富士
    PhotoFormat.JPG,
    PhotoFormat.JPEG,
]

HEIF_SUPPORTED_FILE_EXT = [".heif", ".heic", ".hif"]
