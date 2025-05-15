import os
from enum import StrEnum

INTERNAL_ICLOUD_DIR = os.path.expandvars(
    r"$HOME/Library/Mobile Documents/com~apple~CloudDocs"
)
"""内部 iCloud 目录，不对外暴露
"""


class PhotographDir(StrEnum):
    ICLOUD_DIR = INTERNAL_ICLOUD_DIR
    """iCloud 目录"""

    ICLOUD_PHOTO_LOCAL = f"{INTERNAL_ICLOUD_DIR}/Photograph-local"
    """iCloud 原始照片目录"""

    ICLOUD_PANO_LOCAL = f"{INTERNAL_ICLOUD_DIR}/Panorama-local"
    """iCloud 原始全景照片目录"""
