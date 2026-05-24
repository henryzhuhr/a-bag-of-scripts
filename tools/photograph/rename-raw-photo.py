"""
基于通用任务框架的 RAW 照片重命名任务
"""

import argparse
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

from modules.photograph._enums.photo import PhotographDir as PD
from modules.photograph._types.photo import FileTag
from modules.photograph.tasks.rename_raw_photo import (
    RenameRawPhotoTask,
    RenameRawPhotoTaskConfig,
)
from modules.task.task_manager import TaskManager

TASK_NAME = "rename-raw-photo"
DEFAULT_CONFIG_PATH = Path(__file__).with_name("rename-raw-photo.yaml")
BASE_DIR_MAP = {
    "icloud_raw_photo": str(PD.ICLOUD_RAW_PHOTO),
    "local_raw_photo": str(PD.LOCAL_RAW_PHOTO),
    "icloud_raw_video": str(PD.ICLOUD_RAW_VIDEO),
    "icloud_raw_timelapse_photo": str(PD.ICLOUD_RAW_TIMELAPSE_PHOTO),
    "icloud_raw_pano": str(PD.ICLOUD_RAW_PANO),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="重命名 RAW 照片")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"YAML 配置文件路径，默认读取 {DEFAULT_CONFIG_PATH}。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印计划，不询问确认，也不实际重命名。",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="兼容旧用法；默认已经会询问确认后执行。",
    )
    parser.add_argument(
        "--fail-on-invalid",
        action="store_true",
        help="发现不符合规则的文件时直接停止；默认记录后继续处理其他文件。",
    )
    return parser


def load_config(config_path: Path) -> RenameRawPhotoTaskConfig:
    if not config_path.exists():
        raise FileNotFoundError(
            f"配置文件不存在: {config_path}。"
            f"可以参考 {config_path.with_name('rename-raw-photo.example.yaml')} 创建。"
        )

    with config_path.open("r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f) or {}
    if not isinstance(raw_config, dict):
        raise ValueError("配置文件根节点必须是 YAML mapping")

    task_name = raw_config.get("task_name", TASK_NAME)
    if not isinstance(task_name, str) or not task_name:
        raise ValueError("配置项 task_name 必须是非空字符串")

    base_dir = resolve_base_dir(raw_config.get("base_dir"))
    file_tag_list = load_file_tag_list(raw_config.get("file_tag_list"), base_dir)
    return RenameRawPhotoTaskConfig(name=task_name, file_tag_list=file_tag_list)


def resolve_base_dir(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError("配置项 base_dir 必须是非空字符串")
    return BASE_DIR_MAP.get(value, value)


def load_file_tag_list(value: Any, base_dir: str | None) -> list[FileTag]:
    if not isinstance(value, list) or len(value) == 0:
        raise ValueError("配置项 file_tag_list 必须是非空列表")

    file_tag_list: list[FileTag] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"file_tag_list 第 {index} 项必须是 YAML mapping")

        tag = item.get("tag")
        directory = item.get("dir")
        if not isinstance(tag, str) or not tag:
            raise ValueError(f"file_tag_list 第 {index} 项缺少非空 tag")
        if not isinstance(directory, str) or not directory:
            raise ValueError(f"file_tag_list 第 {index} 项缺少非空 dir")

        file_tag_list.append(FileTag(tag=tag, dir=resolve_dir(directory, base_dir)))
    return file_tag_list


def resolve_dir(directory: str, base_dir: str | None) -> str:
    path = Path(directory).expanduser()
    if path.is_absolute() or base_dir is None:
        return str(path)
    return str(Path(base_dir).expanduser() / path)


def main():
    args = build_parser().parse_args()
    dry_run = args.dry_run

    try:
        config = load_config(args.config)
        manager = TaskManager()
        task = RenameRawPhotoTask(config)
        manager.register_task(task)
        print(task.describe())

        if task.invalid_files:
            logger.warning(f"found {len(task.invalid_files)} invalid files")
            for invalid_file in task.invalid_files:
                logger.warning(
                    f"invalid file summary: '{invalid_file.file_path}', reason: {invalid_file.reason}"
                )
            if args.fail_on_invalid:
                logger.error("skip execution because --fail-on-invalid is enabled")
                return

        # 默认打印计划并询问 yes/no；传入 --dry-run 时只检查，不修改照片文件。
        manager.execute(TASK_NAME, dry_run=dry_run)
    except Exception as e:
        logger.error(f"failed to execute task: {e}")


if __name__ == "__main__":
    main()
