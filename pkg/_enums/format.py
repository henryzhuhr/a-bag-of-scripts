from enum import StrEnum


class FilenameRule(StrEnum):
    """文件名重命名规则"""

    STANDAERD_DATETIME = "{year}{month:02d}{day:02d}_{hour:02d}{minute:02d}{second:02d}"
    """标准日期格式 YYYYMMDD_HHMMSS"""

    DATE = "{year}{month:02d}{day:02d}"
    """日期格式"""

    TIME = "{hour:02d}{minute:02d}{second:02d}"
    """时间格式"""

    ALBUM = "{album}"
    """相册名"""

    DEFAULT = f"{str(ALBUM)}_{str(TIME)}"
    """默认格式"""


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
