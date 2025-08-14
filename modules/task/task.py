from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseTask(ABC):
    """
    通用任务基础类，定义任务的基本接口。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def generate(self) -> None:
        """
        生成任务所需的资源或准备工作。
        """
        pass

    @abstractmethod
    def describe(self) -> str:
        """
        返回任务的描述信息。
        """
        pass

    @abstractmethod
    def execute(self, dry_run: bool = False) -> Any:
        """
        执行任务。
        :param dry_run: 模拟执行（不产生实际效果）
        :return: 执行结果
        """
        pass
