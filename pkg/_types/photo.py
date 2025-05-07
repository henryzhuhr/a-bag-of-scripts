import os
from datetime import datetime

from pydantic import BaseModel


class FileTag:
    tag: str
    """文件名
    """

    dir: str
    """文件目录
    """

    def __init__(self, tag: str, dir: str):
        self.tag = tag
        self.dir = os.path.expanduser(os.path.expandvars(dir))


class ExifData(BaseModel):
    date_time_original: datetime
    """拍摄时间"""

    # make: str
    # """相机品牌"""

    # model: str
    # """相机型号"""

    # exposure_time: str
    # """曝光时间"""

    # f_number: str
    # """光圈值"""

    # iso_speed: str
    # """ISO 感光度"""

    # focal_length: str
    # """焦距"""


class PhotoInfo(BaseModel):
    file_path: str
    """文件路径"""

    file_name: str
    """文件名"""

    file_ext: str
    """文件扩展名"""

    exif_data: ExifData
    """Exif 数据"""
