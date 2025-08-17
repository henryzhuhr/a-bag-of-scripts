from abc import ABC, abstractmethod
from typing import Any, List


class BaseTask(ABC):
    """任务基类"""

    _ready: bool
    """任务是否准备就绪的标志"""

    def __init__(self):
        self._ready = False  # 初始化时任务未准备就绪

    @classmethod
    @abstractmethod
    def must_match(cls, obj: Any) -> None:
        """
        判断输入对象是否匹配当前任务类型
        如果不符合，必须抛出异常（如 ValueError）。

        Args:
            obj (Any): 待检查的对象
        Raises:
            Exception: 输入对象不符合要求抛出异常
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def description(self, dry_run: bool = True) -> str:
        """
        返回任务描述

        Args:
            dry_run(bool): 模拟执行的时候，输出对应的描述信息
        Returns:
            str: 任务描述信息
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def create(self) -> None:
        """创建任务，子类需要实现此方法，且需要调用 must_match 方法来检查输入对象是否符合要求。"""
        try:
            self.must_match(obj=self)
        except Exception as e:
            raise Exception(f"Object does not match task requirements: {e}")

        self._ready = True

        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def execute(self, dry_run: bool = True) -> None:
        """
        执行当前任务

        Args:
            dry_run(bool): 是否为模拟执行
        """
        raise NotImplementedError("Subclasses must implement this method")


class TaskManager:
    """任务管理器，用于注册和管理处理器任务"""

    task_list: List[BaseTask]
    """任务列表，存储所有注册的处理器"""

    def __init__(self):
        self.task_list = []

    def add_task(self, task: BaseTask) -> None:
        """添加任务到列表"""
        self.task_list.append(task)

    def execute_all(self, dry_run: bool = True) -> None:
        """执行所有任务"""
        for task in self.task_list:
            print(f"执行任务: {task.description()}")
            task.execute(dry_run)
