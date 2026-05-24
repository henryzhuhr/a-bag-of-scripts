"""
Console entry point for the RAW photo rename task.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

import yaml
from loguru import logger

from modules.photograph._types.photo import FileTag
from modules.photograph.tasks.rename_raw_photo import (
    RenameRawPhotoTask,
    RenameRawPhotoTaskConfig,
)
from modules.task.task_manager import TaskManager

DEFAULT_TASK_NAME = "rename-raw-photo"


def _parse_file_tag(value: str) -> FileTag:
    if "=" not in value:
        raise argparse.ArgumentTypeError(
            "file tag must use TAG=DIR format, for example TEST=~/Photos"
        )
    tag, directory = value.split("=", 1)
    tag = tag.strip()
    directory = directory.strip()
    if not tag or not directory:
        raise argparse.ArgumentTypeError("both TAG and DIR are required")
    return FileTag(tag=tag, dir=directory)


def _load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("config file must contain a mapping")
    return data


def _load_file_tags(config: dict[str, Any]) -> list[FileTag]:
    raw_items = config.get("file_tag_list", [])
    if not isinstance(raw_items, list):
        raise ValueError("config field 'file_tag_list' must be a list")

    file_tags: list[FileTag] = []
    for item in raw_items:
        if not isinstance(item, dict):
            raise ValueError("each file_tag_list item must be a mapping")
        try:
            file_tags.append(FileTag(tag=item["tag"], dir=item["dir"]))
        except KeyError as e:
            raise ValueError("each file_tag_list item requires 'tag' and 'dir'") from e
    return file_tags


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rename RAW photos using EXIF date and configured tags."
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="YAML config with task_name and file_tag_list entries.",
    )
    parser.add_argument(
        "--file-tag",
        action="append",
        default=[],
        type=_parse_file_tag,
        metavar="TAG=DIR",
        help="Photo tag and directory pair. Can be passed multiple times.",
    )
    parser.add_argument(
        "--task-name",
        default=None,
        help=f"Task name. Defaults to {DEFAULT_TASK_NAME!r}.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually rename files. Without this flag the task runs as dry-run.",
    )
    return parser


def _resolve_task_config(args: argparse.Namespace) -> RenameRawPhotoTaskConfig:
    config: dict[str, Any] = {}
    if args.config:
        config = _load_config(args.config)

    file_tags = _load_file_tags(config)
    file_tags.extend(args.file_tag)

    if not file_tags:
        raise ValueError("provide at least one --file-tag TAG=DIR or config entry")

    task_name = args.task_name or config.get("task_name") or DEFAULT_TASK_NAME
    return RenameRawPhotoTaskConfig(name=task_name, file_tag_list=file_tags)


def run(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = _resolve_task_config(args)
        manager = TaskManager()
        task = RenameRawPhotoTask(config)
        manager.register_task(task)
        print(task.describe())
        manager.execute(config.name, dry_run=not args.execute)
    except Exception as e:
        logger.error(f"failed to execute task: {e}")
        return 1
    return 0


def main() -> int:
    return run()
