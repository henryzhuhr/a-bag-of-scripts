"""
python3 -m pip install exifread pillow-heif piexif
"""

import argparse
import os
import typing
from typing import List, Optional

import exifread
import piexif
import pillow_heif

from modules.photograph._enums.photo import PhotographDir


class FileTag:
    def __init__(self, tag: str, dir: str):
        self.tag = tag
        self.dir = os.path.expanduser(os.path.expandvars(dir))


# ================== 目录路径设置 ==================
BASE_DIR = PhotographDir.ICLOUD_RAW_PHOTO
# BASE_DIR = ".cache/Photograph-local"
FILE_TAG_LIST: typing.List[FileTag] = [
    # fmt: off
    # FileTag(tag="相册名称", dir=f"{BASE_DIR}/YYMMDD-相册名称"),
    FileTag(tag="SZX深圳宝安国际机场", dir=f"{BASE_DIR}/250726-SZX深圳宝安国际机场"),
    FileTag(tag="CAN广州白云国际机场", dir=f"{BASE_DIR}/250727-CAN广州白云国际机场"),
    # fmt: on
]

EXIF_SUPPORTED_FILE_EXT = [
    ".arw",  # 索尼
    ".dng",
    ".raf",  # 富士
    ".jpg",
    ".jpeg",
]
HEIF_SUPPORTED_FILE_EXT = [".heif", ".heic", ".hif"]


def get_second_id_from_file_base(file_base: str):
    """
    获取文件名中的秒级标识
    `second_id` 秒级标识，避免同一秒内拍摄的多张照片被覆盖
    """
    if file_base.startswith("DJI"):  # DJI 命名规则
        second_id = file_base[-4:-2]
    elif file_base.startswith("PANO"):  # DJI 接片文件命名规则
        second_id = f"PANO~{file_base[-2:]}"
    elif file_base[-7:-3] == "PANO":  # DJI 接片文件命名规则 (二次命名)
        second_id = f"PANO~{file_base[-2:]}"
    elif file_base.startswith("DSC"):  # 索尼命名规则
        second_id = file_base[-2:]
    elif file_base.startswith("IMG_"):  # iPhone 命名规则
        second_id = file_base[-2:]
    else:
        # raise Exception(f"unsupported file name: {file_base}")
        second_id = file_base[-2:]  # 如果报错，手动确认后注释
    return second_id


class DefaultArgs:
    def __init__(self) -> None:
        args = self.get_args()
        self.execute_confirm: bool = args.yes

    @staticmethod
    def get_args():
        parse = argparse.ArgumentParser(description="读取相机exif重命名文件")
        parse.add_argument("-y", "--yes", action="store_true", help="是否确认重命名")
        return parse.parse_args()


def main():
    args = DefaultArgs()
    process_task_list: List[ProcessTask] = []

    # 遍历文件夹
    for file_tag in FILE_TAG_LIST:
        # 遍历文件
        for file in os.listdir(file_tag.dir):
            print(f"正在处理: {file_tag.tag} / {file}")
            if file.startswith("."):
                continue

            # 分割文件名和后缀
            file_base, file_ext = os.path.splitext(file)
            file_path = os.path.join(file_tag.dir, file)

            # 检查文件类型是否支持
            # 解析 exif 信息
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
            else:
                continue

            file_date, file_time = date_time.split(" ")
            file_date = file_date.replace(":", "")[2:]
            file_time = file_time.replace(":", "")
            # 获取文件名中的秒级标识
            second_id = get_second_id_from_file_base(file_base)
            if second_id is None:
                print(
                    f"{COLORMAP.YELLOW}未知文件名格式或已经命名: {file_tag.dir} / {file}{COLORMAP.DEFAULT}"
                )
                continue

            # 文件标识
            file_identification = f"{file_time}_{second_id}"

            # 更新文件名
            update_name = f"{file_date}-{file_tag.tag}-{file_identification}"
            update_file = f"{update_name}{file_ext}"

            process_task_list.append(
                ProcessTask(
                    parent_dir=file_tag.dir,
                    origin_file=file,
                    update_file=update_file,
                    skip=(file_base == update_name),
                )
            )

            # 检查是否存在 xmp 文件
            xmp_file = f"{file_base}.xmp"
            xmp_file_path = os.path.join(file_tag.dir, xmp_file)
            if os.path.exists(xmp_file_path):
                process_task_list.append(
                    ProcessTask(
                        parent_dir=file_tag.dir,
                        origin_file=xmp_file,
                        update_file=f"{update_name}.xmp",
                        skip=(xmp_file == f"{update_name}.xmp"),
                    )
                )

    # ========================================
    #   需要执行的任务
    # ========================================
    def process_task_info_str(_idx: int, _idx_len: int, task: ProcessTask):
        return "{idx}: {dir}  /  {ofile} -> {ufile} {skip}".format(
            idx=f"{str(_idx).rjust(_idx_len)}",
            dir=f"{COLORMAP.YELLOW}{task.parent_dir}{COLORMAP.DEFAULT}",
            ofile=f"{COLORMAP.BLUE}{task.origin_file}{COLORMAP.DEFAULT}",
            ufile=f"{COLORMAP.GREEN}{task.update_file}{COLORMAP.DEFAULT}",
            skip=(f"{COLORMAP.RED}[SKIP]{COLORMAP.DEFAULT}" if task.skip else ""),
        )

    def showall_process_task(ptl: List[ProcessTask]):
        for i, task in enumerate(ptl):
            if not task.skip:
                print(process_task_info_str(i, len(str(len(ptl))), task))

    def execute_process_task(ptl: List[ProcessTask]):
        """执行的任务"""
        for i, task in enumerate(ptl):
            if not task.skip:
                print(process_task_info_str(i, len(str(len(ptl))), task))
                os.rename(
                    os.path.join(task.parent_dir, task.origin_file),
                    os.path.join(task.parent_dir, task.update_file),
                )

    # ========================================
    #   执行前的确认 输入 yes 才会执行
    # ========================================
    if process_task_list.__len__() == 0:
        print("没有需要执行的任务")
    else:
        showall_process_task(process_task_list)
        execute_confirm = args.execute_confirm
        if execute_confirm:
            execute_process_task(process_task_list)
        else:
            incorrect_input_str: Optional[str] = None

            execute_cnt = 0
            while True:
                execute_cnt += 1
                if execute_cnt > 5:
                    print("错误执行次数过多，已取消执行")
                    break
                tip_info = (
                    str(
                        f'未知输入 "{incorrect_input_str}" '
                        if incorrect_input_str
                        else "是否执行以上的重命名操作"
                    )
                    + "，确认执行输入(yes/no):"
                )
                confirm = input(tip_info).lower()

                if confirm in ["yes", "y"]:
                    execute_process_task(process_task_list)
                    break
                elif confirm in ["no", "n"]:
                    print("已取消执行")
                    break
                else:
                    incorrect_input_str = confirm
                continue


class ProcessTask:
    def __init__(
        self,
        parent_dir: str,
        origin_file: str,  # 原始文件名
        update_file: str,  # 更新后的文件名
        skip=False,
    ) -> None:
        self.parent_dir = parent_dir
        self.origin_file = origin_file
        self.update_file = update_file
        self.skip = skip


class COLORMAP:
    DEFAULT = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    PURPLE = "\033[35m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"


if __name__ == "__main__":
    main()
