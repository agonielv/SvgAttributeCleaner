from __future__ import annotations

import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from .cleaner import clean_svg_attributes, clean_svg_folder
from .report import write_report
from .utils import default_output_path, open_path, parse_attributes


class SvgAttributeCleanerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Svg Attribute Cleaner")
        self.geometry("820x650")
        self.mode_var = tk.StringVar(value="file")
        self.input_file_var = tk.StringVar()
        self.input_dir_var = tk.StringVar()
        self.output_file_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=False)
        self.preserve_var = tk.BooleanVar(value=False)
        self.zip_var = tk.BooleanVar(value=False)
        self.last_output_dir: Path | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 5}
        mode = ttk.LabelFrame(self, text="处理模式")
        mode.pack(fill="x", **pad)
        ttk.Radiobutton(mode, text="单文件模式", variable=self.mode_var, value="file", command=self._refresh_defaults).pack(side="left", padx=8)
        ttk.Radiobutton(mode, text="文件夹批量模式", variable=self.mode_var, value="folder", command=self._refresh_defaults).pack(side="left", padx=8)
        ttk.Checkbutton(mode, text="包含子文件夹", variable=self.recursive_var).pack(side="left", padx=8)
        ttk.Checkbutton(mode, text="尽量保留原始格式", variable=self.preserve_var).pack(side="left", padx=8)
        ttk.Checkbutton(mode, text="批量输出 zip", variable=self.zip_var).pack(side="left", padx=8)

        source = ttk.LabelFrame(self, text="输入")
        source.pack(fill="x", **pad)
        ttk.Button(source, text="选择 SVG 文件", command=self.choose_file).grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(source, textvariable=self.input_file_var).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(source, text="选择文件夹", command=self.choose_dir).grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(source, textvariable=self.input_dir_var).grid(row=1, column=1, sticky="ew", **pad)
        source.columnconfigure(1, weight=1)

        attrs = ttk.LabelFrame(self, text="要删除的属性名（一行一个，或用英文逗号/空格分隔）")
        attrs.pack(fill="x", **pad)
        self.attrs_text = tk.Text(attrs, height=5)
        self.attrs_text.pack(fill="x", **pad)
        self.attrs_text.insert("1.0", "data-name")

        output = ttk.LabelFrame(self, text="输出")
        output.pack(fill="x", **pad)
        ttk.Button(output, text="选择输出文件", command=self.choose_output_file).grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(output, textvariable=self.output_file_var).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(output, text="选择输出文件夹", command=self.choose_output_dir).grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(output, textvariable=self.output_dir_var).grid(row=1, column=1, sticky="ew", **pad)
        output.columnconfigure(1, weight=1)

        actions = ttk.Frame(self)
        actions.pack(fill="x", **pad)
        ttk.Button(actions, text="预览统计", command=lambda: self.run_processing(True)).pack(side="left", padx=5)
        ttk.Button(actions, text="开始处理", command=lambda: self.run_processing(False)).pack(side="left", padx=5)
        ttk.Button(actions, text="打开输出目录", command=self.open_output_dir).pack(side="left", padx=5)

        log_frame = ttk.LabelFrame(self, text="日志")
        log_frame.pack(fill="both", expand=True, **pad)
        self.log = scrolledtext.ScrolledText(log_frame, height=16)
        self.log.pack(fill="both", expand=True, **pad)

    def log_line(self, text: str) -> None:
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def choose_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("SVG files", "*.svg"), ("All files", "*.*")])
        if path:
            self.mode_var.set("file")
            self.input_file_var.set(path)
            self.output_file_var.set(str(default_output_path(path)))

    def choose_dir(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.mode_var.set("folder")
            self.input_dir_var.set(path)
            self.output_dir_var.set(str(Path(path) / "output_cleaned"))

    def choose_output_file(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".svg", filetypes=[("SVG files", "*.svg")])
        if path:
            self.output_file_var.set(path)

    def choose_output_dir(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_dir_var.set(path)

    def _refresh_defaults(self) -> None:
        if self.mode_var.get() == "file" and self.input_file_var.get() and not self.output_file_var.get():
            self.output_file_var.set(str(default_output_path(self.input_file_var.get())))
        if self.mode_var.get() == "folder" and self.input_dir_var.get() and not self.output_dir_var.get():
            self.output_dir_var.set(str(Path(self.input_dir_var.get()) / "output_cleaned"))

    def run_processing(self, dry_run: bool) -> None:
        threading.Thread(target=self._process, args=(dry_run,), daemon=True).start()

    def _process(self, dry_run: bool) -> None:
        attrs = parse_attributes(self.attrs_text.get("1.0", "end"))
        if not attrs:
            messagebox.showerror("错误", "请输入至少一个属性名")
            return
        self.log_line("开始预览..." if dry_run else "开始处理...")
        if self.mode_var.get() == "file":
            input_path = self.input_file_var.get()
            output_path = self.output_file_var.get() or str(default_output_path(input_path))
            results = [clean_svg_attributes(input_path, output_path, attrs, preserve_format=self.preserve_var.get(), dry_run=dry_run)]
            report_dir = Path(output_path).parent
        else:
            input_dir = self.input_dir_var.get()
            output_dir = self.output_dir_var.get() or str(Path(input_dir) / "output_cleaned")
            results = clean_svg_folder(input_dir, output_dir, attrs, recursive=self.recursive_var.get(), preserve_format=self.preserve_var.get(), dry_run=dry_run)
            report_dir = Path(output_dir)
        report_path = write_report(results, report_dir / "clean_report.json")
        self.last_output_dir = report_dir
        for item in results:
            self.log_line(f"{'成功' if item['success'] else '失败'}: {item['input']} 删除 {item['total_removed']} 个；{item['removed_counts']} {item.get('error') or ''}")
        self.log_line(f"总处理文件数: {len(results)}")
        self.log_line(f"报告: {report_path}")
        if not dry_run:
            messagebox.showinfo("完成", f"处理完成。输出位置：{report_dir}")

    def open_output_dir(self) -> None:
        if self.last_output_dir:
            open_path(self.last_output_dir)
        else:
            messagebox.showinfo("提示", "还没有输出目录")


def main() -> None:
    app = SvgAttributeCleanerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
