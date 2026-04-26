"""
摄影文件元数据插件系统。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from importlib import import_module, metadata
from typing import Iterable, List, Optional, Sequence

import exifread
import piexif
import pillow_heif

from modules.photograph._enums.format import PhotoFormat, SidecarFormat
from modules.photograph._enums.photo import SupportedPhotoHeifExt, SupportedPhotoRawExt

DEFAULT_ENTRY_POINT_GROUP = "a_bag_of_scripts.photograph.metadata_plugins"


def normalize_extension(extension: str) -> str:
    if not extension:
        raise ValueError("file extension must not be empty")
    extension = extension.lower()
    return extension if extension.startswith(".") else f".{extension}"


def normalize_extensions(extensions: Iterable[str]) -> set[str]:
    return {normalize_extension(extension) for extension in extensions}


class MetadataPluginError(RuntimeError):
    """元数据插件加载或注册失败。"""


class PhotoMetadataPlugin(ABC):
    """读取照片拍摄时间的插件基类。"""

    name: str
    version: str
    extensions: set[str]
    sidecar_extensions: List[str]

    def __init__(
        self,
        name: str,
        extensions: Iterable[str],
        version: str = "0.1.0",
        sidecar_extensions: Optional[Iterable[str]] = None,
    ):
        self.name = name
        self.version = version
        self.extensions = normalize_extensions(extensions)
        self.sidecar_extensions = sorted(
            normalize_extensions(sidecar_extensions or [])
        )
        if not self.extensions:
            raise ValueError(f"metadata plugin '{self.name}' must support extensions")

    @abstractmethod
    def read_original_datetime(self, file_path: str) -> str:
        """返回格式为 YYYY:MM:DD HH:MM:SS 的拍摄时间。"""
        raise NotImplementedError


class ExifMetadataPlugin(PhotoMetadataPlugin):
    """基于 exifread 的内置 EXIF 插件。"""

    def read_original_datetime(self, file_path: str) -> str:
        with open(file_path, "rb") as f:
            exif_data = exifread.process_file(f, details=False, strict=True)
        date_time = exif_data["EXIF DateTimeOriginal"]
        return str(getattr(date_time, "printable", date_time))


class HeifMetadataPlugin(PhotoMetadataPlugin):
    """基于 pillow-heif 和 piexif 的内置 HEIF 插件。"""

    def read_original_datetime(self, file_path: str) -> str:
        heif_file = pillow_heif.open_heif(file_path)
        exif_dict = piexif.load(heif_file.info["exif"], key_is_name=True)
        exif_data = exif_dict["Exif"]
        if exif_data is None:
            raise ValueError(f"metadata 'Exif' not found in file '{file_path}'")
        date_time = exif_data["DateTimeOriginal"]
        if isinstance(date_time, bytes):
            return str(date_time, "utf-8")
        return str(date_time)


@dataclass(frozen=True)
class RegisteredMetadataPlugin:
    plugin: PhotoMetadataPlugin
    source: str


class PhotoMetadataPluginRegistry:
    """扩展名到元数据插件的注册表。"""

    def __init__(
        self,
        plugins: Iterable[PhotoMetadataPlugin],
        ignored_extensions: Optional[Iterable[str]] = None,
    ):
        self._registered_plugins: List[RegisteredMetadataPlugin] = []
        self._plugins_by_extension: dict[str, RegisteredMetadataPlugin] = {}
        self.ignored_extensions = normalize_extensions(ignored_extensions or [])
        for plugin in plugins:
            self.register(plugin)

    @property
    def registered_plugins(self) -> List[RegisteredMetadataPlugin]:
        return list(self._registered_plugins)

    def register(self, plugin: PhotoMetadataPlugin, source: str = "manual") -> None:
        if not isinstance(plugin, PhotoMetadataPlugin):
            raise TypeError(f"invalid metadata plugin type: {type(plugin).__name__}")

        registered_plugin = RegisteredMetadataPlugin(plugin=plugin, source=source)
        for extension in plugin.extensions:
            existing = self._plugins_by_extension.get(extension)
            if existing is not None:
                raise MetadataPluginError(
                    f"duplicated metadata plugin extension '{extension}': "
                    f"'{existing.plugin.name}' and '{plugin.name}'"
                )
            self._plugins_by_extension[extension] = registered_plugin
        self._registered_plugins.append(registered_plugin)

    def find(self, file_ext: str) -> Optional[PhotoMetadataPlugin]:
        registered_plugin = self._plugins_by_extension.get(normalize_extension(file_ext))
        if registered_plugin is None:
            return None
        return registered_plugin.plugin

    def is_ignored(self, file_ext: str) -> bool:
        return normalize_extension(file_ext) in self.ignored_extensions


def default_metadata_plugins(
    exif_supported_ext: Iterable[str],
    heif_supported_ext: Iterable[str],
) -> List[PhotoMetadataPlugin]:
    exif_extensions = normalize_extensions(exif_supported_ext)
    raw_extensions = exif_extensions & normalize_extensions(
        e.value for e in SupportedPhotoRawExt
    )
    plain_exif_extensions = (
        exif_extensions - raw_extensions
    ) | normalize_extensions(
        [
            PhotoFormat.JPG.value,
            PhotoFormat.JPEG.value,
            PhotoFormat.TIF.value,
            PhotoFormat.TIFF.value,
        ]
    )

    plugins: List[PhotoMetadataPlugin] = []
    if raw_extensions:
        plugins.append(
            ExifMetadataPlugin(
                name="builtin.exif-raw",
                extensions=raw_extensions,
                sidecar_extensions=[SidecarFormat.XMP.value, SidecarFormat.ACR.value],
            )
        )
    if plain_exif_extensions:
        plugins.append(
            ExifMetadataPlugin(
                name="builtin.exif-image",
                extensions=plain_exif_extensions,
            )
        )

    heif_extensions = normalize_extensions(heif_supported_ext)
    if heif_extensions:
        plugins.append(
            HeifMetadataPlugin(
                name="builtin.heif",
                extensions=heif_extensions,
            )
        )
    return plugins


def collect_plugins_from_module(module) -> List[PhotoMetadataPlugin]:
    if hasattr(module, "get_plugins"):
        candidates = module.get_plugins()
    elif hasattr(module, "PLUGINS"):
        candidates = module.PLUGINS
    elif hasattr(module, "PLUGIN"):
        candidates = [module.PLUGIN]
    else:
        raise MetadataPluginError(
            f"metadata plugin module '{module.__name__}' must expose "
            "PLUGIN, PLUGINS, or get_plugins()"
        )

    if isinstance(candidates, PhotoMetadataPlugin):
        candidates = [candidates]
    if not isinstance(candidates, Sequence):
        raise MetadataPluginError(
            f"metadata plugin module '{module.__name__}' returned invalid plugins"
        )

    plugins: List[PhotoMetadataPlugin] = []
    for candidate in candidates:
        if not isinstance(candidate, PhotoMetadataPlugin):
            raise MetadataPluginError(
                f"metadata plugin module '{module.__name__}' returned invalid "
                f"plugin type: {type(candidate).__name__}"
            )
        plugins.append(candidate)
    return plugins


def load_plugins_from_module_paths(module_paths: Iterable[str]) -> List[PhotoMetadataPlugin]:
    plugins: List[PhotoMetadataPlugin] = []
    for module_path in module_paths:
        module = import_module(module_path)
        plugins.extend(collect_plugins_from_module(module))
    return plugins


def load_plugins_from_entry_points(
    group: str = DEFAULT_ENTRY_POINT_GROUP,
) -> List[PhotoMetadataPlugin]:
    plugins: List[PhotoMetadataPlugin] = []
    entry_points = metadata.entry_points()
    if hasattr(entry_points, "select"):
        selected_entry_points = entry_points.select(group=group)
    else:
        selected_entry_points = entry_points.get(group, [])

    for entry_point in selected_entry_points:
        loaded = entry_point.load()
        if isinstance(loaded, PhotoMetadataPlugin):
            plugins.append(loaded)
        elif callable(loaded):
            candidates = loaded()
            if isinstance(candidates, PhotoMetadataPlugin):
                candidates = [candidates]
            if not isinstance(candidates, Sequence):
                raise MetadataPluginError(
                    f"metadata plugin entry point '{entry_point.name}' returned "
                    "invalid plugins"
                )
            plugins.extend(candidates)
        else:
            raise MetadataPluginError(
                f"metadata plugin entry point '{entry_point.name}' is invalid"
            )

    for plugin in plugins:
        if not isinstance(plugin, PhotoMetadataPlugin):
            raise MetadataPluginError(
                f"metadata plugin entry point returned invalid plugin type: "
                f"{type(plugin).__name__}"
            )
    return plugins
