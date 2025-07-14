from pathlib import Path
import importlib.util
import inspect
import logging

from .file import File


class TestbenchFiles:
    def __init__(self, root: str):
        self.log = logging.getLogger("files")

        self.__root = Path(root).resolve()
        if not self.__root.is_dir():
            raise ValueError(f"Testbench root path {self.__root} is not a directory")

        self.__files: dict[str, dict] = {}
        self.__discover()

        self.log.info(f"Discovered {len(self.__files)} file types")

    # ------------------------------------------------------------------
    def __discover(self) -> None:
        for py in sorted(self.__root.glob("file_*.py")):
            file_type = py.stem.split("_", 1)[-1]  # file_json -> json
            cls = self.__load_class(py)
            if cls == File:
                continue
            if cls:
                self.__files[file_type] = {
                    "cls": cls,
                    "path": py,
                    "type": file_type,
                }
                self.log.debug(f"  [+] {file_type} -> {py}")

    @staticmethod
    def __load_class(py: Path):
        spec = importlib.util.spec_from_file_location(py.stem, py)
        if spec is None:
            raise ImportError(f"Could not load module from {py}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore

        for _, obj in inspect.getmembers(mod, inspect.isclass):
            # Only consider classes defined in this module, not imported ones
            if hasattr(obj, "parse") and obj.__module__ == py.stem:
                return obj
        return None

    def get(self) -> dict:
        return self.__files
