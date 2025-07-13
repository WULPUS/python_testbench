from pathlib import Path
import logging


class TestbenchFiles:
    def __init__(self, config: dict):
        self.log = logging.getLogger("files")

        self.__config = config

        if "path" not in self.__config:
            raise KeyError("No path found in configuration")
        self.__files_path = Path(self.__config["path"])
        if not self.__files_path.exists():
            raise FileNotFoundError(f'Path "{self.__files_path}" does not exist')
        self.log.info(f"Files registry: {self.__files_path}")

        try:
            self.__files = {}
            self.__parse_files()
        except Exception as e:
            raise ValueError(f"Error setting up files: {e}")

    def __parse_files(self) -> None:
        self.log.debug("Parsing files configuration")

        for file_type in self.__config:
            if file_type == "path":
                continue

            self.log.debug(f"Processing file type: {file_type}")

            file_path = (self.__files_path / ("file_" + file_type)).with_suffix(".py")
            if not file_path.exists():
                raise FileNotFoundError(f'File path "{file_path}" does not exist')

            file_class = self.__config[file_type]

            global_vars = globals()
            try:
                exec(
                    f"from {str(file_path.with_suffix('')).replace('\\', '.')} import {file_class}",
                    global_vars,
                )
            except ImportError:
                raise ImportError(f"{file_class} not found in {file_path}")

            self.__files[file_type] = {
                "cls": global_vars[file_class],
                "path": file_path,
                "type": file_type,
            }

    def get(self) -> dict:
        return self.__files
