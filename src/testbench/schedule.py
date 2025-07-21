import time
import threading
from typing import Optional
import logging


class TestbenchSchedule:
    def __init__(self, config: dict, tools: dict, tasks: dict):
        self.log = logging.getLogger("schedule")

        self.__config = config
        self.__tools = tools
        self.__tasks = tasks

        try:
            self.__parse_schedule()
        except Exception as e:
            raise ValueError(f"Error setting up schedule: {e}")

        self.__current = self.__get_lowest(0)

        if self.__current is None:
            self.log.warning("Schedule is empty, no tasks to run")

    def __parse_schedule(self) -> None:
        self.log.debug("Parsing schedule configuration")

        if self.__config is None:
            return

        for task_name in self.__config:
            self.log.debug(f"Processing task: {task_name}")

            if task_name not in self.__tasks:
                raise KeyError(f'Task "{task_name}" not found in tasks configuration')

            task = self.__tasks[task_name]
            schedule_task = self.__config[task_name]

            if "order" not in schedule_task:
                raise KeyError(f'No order found in schedule for task "{task_name}"')
            task_order = schedule_task["order"]

            if "steps" not in schedule_task:
                raise KeyError(f'No steps found in schedule for task "{task_name}"')
            task_steps = schedule_task["steps"]

            cleanup_steps = schedule_task.get("cleanup", [])

            task_steps_list = []
            for step_name in task_steps:
                step = schedule_task["steps"][step_name]
                step_tool_type, step_tool = step.split(";")

                if step_tool_type not in task["tools"]:
                    raise KeyError(
                        f'Tool type "{step_tool_type}" not found in tools of task "{task_name}"'
                    )
                if step_tool != task["tools"][step_tool_type]["name"]:
                    raise KeyError(
                        f'No tool of type "{step_tool_type}" with name "{step_tool}" found in task "{task_name}"'
                    )
                if (
                    step_name
                    not in self.__tools[step_tool_type][step_tool]["cls"].__dict__
                ):
                    raise KeyError(
                        f'Tool "{step_tool}" of type "{step_tool_type}" does not have function "{step_name}"'
                    )

                task_steps_list.append(
                    {"type": step_tool_type, "tool": step_tool, "func": step_name}
                )

            task_cleanup_list = []
            for step_name in cleanup_steps:
                step = schedule_task["cleanup"][step_name]
                step_tool_type, step_tool = step.split(";")

                if step_tool_type not in task["tools"]:
                    raise KeyError(
                        f'Tool type "{step_tool_type}" not found in tools of task "{task_name}"'
                    )
                if step_tool != task["tools"][step_tool_type]["name"]:
                    raise KeyError(
                        f'No tool of type "{step_tool_type}" with name "{step_tool}" found in task "{task_name}"'
                    )
                if (
                    step_name
                    not in self.__tools[step_tool_type][step_tool]["cls"].__dict__
                ):
                    raise KeyError(
                        f'Tool "{step_tool}" of type "{step_tool_type}" does not have function "{step_name}"'
                    )

                task_cleanup_list.append(
                    {"type": step_tool_type, "tool": step_tool, "func": step_name}
                )

            self.__tasks[task_name]["order"] = task_order
            self.__tasks[task_name]["steps"] = task_steps_list
            self.__tasks[task_name]["cleanup"] = task_cleanup_list

    def __get_lowest(self, min: int) -> Optional[int]:
        # Get lowest order task above min
        lowest = None
        for task_name in self.__tasks:
            task_order = self.__tasks[task_name]["order"]
            if task_order < min:
                continue
            if not lowest or task_order < lowest:
                lowest = task_order

        return lowest

    def __get_tasks(self, order: int) -> dict:
        tasks = {}
        for task_name in self.__tasks:
            task_order = self.__tasks[task_name]["order"]
            if task_order == order:
                tasks[task_name] = self.__tasks[task_name]

        return tasks

    def is_done(self) -> bool:
        return self.__current is None

    def iterate(self) -> Optional[int]:
        self.log.debug("Iterating schedule")

        if self.__current is None:
            self.log.warning("No current task to run, schedule is done.")
            return None

        current = self.__current
        self.__current = self.__get_lowest(current + 1)

        current_tasks = self.__get_tasks(current)

        while len(current_tasks) == 0:
            current = self.__current
            if current is None:
                return None

            current_tasks = self.__get_tasks(current)

        self.log.debug(f"Running order {len(current_tasks)} tasks at order {current}")

        if len(current_tasks) > 1:
            threads = []
            for task_name in current_tasks:
                task = current_tasks[task_name]
                thread = threading.Thread(
                    target=self.__run_task, args=(task_name, task)
                )
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()
        else:
            task_name = list(current_tasks.keys())[0]
            task = current_tasks[task_name]
            self.__run_task(task_name, task)

        return current

    def __run_task(self, task_name: str, task: dict) -> None:
        self.log.info(f"Running task: {task_name}")

        for step in task["steps"]:
            self.log.info(f"Running step: {task_name}/{step['type']}/{step['func']}")
            start_time = time.time()
            try:
                getattr(task["tools"][step["type"]], step["func"])()
                end_time = time.time()
                self.log.info(
                    f"Done ({end_time - start_time:.2f}s): {task_name}/{step['type']}/{step['func']}"
                )
            except Exception as e:
                end_time = time.time()
                self.log.error(
                    f"Failed ({end_time - start_time:.2f}s): {task_name}/{step['type']}/{step['func']} ({e})"
                )
                break

        for step in task["cleanup"]:
            start_time = time.time()
            try:
                start_time = time.time()
                getattr(task["tools"][step["type"]], step["func"])()
                end_time = time.time()
                self.log.info(
                    f"Cleaned ({end_time - start_time:.2f}s): {task_name}/{step['type']}/{step['func']}"
                )
            except Exception as e:
                end_time = time.time()
                self.log.error(
                    f"Clean failed ({end_time - start_time:.2f}s): {task_name}/{step['type']}/{step['func']} ({e})"
                )
