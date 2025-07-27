from pathlib import Path
import logging


class TestbenchTasks:
    def __init__(self, config: dict, tools: dict, files: dict, output_dir: Path):
        self.log = logging.getLogger("tools")

        self.__config = config
        self.__tools = tools
        self.__files = files
        self.__output_dir = output_dir

        try:
            self.__tasks = {}
            self.__parse_tasks()
        except Exception as e:
            raise ValueError(f"Error parsing tasks: {e}")

        if not self.__tasks:
            self.log.warning("No task configurations provided")
        else:
            self.log.info(
                f"Initialized {len(self.__tasks)} tasks with {sum(len(v['tools']) for v in self.__tasks.values())} tools"
            )

    def __parse_tasks(self) -> None:
        self.log.debug("Parsing tasks configuration")

        if self.__config is None:
            return

        for task_name in self.__config:
            self.log.debug(f"Processing task: {task_name}")

            task = self.__config[task_name]

            if "path" not in task:
                raise KeyError(f'No path found in configuration for task "{task_name}"')
            if "tools" not in task:
                raise KeyError(
                    f'No tools found in configuration for task "{task_name}"'
                )

            task_path = Path(task["path"]).absolute()
            if not task_path.exists():
                raise FileNotFoundError(
                    f'Path "{task_path}" for task "{task_name}" does not exist'
                )

            self.log.debug(f"Task path: {task_path}")

            task_tools = {}
            for tool_type in task["tools"]:
                if tool_type not in self.__tools:
                    raise KeyError(
                        f'Tool type "{tool_type}" not found in tools configuration'
                    )

                for tool_name in task["tools"][tool_type]:
                    if tool_name not in self.__tools[tool_type]:
                        raise KeyError(
                            f'Tool "{tool_name}" not found in tools configuration'
                        )

                    tool_params = task["tools"][tool_type][tool_name]
                    if tool_params is None:
                        tool_params = {}

                    if tool_type not in task_tools:
                        task_tools[tool_type] = {}

                    task_tools[tool_type][tool_name] = {
                        "name": tool_name,
                        "params": tool_params,
                    }

            task_files = {}
            if "files" in task:
                for file_type in task["files"]:
                    if file_type not in self.__files:
                        raise KeyError(
                            f'File type "{file_type}" not found in files configuration'
                        )

                    if "path" not in task["files"][file_type]:
                        raise KeyError(
                            f'No path found in "{file_type}" file configuration for task "{task}"'
                        )
                    file_path = task_path / task["files"][file_type]["path"]

                    file_configs = task["files"][file_type].get("configs", [])

                    file_name = task["files"][file_type].get("name", None)

                    task_files[file_type] = {
                        "path": file_path,
                        "configs": file_configs,
                        "name": file_name,
                    }

            self.__tasks[task_name] = {
                "name": task_name,
                "path": task_path,
                "output": self.__output_dir / task_name,
                "tools": task_tools,
                "files": task_files,
            }

    def get(self) -> dict:
        return self.__tasks
