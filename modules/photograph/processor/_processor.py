from abc import ABC

from pkg._enums.format import FilenameRule


class BaseProcessor(ABC):
    """处理器基类"""

    def __init__(self):
        """初始化处理器：
        - 设置重命名规则为默认规则。如果需要自定义规则，请调用 `set_rename_rule` 方法。
        """
        self.set_rename_rule()

    def set_rename_rule(self, rule: FilenameRule = FilenameRule.DEFAULT):
        """设置重命名规则"""
        self.rename_rule = rule
