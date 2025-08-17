from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class BaseTaskConfig(BaseModel):
    """
    通用任务配置基础类，所有任务配置应继承自此类。
    """

    name: str = Field(
        default="BaseTaskConfig",
        description="任务配置名称",
    )


class BaseTask(ABC):
    """
    通用任务基础类，定义任务的基本接口。
    """

    def __init__(self, config: BaseTaskConfig):
        self.config = config

    @abstractmethod
    def name(self) -> str:
        """
        返回任务名称
        """
        pass

    @abstractmethod
    def describe(self) -> str:
        """
        返回任务的描述信息
        """
        pass

    @abstractmethod
    def execute(self, dry_run: bool = False) -> Any:
        """
        执行任务。
        :param dry_run: 不实际执行
        :return: 执行结果
        """
        pass
