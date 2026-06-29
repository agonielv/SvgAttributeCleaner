from __future__ import annotations

import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from .cleaner import clean_svg_attributes, clean_svg_folder
from .report import write_report
from .utils import default_output_path, open_path, parse_attributes


class SvgAttributeCleanerApp(tk.Tk):
    """Modern Tkinter desktop UI for SVG attribute cleanup."""

    BG = "#f6f8fc"
    CARD = "#ffffff"
    CARD_SOFT = "#eef4ff"
    TEXT = "#172033"
    MUTED = "#667085"
    PRIMARY = "#2563eb"
    PRIMARY_DARK = "#1d4ed8"
    SUCCESS = "#059669"
    BORDER = "#dbe3ef"

    def __init__(self) -> None:
        super().__init__()
        self.title("Svg Attribute Cleaner")
        self.geometry("980x720")
        self.minsize(900, 640)
        self.configure(bg=self.BG)
        self.mode_var = tk.StringVar(value="file")
        self.input_file_var = tk.StringVar()
        self.input_dir_var = tk.StringVar()
        self.output_file_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=False)
        self.preserve_var = tk.BooleanVar(value=False)
        self.last_output_dir: Path | None = None
        self.status_var = tk.StringVar(value="准备就绪")
        self.summary_var = tk.StringVar(value="选择 SVG 文件或文件夹，然后输入要删除的属性名。")
        self._configure_style()
        self._build_ui()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("App.TFrame", background=self.BG)
        style.configure("Card.TFrame", background=self.CARD, relief="flat")
        style.configure("Soft.TFrame", background=self.CARD_SOFT)
        style.configure("Title.TLabel", background=self.BG, foreground=self.TEXT, font=("Segoe UI", 24, "bold"))
        style.configure("Subtitle.TLabel", background=self.BG, foreground=self.MUTED, font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=self.CARD, foreground=self.TEXT, font=("Segoe UI", 12, "bold"))
        style.configure("Hint.TLabel", background=self.CARD, foreground=self.MUTED, font=("Segoe UI", 9))
        style.configure("Status.TLabel", background=self.CARD_SOFT, foreground=self.PRIMARY_DARK, font=("Segoe UI", 10, "bold"))
        style.configure("Path.TEntry", fieldbackground="#f8fafc", bordercolor=self.BORDER, lightcolor=self.BORDER, darkcolor=self.BORDER, padding=8)
        style.configure("Modern.TRadiobutton", background=self.CARD, foreground=self.TEXT, font=("Segoe UI", 10))
        style.configure("Modern.TCheckbutton", background=self.CARD, foreground=self.TEXT, font=("Segoe UI", 10))
        style.configure("Primary.TButton", background=self.PRIMARY, foreground="#ffffff", borderwidth=0, focusthickness=0, padding=(18, 10), font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", self.PRIMARY_DARK), ("pressed", self.PRIMARY_DARK)], foreground=[("disabled", "#d0d5dd")])
        style.configure("Secondary.TButton", background="#eaf1ff", foreground=self.PRIMARY_DARK, borderwidth=0, padding=(14, 9), font=("Segoe UI", 10, "bold"))
        style.map("Secondary.TButton", background=[("active", "#d8e6ff"), ("pressed", "#d8e6ff")])
        style.configure("Ghost.TButton", background=self.CARD, foreground=self.TEXT, bordercolor=self.BORDER, padding=(12, 8), font=("Segoe UI", 10))
        style.configure("Accent.Horizontal.TProgressbar", troughcolor="#e5e7eb", background=self.PRIMARY, bordercolor="#e5e7eb", lightcolor=self.PRIMARY, darkcolor=self.PRIMARY)

    def _card(self, parent: tk.Widget, title: str, hint: str | None = None) -> ttk.Frame:
        outer = tk.Frame(parent, bg=self.CARD, highlightbackground=self.BORDER, highlightthickness=1, bd=0)
        outer.pack(fill="x", pady=8)
        frame = ttk.Frame(outer, style="Card.TFrame", padding=(18, 14))
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=title, style="CardTitle.TLabel").pack(anchor="w")
        if hint:
            ttk.Label(frame, text=hint, style="Hint.TLabel").pack(anchor="w", pady=(2, 10))
        body = ttk.Frame(frame, style="Card.TFrame")
        body.pack(fill="both", expand=True)
        return body

    def _build_ui(self) -> None:
        root = ttk.Frame(self, style="App.TFrame", padding=(24, 20))
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root, style="App.TFrame")
        header.pack(fill="x", pady=(0, 10))
        title_block = ttk.Frame(header, style="App.TFrame")
        title_block.pack(side="left", fill="x", expand=True)
        ttk.Label(title_block, text="Svg Attribute Cleaner", style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_block, text="安全删除 SVG/XML 指定属性，保留图形结构与未选属性。", style="Subtitle.TLabel").pack(anchor="w", pady=(2, 0))
        status = ttk.Frame(header, style="Soft.TFrame", padding=(14, 9))
        status.pack(side="right")
        ttk.Label(status, textvariable=self.status_var, style="Status.TLabel").pack()

        mode_card = self._card(root, "1. 选择处理模式", "单文件适合快速处理；文件夹模式可批量处理 .svg 文件。")
        mode_grid = ttk.Frame(mode_card, style="Card.TFrame")
        mode_grid.pack(fill="x")
        ttk.Radiobutton(mode_grid, text="单文件模式", variable=self.mode_var, value="file", style="Modern.TRadiobutton", command=self._refresh_defaults).grid(row=0, column=0, sticky="w", padx=(0, 20), pady=2)
        ttk.Radiobutton(mode_grid, text="文件夹批量模式", variable=self.mode_var, value="folder", style="Modern.TRadiobutton", command=self._refresh_defaults).grid(row=0, column=1, sticky="w", padx=(0, 20), pady=2)
        ttk.Checkbutton(mode_grid, text="包含子文件夹", variable=self.recursive_var, style="Modern.TCheckbutton").grid(row=0, column=2, sticky="w", padx=(0, 20), pady=2)
        ttk.Checkbutton(mode_grid, text="尽量保留原始格式", variable=self.preserve_var, style="Modern.TCheckbutton").grid(row=0, column=3, sticky="w", padx=(0, 20), pady=2)

        source = self._card(root, "2. 选择输入与输出", "默认不覆盖原文件；单文件输出为 *_cleaned.svg，批量输出到 output_cleaned。")
        source.columnconfigure(1, weight=1)
        ttk.Button(source, text="选择 SVG 文件", style="Secondary.TButton", command=self.choose_file).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        ttk.Entry(source, textvariable=self.input_file_var, style="Path.TEntry").grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Button(source, text="输出文件", style="Ghost.TButton", command=self.choose_output_file).grid(row=0, column=2, sticky="e", padx=(10, 0), pady=5)
        ttk.Entry(source, textvariable=self.output_file_var, style="Path.TEntry").grid(row=0, column=3, sticky="ew", padx=(10, 0), pady=5)
        ttk.Button(source, text="选择文件夹", style="Secondary.TButton", command=self.choose_dir).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=5)
        ttk.Entry(source, textvariable=self.input_dir_var, style="Path.TEntry").grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Button(source, text="输出文件夹", style="Ghost.TButton", command=self.choose_output_dir).grid(row=1, column=2, sticky="e", padx=(10, 0), pady=5)
        ttk.Entry(source, textvariable=self.output_dir_var, style="Path.TEntry").grid(row=1, column=3, sticky="ew", padx=(10, 0), pady=5)
        source.columnconfigure(3, weight=1)

        attrs = self._card(root, "3. 输入要删除的属性名", "支持一行一个，也支持英文逗号或空格分隔，例如 data-name, inkscape:label。")
        self.attrs_text = tk.Text(
            attrs,
            height=4,
            wrap="word",
            bd=0,
            relief="flat",
            font=("Cascadia Mono", 11),
            bg="#f8fafc",
            fg=self.TEXT,
            insertbackground=self.PRIMARY,
            highlightbackground=self.BORDER,
            highlightcolor=self.PRIMARY,
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        self.attrs_text.pack(fill="x")
        self.attrs_text.insert("1.0", "data-name")

        action_card = tk.Frame(root, bg=self.CARD, highlightbackground=self.BORDER, highlightthickness=1, bd=0)
        action_card.pack(fill="x", pady=8)
        actions = ttk.Frame(action_card, style="Card.TFrame", padding=(18, 14))
        actions.pack(fill="x")
        ttk.Button(actions, text="预览统计", style="Secondary.TButton", command=lambda: self.run_processing(True)).pack(side="left", padx=(0, 10))
        ttk.Button(actions, text="开始处理", style="Primary.TButton", command=lambda: self.run_processing(False)).pack(side="left", padx=(0, 10))
        ttk.Button(actions, text="打开输出目录", style="Ghost.TButton", command=self.open_output_dir).pack(side="left")
        ttk.Label(actions, textvariable=self.summary_var, style="Hint.TLabel").pack(side="right")
        self.progress = ttk.Progressbar(actions, mode="indeterminate", style="Accent.Horizontal.TProgressbar", length=170)
        self.progress.pack(side="right", padx=(0, 16))

        log_card = tk.Frame(root, bg=self.CARD, highlightbackground=self.BORDER, highlightthickness=1, bd=0)
        log_card.pack(fill="both", expand=True, pady=8)
        log_inner = ttk.Frame(log_card, style="Card.TFrame", padding=(18, 14))
        log_inner.pack(fill="both", expand=True)
        ttk.Label(log_inner, text="处理日志", style="CardTitle.TLabel").pack(anchor="w")
        self.log = scrolledtext.ScrolledText(
            log_inner,
            height=10,
            bd=0,
            relief="flat",
            font=("Cascadia Mono", 10),
            bg="#0f172a",
            fg="#dbeafe",
            insertbackground="#93c5fd",
            padx=12,
            pady=10,
        )
        self.log.pack(fill="both", expand=True, pady=(10, 0))
        self.log_line("欢迎使用。请选择输入文件/文件夹，并输入要删除的属性名。")

    def log_line(self, text: str) -> None:
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def safe_log_line(self, text: str) -> None:
        self.after(0, self.log_line, text)

    def choose_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("SVG files", "*.svg"), ("All files", "*.*")])
        if path:
            self.mode_var.set("file")
            self.input_file_var.set(path)
            self.output_file_var.set(str(default_output_path(path)))
            self.status_var.set("已选择单文件")

    def choose_dir(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.mode_var.set("folder")
            self.input_dir_var.set(path)
            self.output_dir_var.set(str(Path(path) / "output_cleaned"))
            self.status_var.set("已选择文件夹")

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
        self.status_var.set("单文件模式" if self.mode_var.get() == "file" else "批量模式")

    def run_processing(self, dry_run: bool) -> None:
        threading.Thread(target=self._process, args=(dry_run,), daemon=True).start()

    def _set_busy(self, busy: bool, text: str) -> None:
        self.status_var.set(text)
        if busy:
            self.progress.start(12)
        else:
            self.progress.stop()

    def _process(self, dry_run: bool) -> None:
        attrs = parse_attributes(self.attrs_text.get("1.0", "end"))
        if not attrs:
            messagebox.showerror("错误", "请输入至少一个属性名")
            return
        self.after(0, self._set_busy, True, "预览中..." if dry_run else "处理中...")
        self.safe_log_line("开始预览..." if dry_run else "开始处理...")
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
        total_removed = sum(int(item.get("total_removed", 0)) for item in results)
        failed = [item for item in results if not item.get("success")]
        for item in results:
            self.safe_log_line(f"{'成功' if item['success'] else '失败'}: {item['input']} 删除 {item['total_removed']} 个；{item['removed_counts']} {item.get('error') or ''}")
        self.safe_log_line(f"总处理文件数: {len(results)}；总删除属性数: {total_removed}；失败: {len(failed)}")
        self.safe_log_line(f"报告: {report_path}")
        self.after(0, self.summary_var.set, f"完成 {len(results)} 个文件，删除 {total_removed} 个属性，失败 {len(failed)} 个。")
        self.after(0, self._set_busy, False, "预览完成" if dry_run else "处理完成")
        if not dry_run:
            self.after(0, messagebox.showinfo, "完成", f"处理完成。输出位置：{report_dir}")

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
