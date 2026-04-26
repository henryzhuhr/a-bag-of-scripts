"""
测试 RAW 照片重命名任务和元数据插件系统。
"""

from pathlib import Path

import pytest

from modules.photograph import metadata_plugins as metadata_plugin_module
from modules.photograph.metadata_plugins import (
    MetadataPluginError,
    PhotoMetadataPlugin,
)
from modules.photograph._types.photo import FileTag
from modules.photograph.tasks.rename_raw_photo import (
    RenameRawPhotoTask,
    RenameRawPhotoTaskConfig,
)

EXPECTED_BASE = "20230817-TEST-123456_DSC00001"


class DummyExif:
    def __init__(self, date_time: str):
        self.printable = date_time


def mock_exifread_process_file(f, details=False, strict=True):
    return {"EXIF DateTimeOriginal": DummyExif("2023:08:17 12:34:56")}


def mock_pillow_heif_open_heif(file_path):
    class DummyHeif:
        info = {"exif": b"dummy_exif"}

    return DummyHeif()


def mock_piexif_load(exif_bytes, key_is_name=True):
    return {"Exif": {"DateTimeOriginal": b"2023:08:17 12:34:56"}}


class DummyMetadataPlugin(PhotoMetadataPlugin):
    def read_original_datetime(self, file_path: str) -> str:
        return "2023:08:17 12:34:56"


@pytest.fixture(autouse=True)
def mock_builtin_metadata(monkeypatch):
    monkeypatch.setattr(
        metadata_plugin_module.exifread, "process_file", mock_exifread_process_file
    )
    monkeypatch.setattr(
        metadata_plugin_module.pillow_heif,
        "open_heif",
        mock_pillow_heif_open_heif,
    )
    monkeypatch.setattr(metadata_plugin_module.piexif, "load", mock_piexif_load)


@pytest.fixture
def photo_dir(tmp_path):
    photos = tmp_path / "photos"
    photos.mkdir()
    return photos


def make_task(
    photo_dir: Path,
    metadata_plugins: list[PhotoMetadataPlugin] | None = None,
    metadata_plugin_modules: list[str] | None = None,
    load_entry_point_plugins: bool = False,
) -> RenameRawPhotoTask:
    config = RenameRawPhotoTaskConfig(
        name="rename-raw-photo",
        file_tag_list=[FileTag(tag="TEST", dir=str(photo_dir))],
        metadata_plugins=metadata_plugins,
        metadata_plugin_modules=metadata_plugin_modules or [],
        load_entry_point_plugins=load_entry_point_plugins,
    )
    return RenameRawPhotoTask(config)


def write_raw_bundle(photo_dir: Path):
    raw = photo_dir / "DSC00001.ARW"
    xmp = photo_dir / "DSC00001.xmp"
    acr = photo_dir / "DSC00001.acr"
    raw.write_bytes(b"RAW DATA")
    xmp.write_bytes(b"xmp data")
    acr.write_bytes(b"acr data")
    return raw, xmp, acr


def test_default_plugins_build_raw_xmp_and_acr_tasks(photo_dir):
    write_raw_bundle(photo_dir)

    task = make_task(photo_dir)
    tasks_by_origin = {task.origin_file: task for task in task.process_tasks}

    assert set(tasks_by_origin) == {"DSC00001.ARW", "DSC00001.xmp", "DSC00001.acr"}
    assert tasks_by_origin["DSC00001.ARW"].update_file == f"{EXPECTED_BASE}.ARW"
    assert tasks_by_origin["DSC00001.xmp"].update_file == f"{EXPECTED_BASE}.xmp"
    assert tasks_by_origin["DSC00001.acr"].update_file == f"{EXPECTED_BASE}.acr"
    assert task.process_task_list == task.process_tasks


@pytest.mark.parametrize("extension", [".tif", ".tiff"])
def test_default_plugins_support_tiff_extensions(photo_dir, extension):
    (photo_dir / f"DSC00001{extension}").write_bytes(b"tiff data")

    task = make_task(photo_dir)

    assert len(task.process_tasks) == 1
    assert task.process_tasks[0].origin_file == f"DSC00001{extension}"
    assert task.process_tasks[0].update_file == f"{EXPECTED_BASE}{extension}"


def test_default_plugins_support_heic_without_sidecar(photo_dir):
    (photo_dir / "DSC00001.HEIC").write_bytes(b"heic data")
    (photo_dir / "DSC00001.xmp").write_bytes(b"xmp data")
    (photo_dir / "DSC00001.acr").write_bytes(b"acr data")

    task = make_task(photo_dir)

    assert len(task.process_tasks) == 1
    assert task.process_tasks[0].origin_file == "DSC00001.HEIC"
    assert task.process_tasks[0].update_file == f"{EXPECTED_BASE}.HEIC"


