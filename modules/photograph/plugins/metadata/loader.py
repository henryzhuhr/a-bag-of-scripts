"""元数据插件加载器。"""

from importlib import import_module, metadata
from typing import Iterable, List, Sequence

from .base import (
    DEFAULT_ENTRY_POINT_GROUP,
    MetadataPluginError,
    PhotoMetadataPlugin,
)


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
