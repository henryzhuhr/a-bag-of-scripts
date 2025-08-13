import os
from enum import StrEnum

_INTERNAL_ICLOUD_DIR = os.path.expandvars(
    r"$HOME/Library/Mobile Documents/com~apple~CloudDocs"
)
"""内部 iCloud 目录，不对外暴露"""

_INTERNAL_LOCAL_DIR = os.path.expandvars(r"$HOME")
"""内部本地目录，不对外暴露"""


class PhotographDir(StrEnum):
    ICLOUD_DIR = _INTERNAL_ICLOUD_DIR
    """iCloud 目录"""

    LOCAL_DIR = _INTERNAL_LOCAL_DIR
    """本地目录"""

    ICLOUD_RAW_PHOTO = f"{ICLOUD_DIR}/Photograph-Raw"
    """iCloud 原始照片目录"""

    LOCAL_RAW_PHOTO = f"{LOCAL_DIR}/Photograph-Raw"
    """本地原始照片目录"""

    ICLOUD_RAW_TIMELAPSE_PHOTO = f"{ICLOUD_DIR}/TimeLapse-Raw"
    """iCloud 原始照片目录"""

    ICLOUD_RAW_PANO = f"{ICLOUD_DIR}/Panorama-Raw"
    """iCloud 原始全景照片目录"""


class ExifImageMake(StrEnum):
    """相机制造商枚举"""

    UNKNOWN = "Unknown"
    """未知制造商"""

    SONY = "SONY"
    """索尼相机"""

    @classmethod
    def from_string(cls, value: str) -> "ExifImageMake":
        """
        根据字符串匹配对应的枚举值（不区分大小写）

        Args:
            value (str): 输入字符串
        """
        value_upper = value.strip()
        for member in cls:
            # TODO: 可能会导致大小写不敏感匹配，如果需要严格匹配，可以使用 `value_upper.lower() == member.value.lower()`
            if member.value == value_upper:
                return member
        raise ValueError(f"Unsupported camera make: {value}")
