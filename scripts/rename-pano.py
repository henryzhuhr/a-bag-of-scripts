"""
全景照片命名，适用于 DJI 拍摄的全景照片目录

"""

import os
import typing
from genericpath import exists

from loguru import logger

from pkg._enums.photo import PhotographDir
from pkg._types.photo import FileTag
from utils.xphoto import XPhoto

# ================== 目录路径设置 ==================
BD = PhotographDir.ICLOUD_PHOTO_LOCAL
"""基本目录 base dir"""

BD = f"{BD}/250501-【旅游】长沙/250501-DCIMmxhnight/PANORAMA"


class Args:
    PANO_DIR_LIST: typing.List[FileTag] = [
        # fmt: off
        # FileTag(tag="梅溪湖艺术中心大剧院", dir=f"{BD}/001_0016"),
        # fmt: on
        # ============ 目录范围 ============
        # fmt: off
        *[
            FileTag(tag="梅溪湖艺术中心大剧院", dir=f"{BD}/001_00{index:02d}")
            for index in range(0, 100 + 1)  # 左闭右开，所以右边+1
        ]
        # fmt: on
    ]
    """全景照片目录"""


def main():
    print("Hello from common-scripts!")

    for photo_dir in Args.PANO_DIR_LIST:
        print(f"{photo_dir.tag} - {photo_dir.dir}")

        # 检查是否存在目录
        if not exists(photo_dir.dir):
            logger.warning(f"目录不存在: {photo_dir.dir}")
            continue

        pano_photos: typing.List[XPhoto] = []

        for file in os.listdir(photo_dir.dir):
            # 排除 macOS 系统文件
            if file.startswith(".DS_Store"):
                continue
            xphoto = XPhoto(file_path=os.path.join(photo_dir.dir, file))
            logger.info(xphoto.photo_info.exif_data.date_time_original)
            pano_photos.append(xphoto)

        # 按照 拍摄时间 升序排序
        pano_photos.sort(key=lambda x: x.photo_info.exif_data.date_time_original)
        for xphoto in pano_photos:
            logger.info(xphoto.photo_info.exif_data.date_time_original)

        if len(pano_photos) == 0:
            logger.warning("没有找到全景照片")
            continue

        # 在 photo_dir.dir 同目录下创建 YYMMDD-<photo_dir.tag>-HHMMSS 文件夹，然后将全部文件以 YYMMDD-<photo_dir.tag>-HHMMSS_<index> 重命名
        # 1. 创建同目录下的新文件夹
        date_time = pano_photos[0].photo_info.exif_data.date_time_original
        print(type(date_time), date_time)

        dir_name = f"{date_time.strftime('%Y%m%d')[2:]}-{photo_dir.tag}_{date_time.strftime('%H%M%S')}"
        dir_path = os.path.join(os.path.dirname(photo_dir.dir), dir_name)
        logger.info(f"新目录: {dir_name}, {dir_path}")
        # 2. 重命名文件

        os.makedirs(dir_path, exist_ok=True)

        for index, xphoto in enumerate(pano_photos):
            new_file_name = f"{dir_name}_{index:02d}{os.path.splitext(xphoto.photo_info.file_path)[1]}"

            new_file_path = os.path.join(dir_path, new_file_name)
            logger.info(f"重命名: {xphoto.photo_info.file_path} -> {new_file_path}")
            os.rename(xphoto.photo_info.file_path, new_file_path)


if __name__ == "__main__":
    main()
