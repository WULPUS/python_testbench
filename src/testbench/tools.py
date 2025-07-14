from pathlib import Path
import importlib.util
import inspect
import logging

from .tool import Tool


class TestbenchTools:
    def __init__(self, root: Path):
        self.log = logging.getLogger("tools")

        self.__root = root
        if not self.__root.is_dir():
            raise ValueError(f"Testbench root path {self.__root} is not a directory")

        self.__tools: dict[str, dict[str, dict]] = {}
        self.__discover()

        self.log.info(
            f"Discovered {len(self.__tools)} tool types "
            f"with {sum(len(v) for v in self.__tools.values())} tools"
        )

    def __discover(self) -> None:
        for type_dir in filter(Path.is_dir, self.__root.iterdir()):
            tool_type = type_dir.name
            if tool_type.startswith("__"):
                continue
            self.__tools[tool_type] = {}

            for py in sorted(type_dir.glob("*.py")):
                if py.name.startswith("__"):
                    continue
                tool_name = py.stem.split("_", 1)[-1]  # build_gcc -> gcc
                if tool_name == tool_type:
                    continue
                cls = self.__load_class(py, Tool)
                if cls:
                    self.__tools[tool_type][tool_name] = {
                        "cls": cls,
                        "path": py,
                        "type": tool_type,
                        "name": tool_name,
                    }
                    self.log.debug(f"  [+] {tool_type}/{tool_name} -> {py}")

            if not self.__tools[tool_type]:
                self.log.warning(f"No tools found in {type_dir}")

    @staticmethod
    def __load_class(py: Path, base) -> type | None:
        """
        Import `py` and return the *first* class that subclasses `base`.
        """
        spec = importlib.util.spec_from_file_location(py.stem, py)
        if spec is None:
            raise ImportError(f"Could not load module from {py}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore

        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if obj is not base and issubclass(obj, base) and obj.__module__ == py.stem:
                return obj
        return None

    def get(self) -> dict:
        return self.__tools
