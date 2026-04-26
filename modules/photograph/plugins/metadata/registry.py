"""元数据插件注册表。"""

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .base import (
    MetadataPluginError,
    PhotoMetadataPlugin,
    normalize_extension,
    normalize_extensions,
)


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
