"""Various functions that operate on Tasks."""
from dataclasses import dataclass
from .taskrendersettings import TaskRenderSettings


from .task import Task


@dataclass
class FilterResult:
    """Result of filtering tasks."""
    tasks: list[Task]
    progress: list[str]



def filter_before_listing(tasks:list[Task], settings:TaskRenderSettings) -> FilterResult:
    """Filter tasks before listing them."""
    progress = []
    progress += [f"Before filtering: {len(tasks)}."]

    if settings.tags:
        filtered_tasks = filter_tasks_by_tags(tasks, tags=settings.tags)
        if not filtered_tasks:
            progress += [f"No tasks after filtering by tag ({settings.tags})"]
            return FilterResult(tasks=[], progress=progress)

        progress += [f"After filtering by tag ({settings.tags}): {len(filtered_tasks)}."]
    else:
        filtered_tasks = tasks

    if settings.search:
        search_filtered_tasks = search_for_tasks(tasks=filtered_tasks, search=settings.search)
        if not search_filtered_tasks:
            progress += [f"No tasks after filtering by regex search ({settings.search})"]
            return FilterResult(tasks=[], progress=progress)
        progress += [f"After filtering by regex search ({settings.search}): {len(search_filtered_tasks)}."]
    else:
        search_filtered_tasks = filtered_tasks

    progress += [f"Final number of tasks: {len(search_filtered_tasks)}."]
    return FilterResult(tasks=search_filtered_tasks, progress=progress)

def filter_tasks_by_tags(tasks: list[Task], tags: list[str]) -> list[Task]:
    """Return only tasks which have any of the tags."""
    if not tags:
        return tasks

    filtered = []
    for task in tasks:
        if task.tags:
            for tag in task.tags:
                if tag in tags:
                    filtered.append(task)
                    break
    return filtered

from taskcli.task import UserError
def search_for_tasks(tasks: list[Task], search: str) -> list[Task]:
    """Search for tasks by regex."""
    import re
    try:
        regex = re.compile(search)
    except re.error as e:
        raise UserError(f"Invalid Python regex: {search}") from e

    out:list[Task] = []
    for task in tasks:
        if regex.search(task.name):
            out.append(task)
        elif regex.search(task.get_summary_line()):
            out.append(task)

    return out