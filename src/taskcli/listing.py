import inspect
from typing import Any

import taskcli

from . import configuration, utils
from .configuration import config
from .group import Group
from .task import Task
from .utils import param_to_cli_option

ORDER_TYPE_DEFINITION = "definition"
ORDER_TYPE_ALPHA = "alpha"
ORDER_TYPE_DEFAULT = ORDER_TYPE_ALPHA

ENDC = configuration.get_end_color()


class SafeFormatDict(dict[str, str]):
    """Makes placeholders in a string optional.

    e.g. "Hello {name}" will be rendered as "Hello {name}" if name is not in the dict.
    """

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"  # Return the key as is


def format_colors(template: str, **kwargs: Any) -> str:
    """Apply colors to a template string of e.g. '{red}foobar{pink}bar."""
    if "name" in kwargs:
        kwargs["NAME"] = kwargs["name"].upper()

    format = SafeFormatDict(clear=configuration.colors.end, **kwargs)
    colors = {color: value for color, value in configuration.colors.__dict__.items() if isinstance(value, str)}
    format.update(colors)
    return template.format(**format)


def _sort_tasks(tasks: list[Task], sort: str, sort_important_first: bool) -> list[Task]:
    presorted = []
    if sort == ORDER_TYPE_ALPHA:
        presorted = sorted(tasks, key=lambda task: task.name)
    else:
        # dont's sort
        presorted = tasks

    if sort_important_first:
        # Bubble the important ones to the top
        tasks = []
        for task in presorted:
            if task.important:
                tasks.append(task)
        for task in presorted:
            if not task.important:
                tasks.append(task)

    return tasks


def list_tasks(tasks: list[Task], verbose: int, env_verbose: int = 0) -> list[str]:
    """Return a list of lines to be printed to the console."""
    assert len(tasks) > 0, "No tasks found"

    show_hidden_groups = verbose >= 3 or configuration.config.show_hidden_groups

    # TODO: extract groups info
    groups = create_groups(tasks=tasks, group_order=configuration.config.group_order)

    # first, prepare rows, row can how more than one line
    lines: list[str] = []

    num_visible_groups = len([group.name for group in groups if group.name not in taskcli.get_runtime().hidden_groups])

    for group in groups:
        GROUP_IS_HIDDEN = group.hidden or group.name in taskcli.get_runtime().hidden_groups

        if not show_hidden_groups and GROUP_IS_HIDDEN:
            continue

        if num_visible_groups > 1:
            num_tasks = group.render_num_shown_hidden_tasks()
            group_name_rendered = format_colors(
                config.render_format_of_group_name, name=group.name, desc=group.desc, num_tasks=num_tasks
            )
            lines += [group_name_rendered]

        tasks = _sort_tasks(group.tasks, sort=config.sort, sort_important_first=config.sort_important_first)

        show_hidden_tasks = verbose >= 3 or configuration.config.show_hidden_tasks
        for task in tasks:
            if task.is_hidden() and not show_hidden_tasks:
                continue
            lines.extend(smart_task_lines(task, verbose=verbose, env_verbose=env_verbose))
    lines = [line.rstrip() for line in lines]

    FIRST_LINE_STARTS_WITH_NEW_LINE = lines and lines[0] and lines[0][0] == "\n"
    if FIRST_LINE_STARTS_WITH_NEW_LINE:
        # This can happen if user prefixes the custom group format with a "\n" to separate groups with whitesapce
        lines[0] = lines[0][1:]

    return lines


