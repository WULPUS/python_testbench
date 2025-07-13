import subprocess
import time
from typing import Any
import logging


class Tool:
    def __init__(
        self,
        type: str,
        name: str,
        task: dict,
        params: dict,
        env: dict,
    ):
        self.type = type
        self.type_name = name
        self.task = task
        self.params = params
        self.env = env

        self.log = logging.getLogger(f"tool.{self.type}.{self.type_name}")

        self.task_path = self.task["path"]
        self.task_name = self.task["name"]
        self.task_output = self.task["output"]

        self.output_dir = self.task_output / f"{self.type}_{self.type_name}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_command(self, command: str, type: str) -> None:
        self.log.debug(f"Running {type} command: '{command}'")

        stdout_file = (
            self.output_dir / f"{self.type}_{self.type_name}_{type}_stdout.txt"
        )
        stderr_file = (
            self.output_dir / f"{self.type}_{self.type_name}_{type}_stderr.txt"
        )

        self.log.debug(
            f"Redirecting {type} output to '{stdout_file}' and '{stderr_file}'"
        )

        with open(stdout_file, "w") as stdout, open(stderr_file, "w") as stderr:
            # Write header to stdout and stderr files
            stdout.write(f"stdout\ncommand: {command}\n")
            stdout.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            stdout.write("-" * 45 + "\n\n")
            stderr.write(f"stderr\ncommand: {command}\n")
            stderr.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            stderr.write("-" * 45 + "\n\n")

        result = None
        try:
            with open(stdout_file, "a") as stdout, open(stderr_file, "a") as stderr:
                result = subprocess.Popen(
                    command,
                    stdout=stdout,
                    stderr=stderr,
                    shell=True,
                    errors="ignore",
                    encoding="utf-8",
                )
                result.communicate()

                if result.returncode != 0:
                    raise Exception(
                        f"{type} command failed with code {result.returncode}"
                    )
        except subprocess.TimeoutExpired:
            if result is not None:
                result.kill()
                stdout, stderr = result.communicate()
            raise Exception(f"{type} command timed out")

    def ensure(self, loc: str, variable: str) -> Any:
        match loc:
            case "env":
                if variable not in self.env:
                    raise Exception(
                        f"Tool {self.type}/{self.type_name} for {self.task_name} requires {variable} in environment"
                    )

                return self.env[variable]

            case "params":
                if variable not in self.params:
                    raise Exception(
                        f"Tool {self.type}/{self.type_name} for {self.task_name} requires {variable} in params"
                    )

                return self.params[variable]

            case "file":
                if variable not in self.task["files"]:
                    raise Exception(
                        f"Tool {self.type}/{self.type_name} for {self.task_name} requires {variable} in files"
                    )

                return self.task["files"][variable]

            case _:
                raise Exception(f"Unknown location: {loc}")

    def run(self, command_name: str) -> None:
        self.log.info(f"Running command: {command_name}")
        # Run method of this class, e.g. command_name = 'build' -> self.build()
        if not hasattr(self, command_name):
            raise Exception(
                f"Command {command_name} not found in tool {self.type_name}/{self.type_name} for {self.task_name}"
            )

        getattr(self, command_name)()
