# Repository Guidelines

## 项目结构与模块组织

本仓库是一个 Python 脚本集合，包含可复用任务模块和可直接运行的工具脚本。`modules/` 存放可导入代码：`modules/task/` 是通用任务框架，`modules/photograph/` 包含照片元数据、处理器和重命名任务。`tools/` 存放面向手动执行的入口，例如 `tools/photograph/rename-raw-photo.py`。`scripts/` 存放独立或历史脚本，包括 `scripts/opencv/` 下的 OpenCV 辅助脚本。`utils/` 存放共享工具，`test/` 存放 pytest 测试，`docs/` 存放设计说明。

## 构建、测试与开发命令

- `uv sync` 根据 `pyproject.toml` 和 `uv.lock` 安装固定依赖环境。
- `uv run pytest` 运行完整测试套件。
- `uv run pytest test/photograph/test_rename_raw_photo_task.py` 只运行照片重命名任务测试。
- `uv run python scripts/main.py` 运行简单脚本入口。
- `uv run python tools/photograph/rename-raw-photo.py` 在配置 `FILE_TAG_LIST` 后运行 RAW 照片重命名工具。

仓库没有单独的构建步骤。提交前应通过测试和有针对性的脚本 dry run 验证变更。

## 代码风格与命名约定

使用兼容 Python 3.10 的语法。遵循现有风格：4 空格缩进，函数和变量使用 `snake_case`，类使用 `PascalCase`，任务配置和公开任务方法应提供明确类型标注。可导入逻辑放在 `modules/`，命令式编排放在 `tools/` 或 `scripts/`。已有模块使用 `loguru` 的地方继续保持一致。扩展现有中文注释或中文文件名时应保留其语境；新增可复用模块默认使用清晰的英文 `snake_case` 名称，除非本地化脚本名更合适。

## 测试指南

测试框架为 `pytest`。测试文件命名为 `test_*.py`，并放在 `test/` 下对应领域目录中，例如 `test/photograph/test_rename_raw_photo_task.py`。优先 mock 文件系统、EXIF 和外部库行为，不依赖真实照片资产。涉及移动或重命名文件的工具，应覆盖 `dry_run=True` 和基于临时目录的实际执行。

## 提交与 Pull Request 指南

近期提交采用 emoji 加 Conventional Commit 的格式，通常包含 scope，例如 `🐛 fix(photo): ...`、`✨ feat(photo): ...`、`🏗️ refactor(task): ...` 和 `🔀 merge: ...`。提交标题应简洁，并说明受影响模块。

Pull Request 应包含变更摘要、受影响脚本或模块、已运行的测试命令，以及必要的手动验证信息，例如重命名工具的 dry-run 输出。如有关联 issue，应一并链接。涉及破坏性文件操作时，必须说明安全保护和默认行为。

## 安全与配置提示

不要提交个人照片路径、凭据或机器专属配置。除非是安全的测试夹具，否则示例 `FILE_TAG_LIST` 应保持注释状态。开发会重命名、移动或删除文件的脚本时，默认先使用 dry run。
