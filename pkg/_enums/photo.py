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

    ICLOUD_RAW_PHOTO = f"{ICLOUD_DIR}/Photograph-local"
    """iCloud 原始照片目录"""

    LOCAL_RAW_PHOTO = f"{LOCAL_DIR}/Photograph-local"
    """本地原始照片目录"""

    ICLOUD_RAW_PANO = f"{ICLOUD_DIR}/Panorama-local"
    """iCloud 原始全景照片目录"""
