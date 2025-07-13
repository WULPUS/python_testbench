from pathlib import Path
import shutil
from typing import Optional
import logging

from registry.common.fs import get_from_dir


class File:
    def __init__(
        self,
        path: Path,
        extension: str,
        configs: dict,
        output_dir: Path,
        name: Optional[str] = None,
    ):
        self.__path = path
        self.__extension = extension
        self.configs = configs
        self.name = name

        self.log = logging.getLogger(f"file.{self.name}")

        self.file = get_from_dir(self.__path, self.__extension, self.name)

        # Make backup of original file
        self.__file_backup = self.file.with_suffix(".bak")
        shutil.copyfile(self.file, self.__file_backup)

        self.replacements = {}
        self.parse()
        self.__replace()

        self.output_dir = output_dir / "files"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Copy current file to output directory
        shutil.copyfile(self.file, self.output_dir / self.file.name)
        shutil.copyfile(self.__file_backup, self.output_dir / self.__file_backup.name)

    def parse(self) -> None:
        raise NotImplementedError

    def __replace(self) -> None:
        lines = []
        with open(self.file, "r") as f:
            for i, line in enumerate(f):
                for key, replacements in self.replacements.items():
                    for line_num, value in replacements:
                        if i == line_num:
                            line = line.replace(key.strip(), value.strip())

                lines.append(line)

        with open(self.file, "w") as f:
            f.writelines(lines)

    def __del__(self) -> None:
        self.__file_backup.replace(self.file)

    @property
    def path(self) -> Path:
        return Path(self.file)
