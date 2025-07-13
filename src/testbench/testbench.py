from pathlib import Path
import time
import shutil
from typing import Optional
import logging

from dotenv import load_dotenv, dotenv_values
import yaml
import yaml_include

from .common.config import load_config
from .tools import TestbenchTools
from .files import TestbenchFiles
from .tasks import TestbenchTasks
from .schedule import TestbenchSchedule


class Testbench:
    def __init__(
        self, config_path: Path | str, output_dir: Optional[Path | str] = None
    ):
        self.log = logging.getLogger("testbench")

        yaml.add_constructor("!inc", yaml_include.Constructor(), yaml.SafeLoader)

        self.__config_path, self.__config = load_config(config_path)
        self.log.info(f"Testbench: '{self.__config_path}'")

        if output_dir:
            self.__output_base_dir = Path(output_dir)
        else:
            self.__output_base_dir = Path("output")
        self.__output_base_dir.mkdir(parents=True, exist_ok=True)

        self.__output_dir = self.__output_base_dir / time.strftime("%Y%m%d-%H%M%S")
        self.__output_dir.mkdir()
        self.log.info(f"Output directory: '{self.__output_dir}'")

        # Copy config file to output directory
        config_output_dir = self.__output_dir / "config"
        config_output_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.__config_path, config_output_dir / self.__config_path.name)
        self.log.debug(
            f"Copied '{self.__config_path}' to '{config_output_dir / self.__config_path.name}'"
        )

        # Go through the config and copy all includes
        includes_output_dir = config_output_dir / "includes"
        includes_output_dir.mkdir(parents=True, exist_ok=True)
        with open(self.__config_path, "r") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if "!inc" in line:
                include_path = line.split("!inc")[1].strip()
                self.log.debug(f"Copying include: {include_path}")
                shutil.copy(
                    include_path,
                    includes_output_dir / Path(include_path).name,
                )

        # Copy full config to output directory
        with open(self.__output_dir / "config.yml", "w") as f:
            yaml.dump(self.__config, f, default_flow_style=False)
        self.log.debug(f"Copied full config to '{self.__output_dir / 'config.yml'}'")

        try:
            self.__env = None
            self.__handle_env()
        except Exception as e:
            raise ValueError(f"Error setting up environment: {e}")

        try:
            self.__tools = TestbenchTools(self.__get("registry/tools")).get()
        except Exception as e:
            raise ValueError(f"Error setting up tools: {e}")

        try:
            self.__files = TestbenchFiles(self.__get("registry/files")).get()
        except Exception as e:
            raise ValueError(f"Error setting up files: {e}")

        try:
            self.__tasks = TestbenchTasks(
                self.__get("tasks"), self.__tools, self.__files, self.__output_dir
            ).get()
        except Exception as e:
            raise ValueError(f"Error setting up tasks: {e}")

        try:
            self.__schedule = TestbenchSchedule(
                self.__get("schedule"),
                self.__tools,
                self.__tasks,
            )
        except Exception as e:
            raise ValueError(f"Error setting up schedule: {e}")

        self.log.info("Initialized testbench")

    def __get(self, key: str) -> dict:
        if "/" not in key:
            if key not in self.__config:
                raise KeyError(f'Key "{key}" not found in configuration')
            return self.__config[key]
        else:
            keys = key.split("/")
            temp = self.__config.copy()
            for k in keys[:-1]:
                if k not in temp:
                    raise KeyError(f'Key "{k}" not found in configuration')
                temp = temp[k]
            if keys[-1] not in temp:
                raise KeyError(f'Key "{keys[-1]}" not found in configuration')
            return temp[keys[-1]]

    def __handle_env(self):
        self.log.debug("Handling environment variables")

        load_dotenv()
        self.__env = dotenv_values()

        # Place environment into output directory
        with open(self.__output_dir / ".env", "w") as f:
            for key, value in self.__env.items():
                f.write(f"{key}={value}\n")

        def replace_env(obj, env: dict):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    obj[key] = replace_env(value, env)
            elif isinstance(obj, list):
                for i, value in enumerate(obj):
                    obj[i] = replace_env(value, env)
            elif isinstance(obj, str):
                for key, value in env.items():
                    obj = obj.replace(f"<{key.lower()}>", value)

            return obj

        self.log.debug(f"Set up {len(self.__env)} environment variables")

        self.__config = replace_env(self.__config, self.__env)

    def initialize_tasks(self) -> None:
        self.log.debug("Initializing tasks")

        for task_name in self.__tasks:
            self.log.debug(f"Initializing task: {task_name}")

            task = self.__tasks[task_name]

            # Instantiate file classes
            # TODO: Only initialize files needed in steps
            for file in task["files"]:
                file_cls = self.__files[file]["cls"]
                file_path = task["files"][file]["path"]
                file_configs = task["files"][file]["configs"]
                file_name = task["files"][file]["name"]
                file_instance = file_cls(
                    file_path,
                    file_configs,
                    self.__output_dir / task_name,
                    file_name,
                )
                task["files"][file] = file_instance

            # Instantiate only tools referenced in the schedule steps
            needed_tool_types = {step["type"] for step in task.get("steps", [])}
            for tool_type in needed_tool_types:
                tool_info = task["tools"].get(tool_type)
                if not tool_info:
                    raise KeyError(
                        f'Tool type "{tool_type}" not configured in task "{task_name}"'
                    )
                tool_name = tool_info["name"]
                tool_params = tool_info["params"]
                tool_cls = self.__tools[tool_type][tool_name]["cls"]
                tool_instance = tool_cls(task, tool_params, self.__env)
                task["tools"][tool_type] = tool_instance

                for step in task.get("steps", []):
                    if step["type"] == tool_type and step["tool"] == tool_name:
                        step["tool_instance"] = tool_instance

                        # get function from tool class
                        tool_func = getattr(tool_instance, step["func"])
                        step["func_instance"] = tool_func

        self.log.info(
            f"Initialized {len(self.__tasks)} tasks with {sum(len(v['files']) for v in self.__tasks.values())} files and {sum(len(v['tools']) for v in self.__tasks.values())} tools"
        )

    def get_tasks(self) -> dict:
        return self.__tasks

    def __del__(self) -> None:
        if hasattr(self, "__tasks"):
            self.log.debug("Cleaning up files")
            for task_name in self.__tasks:
                task = self.__tasks[task_name]
                for file in list(task["files"].keys()):
                    del task["files"][file]

    def iterate(self) -> None:
        self.__schedule.iterate()

    def is_done(self) -> bool:
        return self.__schedule.is_done()

    def get_output_dir(self) -> Path:
        return self.__output_dir
