# Registering a New Task/Tool

Here, we register a new example tool to the testbench. We want this tool to write "Hello, <name\>!" to a file called `greeting.txt` in the current tasks output directory.


## Creating a New Tool Type

For this, we register a new tool type `hello` in the [`tools`](tools) directory by creating its own directory:

```bash
mkdir registry/tools/hello
```


## Creating a Tool Type Base Class

Then, we create a new tool type base class in the `registry/tools/hello/hello.py` file:

```python
from testbench import Tool


class Hello(Tool):
    def __init__(self, name: str, task: dict, params: dict, env: dict):
        super().__init__("hello", name, task, params, env) # Initialize the base class with the tool type "hello"

    def greet(self) -> None:
        raise NotImplementedError # We will implement this method in a subclass
```

As you can see, this class inherits from the `Tool` base class, which provides some basic functionality for the tool. The `greet` method is a placeholder for the actual implementation of the tool in a subclass.

> [!NOTE]
> The `Tool` base class provides some basic functionality for the tool, such as the `ensure` method to ensure that a parameter or file is present and the `run_command` method to run a command.


## Creating a Concrete Tool Implementation

We can now create the concrete implementation of the hello tool type, for example a `HelloFile` tool that writes the greeting to a file. We create a new file `registry/tools/hello/hello_file.py`:

```python
from registry.tools.hello.hello import Hello


class HelloFile(Hello):
    def __init__(self, task: dict, params: dict, env: dict):
        super().__init__("file", task, params, env)

        self.user = self.ensure("params", "user") # We cannot use `name` here, since it is reserved for the tool name

    def greet(self) -> None:
        with open(self.output_dir / "greeting.txt", "w") as f:
            f.write(f"Hello, {self.user}!\n")
```


## Testing the Tool

First, we need to register the new tool and its type in the `config/registry/tools.yml` file. We add the following entry to the `config/registry/tools.yml` file:

```yaml
path: registry/tools

hello:
  file: HelloFile
```

> [!WARNING]
> Here, the naming is important: The key `hello` is the tool type, and the value `file` is the name of the concrete implementation of the `HelloFile` class. The testbench will use this to search for the tool class when it is instantiated. In this case, the testbench will look for the `HelloFile` class in the `registry/tools/hello/hello_file.py` file. If we were to write:
> ```yaml
> path: registry/tools
> 
> hello:
>   console: HelloPrint
> ```
> Then, the testbench would look for the `HelloPrint` class in the `registry/tools/hello/hello_console.py` file.

We then use this in the `config/testbench.yml` and `config/tasks/greet_user.yml` files to create a task that uses this tool:

```yaml
tasks:
  greet_user: !inc config/tasks/greet_user.yml
```

```yaml
path: . # For now, we use the current directory as the project path, since we don't have a specific project path

tools:
  hello:
    name: file
    user: Cedric # We pass the user name as a parameter to the tool
```

As you can see, we use the tool type `hello` with the tool name `file`, which is the concrete implementation of the `HelloFile` class. We also pass a parameter `user` with the value `Cedric`, which will be used in the tool to greet the user.

We add the task to the `schedule.yml` file:

```yaml
greet_user:
  order: 1
  steps:
    greet: hello;file
```

As you can see, we define the step `greet` with the tool type `hello` and the tool name `file`, which will execute the `greet` method of the `HelloFile` class.


### Running the New Tool

Running the testbench with the added tool will produce the following output in the terminal:

```log
[12:00:00] INFO     Testbench:                                               testbench.py:27
                    'C:\dev\testbench\config\testbench.yml'                   
           INFO     Output directory: 'output\20250101-120000'               testbench.py:37
           INFO     Tools: 'registry\tools'                                      tools.py:16
           INFO     Initialized 3 tool types with 9 tools                        tools.py:24
           INFO     Files registry: registry\files                               files.py:16
           INFO     Initialized 1 tasks with 1 tools                             tasks.py:20
           INFO     Initialized testbench                                    testbench.py:98
           INFO     Initialized 1 tasks with 0 files and 1 tools            testbench.py:189
           INFO     Running testbench...                                          main.py:36
           INFO     Running task: greet_user                                 schedule.py:163
           INFO     Running step: greet_user/hello/greet                     schedule.py:166
           INFO     Done (0.00s): greet_user/hello/greet                     schedule.py:171
           INFO     Done                                                          main.py:40
```

You can see that the testbench initialized the tools and files, and then executed the `greet_user` task. The output directory is `output/20250101-120000`, which contains the output of the tool.
You can find the greeting in the `output/20250101-120000/greet_user/hello_file/greeting.txt` file:

```text
Hello, Cedric!
```

You can also see that the output directory is created with a timestamp, so you can run the testbench multiple times without overwriting the output.

> [!NOTE]
> All of this seems very complex and it is, but with a growing number of tools and files, it is necessary to keep the testbench organized and maintainable. The testbench is designed to be extensible, so you can easily add new tools and files without having to change the existing code.

To find out more about how to create and register new files, see the [new file](new_file.md) documentation.

To find out more about the structure of the testbench, see the [structure](structure.md) documentation.