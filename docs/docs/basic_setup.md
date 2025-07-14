A minimal example of how to use the testbench:

```python
from testbench import Testbench


PATH = "config/testbench.yml"

tb = None
try:
    tb = Testbench(PATH)
    tb.initialize_tasks()

    tasks = tb.get_tasks()

    print("Running testbench...")
    while not tb.is_done():
        current = tb.iterate()

    print("Done")

except Exception as e:
    print(f"Error running testbench: {e}")
```

!!! success
    To see how to configure the testbench, see the [configuration](configuration.md) section.