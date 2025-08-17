from typing import Any, Dict, Optional, Type

from loguru import logger

from .task import BaseTask


class TaskManager:
    """
    任务管理器：用于注册、管理和执行任务。
    """

    _tasks: Dict[str, BaseTask]
    """已注册的任务实例字典"""

    def __init__(self):
        self._tasks = {}
        self._task_types: Dict[str, Type[BaseTask]] = {}

    @property
    def tasks(self) -> Dict[str, BaseTask]:
        """
        获取已注册的任务实例字典。
        :return: 任务实例字典
        """
        return self._tasks

    def register_task(self, task: BaseTask):
        """
        注册任务
        """
        if not isinstance(task, BaseTask):
            raise TypeError(
                f"task must be an instance of BaseTask, but got: {type(task).__name__}"
            )
        self._tasks[task.name()] = task

    def get_task(self, name: str) -> Optional[BaseTask]:
        """
        获取已注册的任务实例。
        :param name: 任务名称
        :return: 任务实例或None
        """
        return self._tasks.get(name)

    def execute(self, name: str, dry_run: bool = False) -> Any:
        """
        执行指定任务。
        :param name: 任务名称
        :param dry_run: 是否为干运行（不实际执行）
        :return: 执行结果
        """
        task = self.get_task(name)
        logger.debug(f"Executing task '{name}' with dry_run={dry_run}")
        if not task:
            raise ValueError(f"任务 '{name}' 未注册。")
        return task.execute(dry_run=dry_run)

    def list_tasks(self) -> Dict[str, BaseTask]:
        """
        列出所有已注册任务。
        :return: 任务字典
        """
        return self._tasks.copy()
