"""Assign track numbers to MP3 files and write ID3 TRCK tags."""

from pathlib import Path

from mutagen.id3 import ID3, TRCK, ID3NoHeaderError


def assign_track_tags(output_paths: list[Path]) -> None:
    """Assign consecutive track numbers in filename order.

    Track numbers use at least two digits and expand to the width
    required by the total number of tracks. Existing total-track
    values are replaced with the track number only.
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

        tags.delall("TRCK")
        tags.add(
            TRCK(
                encoding=3,
                text=[f"{track_number:0{width}d}"],
            )
        )
        tags.save(path)
