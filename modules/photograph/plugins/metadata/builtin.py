"""内置摄影元数据插件。"""

from typing import Iterable, List

import exifread
import piexif
import pillow_heif

from modules.photograph._enums.format import PhotoFormat, SidecarFormat
from modules.photograph._enums.photo import SupportedPhotoRawExt

from .base import PhotoMetadataPlugin, normalize_extensions


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
