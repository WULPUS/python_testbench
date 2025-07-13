This project requires the [uv](https://astral.sh/uv/) Python package to run. You can install it using pip:

```bash
pip install uv
```

This library can be included in a Python project as a **submodule**. If you add the submodule to the base directory of your project, you need to add the following line to the `pyproject.toml` file:

```toml
[tool.uv.workspace]
members = ["python_testbench"]

[tool.uv.sources]
python_testbench = { workspace = true }
testbench = { workspace = true }
```

And then add the testbench via the command:

```bash
uv add python_testbench
```

Now, you can move to a [basic setup](basic_setup.md) to get started with the testbench.