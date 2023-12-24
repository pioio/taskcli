# name, desc


import dataclasses
import sys

LIST_DETAILS_LOW = 0

# Name   desc  mandatory args
LIST_DETAILS_MEDIUM = 1  # Default


# Name desc all args
LIST_DETAILS_HIGH = 2  # -vv


# name desc all args + defaults
LIST_DETAILS_ULTRA = 3  # -vvv

COLOR_NONE = ""
COLOR_DARK_GRAY = "\033[90m"
COLOR_WHITE = "\033[97m"
COLOR_YELLOW = "\033[93m"
COLOR_GREEN = "\033[92m"
COLOR_END = "\033[0m"
COLOR_UNDERLINE = "\033[4m"


@dataclasses.dataclass
class Colors:
    """Colors used for rendering the task list."""

    none: str = COLOR_NONE
    dark_gray: str = COLOR_DARK_GRAY
    white: str = COLOR_WHITE
    yellow: str = COLOR_YELLOW
    green: str = COLOR_GREEN
    pink: str = "\033[95m"
    end: str = COLOR_END
    blue: str = "\033[94m"
    red: str = "\033[91m"
    underline: str = COLOR_UNDERLINE


colors = Colors()


ENABLE_COLORS = sys.stdout.isatty()
if not ENABLE_COLORS:
    for key, _ in colors.__dict__.items():
        if key.startswith("__"):
            continue
        setattr(colors, key, "")


@dataclasses.dataclass
class Config:
    """The main runtime config of the library."""

    # The order of groups of tasks when list
    # All tasks are by default in the "default" group unless task(group="foo") is used
    # Any group not listed here will be shown last, in the order they were defined.
    group_order: list[str] = dataclasses.field(default_factory=lambda: ["default"])

    render_color_mandatory_arg: str = colors.yellow
    render_color_optional_arg: str = colors.dark_gray
    render_color_default_arg = colors.dark_gray + colors.underline
    render_color_task_name: str = colors.green
    render_color_summary: str = colors.white
    render_color_namespace: str = colors.none
    render_color_group_name: str = colors.white
    render_extra_line_indent: str = "    "

    render_task_name: str = "{white}* {green}{name}{clear_format}"

    # Always show these args in the task list, even if they are optional
    render_always_show_args: list[str] = dataclasses.field(default_factory=list)

    # Use to hide rarely used params,or params with long, names from the task list to reduce the noise
    # Hidden params still show up in the tab completion.

    # TODO hightlight soome arguments in special color
    render_highligh_params: dict[str, str] = dataclasses.field(default_factory=dict)

    render_hide_optional_args: list[str] = dataclasses.field(default_factory=list)

    render_format_of_important_tasks: str = "{pink}{name}{clear_format}"

    # Prefix with "\n" to separate group names with a newline
    # use {NAME} instead of {name} to print group name in uppercase
    render_format_of_group_name: str = "\n{white}{underline}{white}*** {name}{clear_format}"

    # The left column (with task name and args) will pref
    # Only rows with very long task names will be longer than this.
    # If your task have many manadatory arguments, you may want to increase
    # this to vertically align the summaries of tasks.
    render_max_left_column_width: int = 30

    # any tasks with more rendered params then this will be split into multiple lines
    render_max_params_per_line: int = 5

    # The left column will never be smaller than this, even with short task names
    # Increaase it if you prefer your summaries to be more to the right.
    render_min_left_column_width: int = 20

    # The column with the task name will never be shorter than this
    # Increasing this will the start of arg listing to the right.
    render_min_task_name: int = 10

    # The amount of info to show by default when running task list
    render_default_list_details: int = LIST_DETAILS_MEDIUM
    render_colors = "auto"  # "auto", "always", or "never"

    # Default args longer than this will be truncated

    render_max_default_arg_width: int = 20

    # -1 for full terminal width
    render_group_header_len: int = 40

    sort = "alpha"  # "alpha"  "definition"

    # If true, tasks marked as important will be shown first.
    # If false, marking task as important will not impact its position in the list
    sort_important_first: bool = True

    #####################################################################
    # Advanced config options

    # if true, @task function prefixed with "_" will be marked as hidden
    adv_hide_private_tasks: bool = True
    show_hidden_tasks: bool = False

    adv_render_separator_line_char: str = "="

    # Python string format for the separator line
    # justify name center
    adv_render_separator_line_title: str = "{underline}{white}*** {underline}{name}{clear_format}"


config = Config()


def get_end_color() -> str:
    """Return the escape code to reset the terminal color."""
    if ENABLE_COLORS:
        return colors.end
    return ""


def get_underline() -> str:
    """Return the escape code to underline the text."""
    if ENABLE_COLORS:
        return COLOR_UNDERLINE
    return ""
