"""Assign track numbers to MP3 titles and write ID3 TIT2 tags."""

from pathlib import Path

from mutagen.id3 import ID3, TIT2, ID3NoHeaderError


def assign_title_tags(output_paths: list[Path]) -> None:
    """Prefix MP3 titles with their zero-padded track number.

    Files are sorted case-insensitively by filename.
    If no TIT2 tag exists, the filename without its extension
    is used as the title.
    """
    ordered_paths = sorted(
        output_paths,
        key=lambda path: path.name.casefold(),
    )

    if not ordered_paths:
        return

    width = max(2, len(str(len(ordered_paths))))

    for track_number, path in enumerate(ordered_paths, start=1):
        try:
            tags = ID3(path)
        except ID3NoHeaderError:
            tags = ID3()

        existing_title = tags.get("TIT2")

        if existing_title:
            title = str(existing_title.text[0])
        else:
            title = path.stem

        tags.delall("TIT2")
        tags.add(
            TIT2(
                encoding=3,
                text=[f"{track_number:0{width}d} - {title}"],
            )
        )
        tags.save(path)
