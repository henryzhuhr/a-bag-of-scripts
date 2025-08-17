from abc import ABC, abstractmethod
from typing import Any, Optional

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

    def confirm(self, max_confirm_cnt=5) -> bool:
        confirm_cnt = 0
        incorrect_input_str: Optional[str] = None
        while True:
            confirm_cnt += 1
            if confirm_cnt > max_confirm_cnt:
                print("错误执行次数过多，已取消执行")
                return False
            tip_info = (
                str(
                    f'未知输入 "{incorrect_input_str}" '
                    if incorrect_input_str
                    else "是否执行以上操作"
                )
                + "，确认执行输入(yes/y)，取消输入(no/n):"
            )
            confirm = input(tip_info).lower()

            if confirm.lower() in ["yes", "y"]:
                return True
            elif confirm.lower() in ["no", "n"]:
                print("已取消执行")
                return False
            else:
                incorrect_input_str = confirm
            continue
