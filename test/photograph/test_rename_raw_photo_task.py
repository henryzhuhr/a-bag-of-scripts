"""
测试 RenameRawPhotoTask 的功能
"""

import os
import shutil
import tempfile

import pytest

from modules.photograph._types.photo import FileTag
from modules.photograph.tasks.rename_raw_photo import (
    RenameRawPhotoTask,
    RenameRawPhotoTaskConfig,
)


class DummyExif:
    def __init__(self, date_time):
        self.printable = date_time


def mock_exifread_process_file(f, details=False, strict=True):
    return {"EXIF DateTimeOriginal": DummyExif("2023:08:17 12:34:56")}


def mock_pillow_heif_open_heif(file_path):
    class DummyHeif:
        info = {"exif": b"dummy_exif"}

    return DummyHeif()


def mock_piexif_load(exif_bytes, key_is_name=True):
    return {"Exif": {"DateTimeOriginal": b"2023:08:17 12:34:56"}}


@pytest.fixture
def temp_photo_dir(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    # 创建模拟 RAW 文件
    raw_file = os.path.join(temp_dir, "DSC00001.ARW")
    with open(raw_file, "wb") as f:
        f.write(b"RAW DATA")
    # 创建模拟 xmp 文件
    xmp_file = os.path.join(temp_dir, "DSC00001.xmp")
    with open(xmp_file, "w") as f:
        f.write("xmp data")
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.mark.usefixtures("temp_photo_dir")
def test_generate_and_execute(monkeypatch, temp_photo_dir):
    # mock exifread, pillow_heif, piexif
    monkeypatch.setattr("exifread.process_file", mock_exifread_process_file)
    monkeypatch.setattr("pillow_heif.open_heif", mock_pillow_heif_open_heif)
    monkeypatch.setattr("piexif.load", mock_piexif_load)

    file_tag = FileTag(tag="TEST", dir=temp_photo_dir)
    config = RenameRawPhotoTaskConfig(file_tag_list=[file_tag])
    task = RenameRawPhotoTask(config)
    # 检查生成的任务
    assert len(task.process_task_list) == 2
    # dry_run 执行
    # execute 方法现在不返回结果，直接检查文件是否未被重命名
    task.execute(dry_run=True)
    files = os.listdir(temp_photo_dir)
    assert "DSC00001.ARW" in files
    assert "DSC00001.xmp" in files
    # 真正执行
    task.execute(dry_run=False)
    # 检查文件是否已重命名
    files = os.listdir(temp_photo_dir)
    assert any(f.endswith(".ARW") and f != "DSC00001.ARW" for f in files)
    assert any(f.endswith(".xmp") and f != "DSC00001.xmp" for f in files)
