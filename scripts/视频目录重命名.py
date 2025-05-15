"""
视频目录下的视频文件重命名

支持
- sony 相机格式

"""

import argparse
import typing
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from loguru import logger
from pydantic import BaseModel

from pkg._enums.photo import PhotographDir

# /Users/henryzhu/250504-武汉动物园小熊猫

# ================== 基础变量设置 ==================
BD = PhotographDir.ICLOUD_PANO_LOCAL
"""基本目录 base dir"""
VIDEO_DIR_LIST: typing.List[str] = [
    "/Users/henryzhu/250504-武汉动物园小熊猫",
]
"""视频目录列表"""
# ================================================


class Args:
    SUPPORTED_TYPES = [
        ".mp4",
    ]

    def __init__(self) -> None:
        args = self.get_args()
        self.execute_confirm: bool = args.yes
        """执行确认"""

    @staticmethod
    def get_args():
        parse = argparse.ArgumentParser(description="视频目录下的视频文件重命名工具")
        parse.add_argument("-y", "--yes", action="store_true", help="是否确认重命名")
        return parse.parse_args()


def main():
    args = Args()

    all_video_files: typing.List[Path] = []

    video_dir_list = [Path(_dir) for _dir in VIDEO_DIR_LIST]

    for video_dir in video_dir_list:
        # 检查路径是否存在，并且检查是否为目录
        if not video_dir.exists() or not video_dir.is_dir():
            raise FileNotFoundError(f"路径不存在或不是目录: {video_dir}")
        # logger.debug(f"视频目录: {video_dir}")

        for file in video_dir.iterdir():
            # 跳过目录 / 检查文件的后缀，忽略大小写
            if file.is_dir() or file.suffix.lower() not in tuple(Args.SUPPORTED_TYPES):
                continue
            all_video_files.append(file)  # file 已经是 Path 对象，无需再拼接

    for video_file in all_video_files:
        logger.debug(f"{type(video_file)} {video_file}")

        # 检查是否有附带的配置文件，例如 20250504_C0840.MP4 会附带一个 20250504_C0840M01.XML 元数据
        # 这里的 XML 文件是 Sony 相机拍摄的文件，包含了视频的元数据
        # 例如拍摄时间、拍摄地点等
        metadata_file = find_metadata_file(video_file)
        if not metadata_file:
            raise ValueError(f"没有找到元数据文件: {video_file}")

        metadate = parse_metadata_file(metadata_file)
        logger.debug(f"解析元数据: {metadate}")

        # 根据元数据重命名视频文件和元数据文件
        # 例如将 20250504_C0840.MP4 重命名为 20250504_C0840_20230504_123456.MP4


def find_metadata_file(video_file: Path) -> Path | None:
    """
    查找视频文件的元数据文件。

    支持模糊匹配（允许元数据文件名包含额外字符）

    参数:
        video_file (Path): 视频文件路径

    返回:
        str: 匹配到的元数据文件路径
    """
    dir_path = video_file.parent
    base_stem = video_file.stem

    logger.debug(f"dir_path: {dir_path} base_stem: {base_stem}")

    # 检查是否有文件名包含 base_stem 的文件，但是不是视频文件
    maybe_metadata_files: typing.List[Path] = []
    for file in dir_path.iterdir():
        if file.name.startswith(base_stem) and file != video_file:
            maybe_metadata_files.append(file)
    if len(maybe_metadata_files) == 0:
        return None
    elif len(maybe_metadata_files) == 1:
        return maybe_metadata_files[0]
    else:
        raise ValueError(f"找到多个元数据文件: {maybe_metadata_files}")


class VideoMetadata(BaseModel):
    manufacturer: str
    """制造商"""

    creation_datetie: datetime
    """创建时间"""


def parse_metadata_file(metadata_file: Path) -> VideoMetadata:
    """
    解析元数据文件，返回视频的元数据。

    参数:
        metadata_file (Path): 元数据文件路径

    返回:
        VideoMetadata: 视频的元数据
    """
    # 这里需要根据实际的元数据文件格式进行解析
    # 例如 XML 文件可以使用 xml.etree.ElementTree 进行解析
    # 这里暂时返回一个空的 VideoMetadata 对象

    if metadata_file.suffix.lower() == ".xml":
        return parse_sony_metadata(metadata_file)
    else:
        raise ValueError(f"不支持的元数据文件格式: {metadata_file.suffix}")


def parse_sony_metadata(metadata_file: Path) -> VideoMetadata:  # noqa: C901
    """
    解析 Sony 相机的元数据文件，返回视频的元数据。

    参数:
        metadata_file (Path): 元数据文件路径

    返回:
        VideoMetadata: 视频的元数据
    """
    # 这里需要根据实际的 Sony 相机的元数据文件格式进行解析
    # 例如 XML 文件可以使用 xml.etree.ElementTree 进行解析
    # 这里暂时返回一个空的 VideoMetadata 对象

    def get_namespace(element: ET.Element) -> str:
        """提取命名空间"""
        if "}" in element.tag:
            return element.tag.split("}", 1)[0][1:]
        return ""

    def find_in_ns(root: ET.Element, tag_name: str) -> ET.Element | None:
        """在命名空间中查找单个元素"""
        ns = get_namespace(root)
        if ns:
            return root.find(f".//{{{ns}}}{tag_name}")
        return root.find(f".//{tag_name}")

    tree = ET.parse(metadata_file)
    root = tree.getroot()

    # 动态获取命名空间
    ns = get_namespace(root)

    # 提取 CreationDate
    creation_date_elem = find_in_ns(root, "CreationDate")

    if (creation_date_elem is not None) and ("value" in creation_date_elem.attrib):
        date_str = creation_date_elem.attrib["value"]
        try:
            creation_datetime = datetime.fromisoformat(date_str)
        except ValueError as e:
            raise ValueError(f"无法解析 CreationDate: {date_str}, 错误: {e}")
    else:
        raise ValueError("无法解析 CreationDate")

    # 提取 Device 信息
    device_elem = find_in_ns(root, "Device")
    manufacturer = "Unknown"
    if device_elem is not None:
        maybe_manufacturer = device_elem.attrib.get("manufacturer")
        if maybe_manufacturer:
            manufacturer = maybe_manufacturer
    # model_name = (
    #     device_elem.attrib.get("modelName") if device_elem is not None else None
    # )
    # serial_number = (
    #     device_elem.attrib.get("serialNo") if device_elem is not None else None
    # )

    # 提取 GPS 信息
    gps_group = (
        root.find(f".//{{{ns}}}Group[@name='ExifGPS']")
        if ns
        else root.find(".//Group[@name='ExifGPS']")
    )
    gps_latitude = gps_longitude = gps_timestamp = None
    if gps_group is not None:
        for item in (
            gps_group.findall(f".//{{{ns}}}Item")
            if ns
            else gps_group.findall(".//Item")
        ):
            name = item.attrib.get("name")
            value = item.attrib.get("value")
            if name == "Latitude":
                gps_latitude = value
            elif name == "Longitude":
                gps_longitude = value
            elif name == "TimeStamp":
                gps_timestamp = value

    return VideoMetadata(manufacturer=manufacturer, creation_datetie=creation_datetime)


if __name__ == "__main__":
    main()