@pytest.mark.parametrize("extension", [".xmp", ".acr"])
def test_sidecar_only_file_is_ignored(photo_dir, extension):
    (photo_dir / f"DSC00001{extension}").write_bytes(b"sidecar data")

    task = make_task(photo_dir)

    assert task.process_tasks == []
    assert task.execute(dry_run=True) is None


def test_custom_metadata_plugin_supports_new_extension(photo_dir):
    (photo_dir / "DSC00001.foo").write_bytes(b"custom data")
    plugin = DummyMetadataPlugin(name="test.foo", extensions=[".foo"])

    task = make_task(photo_dir, metadata_plugins=[plugin])

    assert len(task.process_tasks) == 1
    assert task.process_tasks[0].update_file == f"{EXPECTED_BASE}.foo"


def test_metadata_plugin_module_loading(monkeypatch, tmp_path, photo_dir):
    (photo_dir / "DSC00001.bar").write_bytes(b"module plugin data")
    plugin_module = tmp_path / "sample_photo_plugin.py"
    plugin_module.write_text(
        "\n".join(
            [
                "from modules.photograph.metadata_plugins import PhotoMetadataPlugin",
                "class BarPlugin(PhotoMetadataPlugin):",
                "    def read_original_datetime(self, file_path: str) -> str:",
                "        return '2023:08:17 12:34:56'",
                "PLUGIN = BarPlugin(name='test.bar', extensions=['.bar'])",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    task = make_task(photo_dir, metadata_plugin_modules=["sample_photo_plugin"])

    assert len(task.process_tasks) == 1
    assert task.process_tasks[0].update_file == f"{EXPECTED_BASE}.bar"


def test_entry_point_plugin_loading(monkeypatch, photo_dir):
    (photo_dir / "DSC00001.baz").write_bytes(b"entry point plugin data")
    plugin = DummyMetadataPlugin(name="test.baz", extensions=[".baz"])

    class FakeEntryPoint:
        name = "test-baz"

        def load(self):
            return plugin

    class FakeEntryPoints(list):
        def select(self, group):
            assert group == metadata_plugin_module.DEFAULT_ENTRY_POINT_GROUP
            return self

    monkeypatch.setattr(
        metadata_plugin_module.metadata,
        "entry_points",
        lambda: FakeEntryPoints([FakeEntryPoint()]),
    )

    task = make_task(photo_dir, load_entry_point_plugins=True)

    assert len(task.process_tasks) == 1
    assert task.process_tasks[0].update_file == f"{EXPECTED_BASE}.baz"


def test_duplicate_plugin_extension_is_rejected(photo_dir):
    (photo_dir / "DSC00001.foo").write_bytes(b"custom data")
    first = DummyMetadataPlugin(name="test.foo.one", extensions=[".foo"])
    second = DummyMetadataPlugin(name="test.foo.two", extensions=[".foo"])

    with pytest.raises(MetadataPluginError, match="duplicated metadata plugin extension"):
        make_task(photo_dir, metadata_plugins=[first, second])


def test_unknown_extension_raises_error(photo_dir):
    (photo_dir / "notes.txt").write_text("not a photo", encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported file type '.txt'"):
        make_task(photo_dir)


def test_dry_run_does_not_rename_files(photo_dir):
    raw, xmp, acr = write_raw_bundle(photo_dir)
    task = make_task(photo_dir)

    task.execute(dry_run=True)

    assert raw.exists()
    assert xmp.exists()
    assert acr.exists()
    assert not (photo_dir / f"{EXPECTED_BASE}.ARW").exists()


def test_execute_renames_only_temp_files(monkeypatch, photo_dir):
    raw, xmp, acr = write_raw_bundle(photo_dir)
    monkeypatch.setattr(RenameRawPhotoTask, "confirm", lambda self: True)
    task = make_task(photo_dir)

    task.execute(dry_run=False)

    assert not raw.exists()
    assert not xmp.exists()
    assert not acr.exists()
    assert (photo_dir / f"{EXPECTED_BASE}.ARW").read_bytes() == b"RAW DATA"
    assert (photo_dir / f"{EXPECTED_BASE}.xmp").read_bytes() == b"xmp data"
    assert (photo_dir / f"{EXPECTED_BASE}.acr").read_bytes() == b"acr data"
