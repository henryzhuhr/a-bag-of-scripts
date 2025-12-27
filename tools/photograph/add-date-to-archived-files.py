"""
为归档文件添加修改日期
add-date-to-archived-files
"""

import argparse
import datetime
import os
import re
import time
from typing import List, Optional

from loguru import logger

from modules.photograph._enums.photo import PhotographDir


class DefaultArgs:
    @staticmethod
    def get_args():
        parse = argparse.ArgumentParser(description="为压缩文件添加修改日期")
        parse.add_argument(
            "--dir",
            type=str,
            default=[
                "",  # 默认 防止报错
                f"{PhotographDir.ICLOUD_RAW_PHOTO}",  # 照片 原始
                # f"{PhotographDir.ICLOUD_RAW_TIMELAPSE_PHOTO}",  ## 延时 原始
                # f"{PhotographDir.ICLOUD_RAW_PANO}",  ### 全景 原始
                # f"{PhotographDir.ICLOUD_RAW_VIDEO}",  ### 视频 原始
            ][-1],
            help="需要处理的文件夹",
        )
        return parse.parse_args()

    def __init__(self) -> None:
        args = self.get_args()
        self.dir: str = os.path.expandvars(args.dir)
        assert os.path.exists(self.dir), f"文件夹不存在: {self.dir}"


class ProcessTask:
    def __init__(
        self,
        parent_dir: str,
        file: str,
        file_modify: str,
        sizeGB: float,
    ) -> None:
        self.parent_dir = parent_dir
        self.file = file
        self.file_modify = file_modify
        self.sizeGB = sizeGB


SUPPORTED_COMPRESSION_FILE_TYPES = [
    ".7z",  # 极致压缩率
    ".zip",  # 最常见的格式
    ".tar",  # 仅打包
    *[".tar.gz", ".tgz"],
    *[".tar.bz2", ".tbz2"],
    *[".tar.xz", ".txz"],
]


def main():  # noqa: C901
    args = DefaultArgs()
    file_count = 0
    process_task_list: List[ProcessTask] = []
    file_str_max_len = 0
    file_modify_str_max_len = 0

    for file in os.listdir(args.dir):
        # 排除目录/文件夹
        if os.path.isdir(file):
            continue

        # 排除 dotfile
        if file.startswith("."):
            continue

        # 排除不支持的压缩文件类型
        if not any(
            file.endswith(file_type) for file_type in SUPPORTED_COMPRESSION_FILE_TYPES
        ):
            continue
        file_path = os.path.join(args.dir, file)

        file_type: Optional[str] = None
        for supported_file_type in SUPPORTED_COMPRESSION_FILE_TYPES:
            if file.endswith(supported_file_type):
                file_type = supported_file_type
                break
        if file_type is None:
            raise ValueError(
                f"Unsupported file type for file: {file}. Supported types are: {SUPPORTED_COMPRESSION_FILE_TYPES}"
            )
        file_stat = os.stat(file_path)  # 获取文件的信息

        file_size = byte2GB(file_stat.st_size)  # 文大小 byte -> GB

        file_ctime = ts2str(file_stat.st_ctime)  # 创建时间     # noqa: F841
        file_mtime = ts2str(file_stat.st_mtime)  # 最后修改时间
        file_atime = ts2str(file_stat.st_atime)  # 最后访问时间  # noqa: F841
        file_name = file[: -len(file_type)]  # 文件名 去掉后缀
        file_name = file_name.split("~")[0]  # 文件名 去掉 时间戳

        if file == f"{file_name}~{file_mtime}{file_type}":
            logger.warning(f"skip, 文件名已经包含时间戳, file name is '{file}'")
            continue

        # 有可能文件的时间戳不是修改的时间，需要正则表达式和时间解析来验证是否是一个合法的时间戳
        validated = False
        pattern = rf"{re.escape(file_name)}~(\d{{6}}_\d{{6}}){re.escape(file_type)}"
        # 查找匹配的时间格式字符串
        match = re.search(pattern, file)
        if match:
            file_time_str = match.group(1)
            year = int(file_time_str[:2]) + 2000  # 假设年份在2000年之后
            remaining_part = file_time_str[2:]
            try:
                datetime.datetime.strptime(f"{year}{remaining_part}", "%Y%m%d_%H%M%S")
                logger.warning(
                    f"skip, 文件名已经包含时间戳，与修改时间不匹配, file name is '{file}"
                )
                validated = True
                continue
            except ValueError:
                pass

        if not validated:
            assert file == f"{file_name}{file_type}", (
                f"  [ERROR] 文件名不匹配. 分割文件 {file} 时错误，分割为 [ {file_name}, {file_type} ]"
            )

        file_with_time = f"{file_name}~{file_mtime}{file_type}"
        file_count += 1
        file_str_max_len = max(file_str_max_len, len(file))
        file_modify_str_max_len = max(file_modify_str_max_len, len(file_with_time))
        process_task_list.append(ProcessTask(args.dir, file, file_with_time, file_size))
        print(args.dir, file, file_with_time)

    def execute_process_task():
        """执行的任务"""
        for i, task in enumerate(process_task_list):
            format_str = f"{task.file.ljust(file_str_max_len)} -> {task.file_modify.ljust(file_modify_str_max_len)}"
            print(str(i).rjust(3), str(f"{task.sizeGB:.2f}(G)").rjust(8), format_str)
            os.rename(
                os.path.join(task.parent_dir, task.file),
                os.path.join(task.parent_dir, task.file_modify),
            )

    # ========================================
    #   执行前的确认 输入 yes 才会执行
    # ========================================
    if process_task_list.__len__() == 0:
        logger.info("没有需要执行的任务")
    else:
        logger.info("是否执行如下的重命名操作")
        for i, task in enumerate(process_task_list):
            format_str = f"{task.file.ljust(file_str_max_len)} -> {task.file_modify.ljust(file_modify_str_max_len)}"
            size_str = str(f"{task.sizeGB:.2f}(G)").rjust(8)
            logger.info(f"index:{str(i).rjust(3)}, {size_str}, {format_str}")
        incorrect_input_str: Optional[str] = None
        while True:
            tip_info = (
                str(f'未知输入 "{incorrect_input_str}":' if incorrect_input_str else "")
                + "确认执行输入(yes/no):"
            )
            confirm = input(tip_info).lower()

            if confirm in ["yes", "y"]:
                execute_process_task()
                break
            elif confirm in ["no", "n"]:
                print("已取消执行")
                break
            else:
                incorrect_input_str = confirm
                continue


__byte2GB_ratio = 1024 * 1024 * 1024


def byte2GB(byte: int):
    return byte / __byte2GB_ratio


def ts2str(timestamp: float):
    """time stamp -> str"""
    format_str = time.strftime("%Y%m%d_%H%M%S", time.localtime(timestamp))
    return f"{format_str}"


if __name__ == "__main__":
    main()
