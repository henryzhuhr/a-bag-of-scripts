"""元数据插件基础类型。"""

from abc import ABC, abstractmethod
from typing import Iterable, List, Optional


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