def smart_task_lines(task: Task, verbose: int, env_verbose: int = 0) -> list[str]:
    """Render a single task into a list of lines, scale formatting to the amount of content."""
    lines: list[str] = []

    name = task.name
    name = format_colors(task.name_format, name=name)

    param_line_prefix = "  "
    summary = task.get_summary_line()
    aliases = ", ".join(task.aliases)
    aliases_color = configuration.colors.pink
    clear = configuration.colors.end
    if aliases:
        summary = f"{aliases_color}({aliases}){clear} " + summary

    max_left = taskcli.config.render_max_left_column_width
    if not summary:
        max_left_if_no_summary = 130
        max_left = max_left_if_no_summary

    format = config.render_task_name
    if task.important:
        format = config.render_format_important_tasks
    if task.hidden:
        format = config.render_format_hidden_tasks
    if not task.is_ready():
        format = config.render_format_not_ready

    # if task.group.name != "default":
    #     name = configuration.colors.dark_gray + task.group.name + configuration.colors.end + "." + name

    line = format_colors(format, name=name)

    include_optional = verbose >= 2
    include_defaults = verbose >= 3

    one_line_params = build_pretty_param_string(
        task, include_optional=include_optional, include_defaults=include_defaults
    )

    not_ready_lines = []
    # Check if env is ok
    if not task.is_ready():
        if env_verbose == 0:
            not_ready_reason = task.get_not_ready_reason_short()
            one_line_params += f" {configuration.colors.red}{not_ready_reason}{configuration.colors.end}"
        else:
            not_ready_lines = task.get_not_ready_reason_long()
            not_ready_lines = [
                f"{param_line_prefix}{configuration.colors.red}{line}{configuration.colors.end}"
                for line in not_ready_lines
            ]

    potential_line = line + " " + one_line_params
    if len(utils.strip_escape_codes(potential_line)) < max_left:
        line = potential_line
        one_line_params = ""  # clear, to avoid adding it again later

    min_left = taskcli.config.render_min_left_column_width
    line_len = len(utils.strip_escape_codes(line))
    if line_len < min_left:  # add padding before the summary
        line += " " * (min_left - line_len)

    line += summary
    lines.append(line)

    if one_line_params:
        num_params = len(
            build_pretty_param_list(task, include_optional=include_optional, include_defaults=include_defaults)
        )

        if len(utils.strip_escape_codes(one_line_params)) > 80 or num_params > config.render_max_params_per_line:
            param_list = build_pretty_param_list(
                task, include_optional=include_optional, include_defaults=include_defaults
            )
            for param in param_list:
                lines.append(param_line_prefix + param)
        else:
            lines.append(param_line_prefix + one_line_params)

    lines += not_ready_lines
    return lines


def create_groups(tasks: list[Task], group_order: list[str]) -> list[Group]:
    """Return a dict of group_name -> list of tasks, ordered per group_order, group not listed there will be last."""
    groups: list[Group] = []
    remaining_tasks: set[Task] = set()

    for expected_group_name in group_order:
        for task in tasks:
            already_present = task.group in groups

            if task.group.name == expected_group_name and not already_present:
                groups.append(task.group)
            else:
                remaining_tasks.add(task)

    for task in remaining_tasks:
        if task.group not in groups:
            groups.append(task.group)

    before = [group.name for group in groups]
    after = list({group.name for group in groups})
    assert sorted(before) == sorted(after), f"Duplicate groups found, {before} != {after}"
    return groups


def build_pretty_param_string(task: Task, include_optional: bool = True, include_defaults: bool = True) -> str:
    """Return a string with all params, formatted for the console."""
    endc = configuration.get_end_color()
    pretty_params = build_pretty_param_list(task, include_optional=include_optional, include_defaults=include_defaults)
    return f"{config.render_color_summary}, {endc}".join(pretty_params)


def build_pretty_param_list(  # noqa: C901
    task: Task, include_optional: bool = True, include_defaults: bool = True, truncate_long: bool = True
) -> list[str]:
    """Return a list of params, each element a string formatted for the console."""
    end_color = configuration.get_end_color()

    pretty_params = []
    for param in task.params:
        #    if not include_optional and param_has_a_default and (param.name not in config.render_always_show_args):
        if not include_optional and param.has_default() and not param.important:
            # skip args which have a default value specified
            continue

        if param.has_default() and param.name in config.render_hide_optional_args:
            continue
        rendered = param.name

        if param.kind in [inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD]:
            rendered = rendered.upper()
        elif param.kind in [inspect.Parameter.KEYWORD_ONLY]:
            rendered = param_to_cli_option(rendered)

        if not param.has_default():
            rendered = f"{config.render_color_mandatory_arg}{rendered}{end_color}"
        else:
            if param.important:
                rendered = f"{config.render_color_optional_and_important_arg}{rendered}{end_color}"
            else:
                rendered = f"{config.render_color_optional_arg}{rendered}{end_color}"

        if param.kind in [inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD]:
            rendered = rendered

        elif param.kind in [inspect.Parameter.KEYWORD_ONLY]:
            rendered = param_to_cli_option(param.name)
        elif param.kind in [inspect.Parameter.VAR_POSITIONAL]:
            rendered = f"*{param.name}"
        elif param.kind in [inspect.Parameter.VAR_KEYWORD]:
            rendered = f"**{param.name}"
        else:
            msg = f"Unknown parameter kind: {param.kind}"
            raise Exception(msg)

        if include_defaults and not param.type == bool:
            if param.has_default():
                # Shorten default value
                default_value: Any = param.default
                if truncate_long:
                    if len(str(default_value)) > config.render_max_default_arg_width:
                        default_value = str(default_value)[: config.render_max_default_arg_width] + "..."

                rendered += (
                    f"{config.render_color_optional_arg}={end_color}"
                    f"{config.render_color_default_arg}{default_value}{end_color}"
                )
            else:
                rendered += ""
        pretty_params.append(rendered)

    return pretty_params
