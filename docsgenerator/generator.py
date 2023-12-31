from math import e
from taskcli import task, tt, taskcliconfig, examples
import taskcli
from datetime import datetime
import os
import logging
log =  logging.getLogger(__name__)

def autogen_header():
    """Return the "page was autogenerated" header."""
    #> timedate = datetime.now(tz=None).strftime("%Y-%m-%d %H:%M:%S")
    #> return f"""(This page was autogenerated by `{timedate}`, do not edit manually)\n"""
    return """(This page was autogenerated, do not edit manually)\n"""


BR = "  " # Github markdown needs two spaces for a line break

def generate_settings() -> str:
    """Generate the documentation page with all the settings."""
    config = taskcliconfig.TaskCLIConfig()

    out = "# Configuration fields\n"
    out += autogen_header()

    for field in config.get_fields():
        out += f"### {field.name}\n"
        out += f"{field.desc}{BR}\n"
        if field.env:
            out += f"{field.env_var_name}{BR}\n"
        else:
            out += f"(no env var){BR}\n"

        out += "\n"

    return out


PAGE_EXAMPLES_TEXT = """Best way to learn is by example. Here are some examples of how to use `taskcli`.

You can also view them by running `taskcli --examples` on the terminal.
"""


def generate_example() -> str:
    """Generate the page with examples."""
    examples = taskcli.examples.get_examples()
    out = "# Usage Examples\n"
    out += autogen_header()
    out += PAGE_EXAMPLES_TEXT

    for example in examples:
        out += f"### {example.title}\n"
        if example.desc:
            for line in example.desc.split("\n"):
                out += f"{line}{BR}\n"


        out += "```python\n"
        out += taskcli.examples.format_text_to_markdown(example)
        if out[-1] != "\n":
            out += "\n"
        out += "```\n"
    return out


def write_file(path: str, content: str) -> None:
    assert path.startswith("../docs/")
    abs_path = os.path.abspath(path)
    with open(abs_path, "w") as f:
        f.write(content)

    log.info(f"Written file: {abs_path}")
