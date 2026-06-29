# SvgAttributeCleaner

SvgAttributeCleaner 是一个 Python 3.11 开发的 Windows 图形界面工具，用于从 SVG/XML 文件中删除用户指定的属性及其值。它只删除属性，不删除 `svg`、`path`、`g`、`rect` 等图形元素。

例如输入属性名 `data-name` 后，工具会删除所有 `data-name="..."` 或 `data-name='...'`，并保留未指定删除的 `viewBox`、`id`、`class`、`style`、`d` 等属性。

## 功能

- Tkinter GUI，适合 PyInstaller 打包为单文件 exe。
- 单个 SVG 文件处理。
- 文件夹批量处理，可选递归子文件夹。
- 支持一行一个、英文逗号、空格分隔的多个属性名。
- 支持命名空间属性，例如 `inkscape:label`、`sodipodi:nodetypes`。
- 默认输出新文件，不覆盖原文件，单文件默认命名为 `原文件名_cleaned.svg`。
- 每次运行生成 `clean_report.json` JSON 报告。
- 支持 CLI 和 dry-run 预览统计。
- 可选“尽量保留原始格式”模式，使用谨慎正则删除属性字符串。

## GUI 使用方式

### 启动 GUI

开发环境中运行：

```bash
python svg_attribute_cleaner.py
```

或显式运行：

```bash
python svg_attribute_cleaner.py --gui
```

Windows 用户也可以双击：

```bat
scripts\run_gui.bat
```

### 单文件处理流程

1. 选择“单文件模式”。
2. 点击“选择 SVG 文件”，选择一个 `.svg` 文件。
3. 输出文件会默认设为同目录下的 `原文件名_cleaned.svg`。
4. 如需修改输出位置，点击“选择输出文件”。
5. 在属性输入框输入要删除的属性名。
6. 点击“预览统计”查看将删除的数量，或点击“开始处理”生成新 SVG。
7. 处理完成后，点击“打开输出目录”查看结果。

### 文件夹批量处理流程

1. 选择“文件夹批量模式”。
2. 点击“选择文件夹”。
3. 默认输出到该文件夹下的 `output_cleaned`。
4. 如需包含子文件夹，勾选“包含子文件夹”。
5. 输入属性名后点击“开始处理”。
6. 每个输出文件默认命名为 `原文件名_cleaned.svg`。

### 如何输入属性名

支持以下输入形式：

```text
data-name
inkscape:label
sodipodi:nodetypes
```

也支持英文逗号或空格：

```text
data-name, id, class
```

删除 `data-name` 时，只会精确删除 `data-name`，不会删除 `data-id`、`name` 或 `data-name-extra`。

## 日志和 JSON 报告

GUI 底部日志区域会显示：

- 每个文件的处理状态。
- 每个文件删除了多少个属性。
- 每个属性的删除数量。
- 总处理文件数。
- 失败文件和错误原因。

每次处理完成都会生成 `clean_report.json`，包含输入文件路径、输出文件路径、删除属性列表、每个属性删除数量、总删除数量、处理时间、成功/失败状态和错误信息。

## CLI 使用示例

单文件：

```bash
python svg_attribute_cleaner.py --input input.svg --output output.svg --attrs data-name
```

多个属性：

```bash
python svg_attribute_cleaner.py --input input.svg --output output.svg --attrs data-name,id,class
```

文件夹批量：

```bash
python svg_attribute_cleaner.py --input-dir svgs --output-dir output_cleaned --attrs data-name --recursive
```

预览模式，只统计不生成 SVG：

```bash
python svg_attribute_cleaner.py --input input.svg --attrs data-name --dry-run
```

尽量保留原始格式：

```bash
python svg_attribute_cleaner.py --input input.svg --output output.svg --attrs data-name --preserve-format
```

## Windows 打包 exe

在 Windows 项目根目录执行：

```bat
scripts\build_windows.bat
```

脚本会自动：

1. 创建 `.venv` 虚拟环境。
2. 安装 `requirements.txt`、`pytest`、`pyinstaller`。
3. 运行测试：`python -m pytest`。
4. 运行编译检查：`python -m compileall svg_attribute_cleaner svg_attribute_cleaner.py`。
5. 使用 PyInstaller 打包 GUI 入口。
6. 生成 `dist\SvgAttributeCleaner.exe`。
7. 生成 `release\SvgAttributeCleaner-windows-x64.zip`。

打包命令使用：

```bat
pyinstaller --onefile --windowed --name SvgAttributeCleaner --add-data "configs;configs" svg_attribute_cleaner.py
```

## 分发给其他电脑

把 `release\SvgAttributeCleaner-windows-x64.zip` 发给目标电脑，解压后双击 `SvgAttributeCleaner.exe` 即可运行。目标电脑不需要安装 Python。

## GitHub Actions

仓库包含 `.github/workflows/build-windows.yml`，会在 Windows runner 上安装 Python 3.11、运行测试、执行 compileall、使用 PyInstaller 打包，并上传 `SvgAttributeCleaner-windows-x64.zip` artifact。

## 已知限制

- XML 解析模式可能会改变 SVG 文件格式排版。
- “尽量保留原始格式”模式更接近原文件，但复杂 SVG 中仍需备份原文件。
- 不建议直接覆盖原文件；默认行为会生成新文件。
