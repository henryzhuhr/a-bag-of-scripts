import typing
from abc import ABC, abstractmethod


class Task(ABC):
    """定义任务"""

    pass

    @abstractmethod
    def description(self) -> str:
        """任务描述，用于展示给用户"""
        pass

    @abstractmethod
    def generate(self) -> str:
        """生成执行任务"""
        pass

    @abstractmethod
    def execute(self, dry_run=True) -> None:
        """执行任务，dry_run 为 True 时不真实执行"""
        pass


class TaskManager:
    pass

    def __init__(self):
        self.tasks: typing.List[Task] = []

    def add_task(self, task: Task):
        self.tasks.append(task)

    def show_tasks(self):
        print("\n📋 待执行任务列表:")
        for i, task in enumerate(self.tasks):
            print(f"{i + 1}. {task.description()}")

    def confirm_and_execute(self, dry_run=True):
        if not self.tasks:
            print("没有待执行的任务")
            return

        self.show_tasks()

        confirm = input("\n是否确认执行以上任务？(yes/no): ").lower()
        if confirm in ["yes", "y"]:
            for task in self.tasks:
                task.execute(dry_run=dry_run)
            print("✅ 所有任务已完成")
        else:
            print("❌ 已取消执行")
