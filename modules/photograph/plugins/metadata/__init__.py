"""摄影元数据插件系统公开 API。"""

from .base import (
    DEFAULT_ENTRY_POINT_GROUP,
    MetadataPluginError,
    PhotoMetadataPlugin,
    normalize_extension,
    normalize_extensions,
)
from .builtin import ExifMetadataPlugin, HeifMetadataPlugin, default_metadata_plugins
from .loader import (
    collect_plugins_from_module,
    load_plugins_from_entry_points,
    load_plugins_from_module_paths,
    metadata,
)
from .registry import PhotoMetadataPluginRegistry, RegisteredMetadataPlugin

__all__ = [
    "DEFAULT_ENTRY_POINT_GROUP",
    "MetadataPluginError",
    "PhotoMetadataPlugin",
    "normalize_extension",
    "normalize_extensions",
    "ExifMetadataPlugin",
    "HeifMetadataPlugin",
    "default_metadata_plugins",
    "collect_plugins_from_module",
    "load_plugins_from_entry_points",
    "load_plugins_from_module_paths",
    "metadata",
    "PhotoMetadataPluginRegistry",
    "RegisteredMetadataPlugin",
]
