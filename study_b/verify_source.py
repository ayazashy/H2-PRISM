"""Verify the official MHC release and inventory it without extracting files."""
import argparse
import hashlib
import json
import re
import stat
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

RECORD = "https://zenodo.org/records/19036733"
DOI = "10.5281/zenodo.19036733"
EXPECTED_MD5 = "64cbe2a68c0af5dc2e4a0a9690003eac"
EXPECTED_SIZE = 377874239


def inventory(path):
    if path.stat().st_size != EXPECTED_SIZE:
        raise ValueError("Archive byte count does not match the official release")
    with path.open("rb") as stream:
        md5 = hashlib.file_digest(stream, "md5").hexdigest()
        if md5 != EXPECTED_MD5:
            raise ValueError(f"Official MD5 mismatch: {md5}")
        stream.seek(0)
        sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
    with ZipFile(path) as archive:
        members = []
        seen = set()
        experiments = {}
        overview = []
        for entry in archive.infolist():
            name = entry.filename
            member = PurePosixPath(name)
            if (member.is_absolute() or ".." in member.parts or "\\" in name
                    or ":" in name or stat.S_ISLNK(entry.external_attr >> 16)
                    or str(member).casefold() in seen):
                raise ValueError(f"Unsafe or ambiguous member: {name!r}")
            seen.add(str(member).casefold())
            if entry.is_dir():
                continue
            members.append({"path": name, "bytes": entry.file_size,
                            "crc32": f"{entry.CRC:08x}"})
            match = re.fullmatch(r"Experiment (\d+)\.xlsx", member.name)
            if match:
                run = int(match[1])
                if run in experiments:
                    raise ValueError(f"Duplicate experiment {run}")
                experiments[run] = name
            if member.name == "Experiment Overview.xlsx":
                overview.append(name)
        if set(experiments) != set(range(1, 30)) or len(overview) != 1:
            raise ValueError("Unexpected experiment workbook inventory")
    return {"record": RECORD, "doi": DOI, "version": "1.2",
            "archive_bytes": EXPECTED_SIZE, "md5": md5, "sha256": sha256,
            "overview": overview[0], "experiments": experiments, "members": members}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    manifest = inventory(args.archive)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(manifest['experiments'])} experiment workbooks. "
          f"SHA-256 {manifest['sha256']}")


if __name__ == "__main__":
    main()
