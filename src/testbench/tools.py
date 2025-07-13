from pathlib import Path
import logging


class TestbenchTools:
    def __init__(self, config: dict):
        self.log = logging.getLogger("tools")

        self.__config = config

        if "path" not in self.__config:
            raise KeyError("No path found in configuration")
        self.__tools_path = Path(self.__config["path"])
        if not self.__tools_path.exists():
            raise FileNotFoundError(f'Path "{self.__tools_path}" does not exist')
        self.log.info(f"Tools: '{self.__tools_path}'")

        try:
            self.__tools = {}
            self.__parse_tools()
        except Exception as e:
            raise ValueError(f"Error setting up tools: {e}")

        self.log.info(
            f"Initialized {len(self.__tools)} tool types with {sum(len(v) for v in self.__tools.values())} tools"
        )

    def __parse_tools(self) -> None:
        self.log.debug("Parsing tools configuration")

        for tool_type in self.__config:
            if tool_type == "path":
                continue

            self.log.debug(f"Processing tool type: {tool_type}")

            tool_type_path = self.__tools_path / tool_type
            if not tool_type_path.exists():
                raise FileNotFoundError(
                    f'Tool type path "{tool_type_path}" does not exist'
                )

            self.log.debug(f"Tool type path: {tool_type_path}")

            if tool_type not in self.__tools:
                self.__tools[tool_type] = {}

            for tool in self.__config[tool_type]:
                self.log.debug(f"Processing tool: {tool}")

                tool_path = (tool_type_path / (tool_type + "_" + tool)).with_suffix(
                    ".py"
                )
                if not tool_path.exists():
                    raise FileNotFoundError(f'Tool path "{tool_path}" does not exist')

                tool_class = self.__config[tool_type][tool]

                global_vars = globals()
                try:
                    exec(
                        f"from {str(tool_path.with_suffix('')).replace('\\', '.')} import {tool_class}",
                        global_vars,
                    )
                except ImportError:
                    raise ImportError(f"{tool_class} not found in {tool_path}")

                self.__tools[tool_type][tool] = {
                    "cls": global_vars[tool_class],
                    "path": tool_path,
                    "type": tool_type,
                    "name": tool,
                }

    def get(self) -> dict:
        return self.__tools
