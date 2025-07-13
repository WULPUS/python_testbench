## [`testbench.yml`](config/testbench.yml)

This configuration file contains the top-level testbench configuration. It contains the paths to the other configuration files, as well as the tasks to be executed in the testbench as well as their parameters.

The `testbench.yml` file must contain the `files`, `tools`, and `schedule` fields, which are the paths to the `files.yml`, `tools.yml`, and `schedule.yml` files, respectively.

Then, you can list all tasks to be executed under the `tasks` field.

A task quite a long description. You can have the following fields:

- `path`: Base path of the project which this path may describe, all other paths are relative to this path.
- `tools`: Dictionary of tools to be used in the task, with some optional configurations for each tool.
- `files`: Dictionary of files to be used in the task, with some optional configurations for each file.

The configurations for a tool or file can vary from tool or file. They will be passed to the tool constructor or file class constructor, respectively.

Here is an example of a `testbench.yml` file:

```yaml
schedule: !inc config/schedule.yml

registry:
  tools: !inc config/registry/tools.yml
  files: !inc config/registry/files.yml

tasks:
  program_stm:   !inc config/tasks/program_stm.yml
  test_frontend: !inc config/tasks/test_frontend.yml
  deploy_keys:   !inc config/tasks/deploy_keys.yml
```

> [!NOTE]
> The `!inc` directive is used to include other YAML files in the configuration. This allows you to split the configuration into multiple files for better organization and maintainability.
>
> You can also write the configuration directly in the `testbench.yml` file, but it is recommended to use the `!inc` directive to keep the configuration organized.


## Task Configuration

A task can look like this:

```yaml
path: <project_path>/fw/stm32

tools:
  flasher:
    name: openocd
    interface: cmsis-dap
    target: stm32l4

  builder:
    name: cmake

files:
  cmakelists:
    path: .
  
  c_header:
    path: .
    name: defines.h
    configs:
      DEVICE_NAME: TEST_DEVICE_NAME
```

Here, we define an example task that builds and flashes a firmware project for an STM32 microcontroller.

The `path` field specifies the base path of the project, which is used to resolve relative paths for files and tools.

We use two tools in this task: a flasher and a builder. The `flasher` tool is used to flash the firmware to the microcontroller, while the `builder` tool is used to build the firmware project. Each tool has a `name` field that specifies the tool type to be used, and additional parameters that are passed to the tool when it is executed.

We also define two files to be used in the task: a `CMakeLists.txt` file and a C header file. Each file has a `path` field that specifies the path to the file relative to the base path of the task. Optionally, you can also specify a `name` field to specify the specific name of the file, otherwise a suitable file will be chosen based on the file type.

The `cmakelists` file is used to configure the build system, while the `c_header` file is used to define some constants that will be used in the firmware code. The `configs` field allows you to specify some configurations for the file, which will be passed to the file class when it is instantiated.


## [`files.yml`](config/files.yml)

This configuration file contains all file types available to the testbench. A file type is a means for the testbench (or its tools) to read, manipulate and use its contents by describing it using a Python class.

The `files.yml` file must contain the `path` field; This is the path to the directory where the file classes are located (default: [`registry/files`](registry/files)).

You can then list all file types directly next to the `path` field, as a key-value pair with the file type as the key and the class name as the value. The file type is used to identify the file in the testbench, and the class name is used to instantiate the file class.

Here is an example of a `files.yml` file:

```yaml
path: registry/files

makefile: Makefile
cmakelists: CMakeLists
```


## [`tools.yml`](config/tools.yml)

This configuration file contains all tools available to the testbench. A tool is a means for the testbench to run a command on the system, such as a compiler or a flasher by describing it using a Python class.

The `tools.yml` file must contain the `path` field; This is the path to the directory where the tool classes are located (default: [`registry/tools`](registry/tools)).

A tool can be part of a tool type, which means that it can be used in a specific context, such as a compiler or a flasher. You can list all tool types directly next to the `path` field, with the id to be used in other configurations as the key and a list of tools as key-value pairs with the tool type as the key and the class name as the value.

Here is an example of a `tools.yml` file:

```yaml
path: registry/tools

builder:
  makefile: BuilderMakefile
  cmake: BuilderCMake

flasher:
  makefile: FlasherMakefile
  openocd: FlasherOpenOCD
```


## [`schedule.yml`](config/schedule.yml)

This configuration file contains the schedule for the testbench. A schedule is a list of tasks (described in `testbench.yml`) to be executed in a specific order, with each project having a set of steps to be executed.

Each task has to contain the `order` field, which is a number that determines the order in which the task will be executed. The lower the number, the earlier the task will be executed. Multiple tasks can have the same order, in which case they will be executed concurrently.

Each task then contains the `steps` and `cleanup` fields, which are lists of steps to be executed. The `steps` field contains the steps to be executed before the task is considered complete, while the `cleanup` field contains the steps to be executed after the task is complete, regardless of whether it was successful or not.

A task step is a key-value pair, where the key is the step function (e.g. `build`, `erase`, `flash`, `clean`) and the value is a string of the form `tool_type;tool_id`. The tool type is the type of tool to be used (e.g. `builder`, `flasher`), and the tool id is the id of the tool to be used (e.g. `makefile`, `ses`).

Here is an example of a `schedule.yml` file:

```yaml
program_stm:
  order: 1
  steps:
    build: builder;cmake
    erase: flasher;openocd
    flash: flasher;openocd
  cleanup:
    clean: builder;cmake

test_frontend:
  order: 2
  steps:
    test_excitation: tester;ad2
    test_reception: tester;ad2

deploy_keys:
  order: 3
  steps:
    deploy: backend;javascript
```


## `.env`

As you can see in the example above, some paths are defined as `<project_path>`. These are environment variables that you can define in a `.env` file in the root of the project. The testbench will automatically load these variables and replace them in the configuration files.

A tool or file can also reference environment variables in their configurations, which will be replaced by the testbench when the task is executed.

Here is an example of a `.env` file:

```ini
PROJECT_PATH=C:/dev/company/cool_device
```

To find out more about how to use the tools and files, see the [tools](tools.md) and [files](files.md) documentation.