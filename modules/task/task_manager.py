from typing import Any, Dict, Optional, Type

from loguru import logger

from .task import BaseTask


class TaskManager:
    """
    任务管理器：用于注册、管理和执行任务。
    """

    def __init__(self):
        self._tasks: Dict[str, BaseTask] = {}
        self._task_types: Dict[str, Type[BaseTask]] = {}

    def register_task_type(self, name: str, task_cls: Type[BaseTask]):
        """
        注册任务类型。
        :param name: 任务类型名称
        :param task_cls: 任务类
        """
        self._task_types[name] = task_cls

    def create_task(
        self, name: str, config: Optional[Dict[str, Any]] = None
    ) -> BaseTask:
        """
        根据类型创建任务实例并注册。
        :param name: 任务类型名称
        :param config: 任务配置
        :return: 任务实例
        """
        if name not in self._task_types:
            raise ValueError(f"未注册的任务类型: {name}")
        task = self._task_types[name](config)
        self._tasks[name] = task
        return task

    def get_task(self, name: str) -> Optional[BaseTask]:
        """
        获取已注册的任务实例。
        :param name: 任务名称
        :return: 任务实例或None
        """
        return self._tasks.get(name)

    def describe_task(self, name: str) -> str:
        """
        获取任务描述。
        :param name: 任务名称
        :return: 描述字符串
        """
        task = self.get_task(name)
        if not task:
            return f"任务 '{name}' 未注册。"
        return task.describe()

    def execute_task(self, name: str, dry_run: bool = False) -> Any:
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
