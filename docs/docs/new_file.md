Here, we register a new example file to the testbench. We want this file to be a simple text file that contains a greeting, to be used in the `greet_user` task we created earlier.

## Creating a Concrete File Implementation

For this, we create a new file type `greeting` in `registry/files/file_greeting.py`:

```python
from pathlib import Path
from typing import Optional

from testbench import File


class Greeting(File):
    def __init__(
        self, path: Path, configs: dict, output_dir: Path, name: Optional[str] = None
    ):
        super().__init__(path, "txt", configs, output_dir, name)
```

As you can see, this class inherits from the `File` base class, which provides some basic functionality for the file, including the `parse` method, which is used to read the file and extract the relevant information. In this case, we do not need to implement the `parse` method, since it already is a basic implementation that replaces placeholders in the file with the actual values from the `configs` dictionary.

## Testing the Tool

We then register the new file type in the `config/registry/files.yml` file by adding the following entry:

```yaml
path: registry/files

greeting: Greeting
```

We then add this file to the `greet_user` task in the `config/tasks/greet_user.yml` file:

```yaml
path: test # Now, we use the test directory as the project path

tools:
  hello:
    name: file
    user: Cedric # We pass the user name as a parameter to the tool

files:
  greeting:
    path: .
    name: greeting.txt
    configs:
      USER_NAME: Cedric # We pass the user name as a configuration to the file
```

We create a new file `test/greeting.txt` with the following content:

```text
Hello, USER_NAME!
```

Since we use the `greeting` file type, the testbench will automatically read the `greeting.txt` file and replace the `USER_NAME` placeholder with the actual user name `Cedric`. We thus do not need to add any additional steps to the `schedule.yml` file, since the `greeting` file type will handle the replacement automatically.

This will then produce the same output as before, but now we also have a `files` directory in the task output directory that contains the `greeting.txt` file with the following content:

```text
Hello, Cedric!
```

This means that the `USER_NAME` placeholder in the `greeting.txt` file was replaced with the actual user name `Cedric`.

As well as `greeting.bak`, which is a backup of the original file before the replacement was made.

!!! info
    In the future, the functionality of directly writing to a file will be moved to the `File` base class, so that all file types can use it. This will make it easier to create new file types that need to write to a file. Also, we should be able to create new files and not relay on existing files, so that we can create files from scratch.

!!! success
    To find out more about how to create and register new tools and tasks, see the [new tool](new_tool.md) documentation.

    To find out more about the structure of the testbench, see the [structure](structure.md) documentation.