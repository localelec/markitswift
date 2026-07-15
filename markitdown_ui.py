"""MarkItSwift — desktop UI (CustomTkinter) for converting documents to Markdown.

แปลงไฟล์เอกสาร (PDF, Word, Excel, PowerPoint, รูปภาพ ฯลฯ) เป็น Markdown
ขับเคลื่อนด้วย markitdown ของ Microsoft; ออกแบบให้แพ็กเป็น .exe ด้วย PyInstaller (ดู build_exe.bat).
"""
from __future__ import annotations

import os
import queue
import sys
import threading
import traceback

import customtkinter as ctk
from tkinter import filedialog, messagebox

try:
    from markitdown import MarkItDown
except ImportError:  # pragma: no cover - surfaced to the user at runtime
    MarkItDown = None

# ลาก-วางไฟล์ (optional): ต้องมี tkinterdnd2 จึงจะใช้ได้
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _DND_AVAILABLE = True
except ImportError:  # pragma: no cover - DnD ปิดอัตโนมัติถ้าไม่มี lib
    DND_FILES = None
    TkinterDnD = None
    _DND_AVAILABLE = False


def _dnd_base():
    """คืน mixin สำหรับเปิดใช้ DnD บน CTk ถ้ามี tkinterdnd2, ไม่งั้นคืน object เปล่า."""
    return TkinterDnD.DnDWrapper if _DND_AVAILABLE else object


SUPPORTED = [
    ("เอกสารทั้งหมด", "*.pdf *.docx *.pptx *.xlsx *.xls *.csv *.json *.xml "
                       "*.html *.htm *.txt *.md *.rtf *.epub "
                       "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.mp3 *.wav *.m4a *.zip"),
    ("PDF", "*.pdf"),
    ("Word", "*.docx"),
    ("PowerPoint", "*.pptx"),
    ("Excel", "*.xlsx *.xls"),
    ("รูปภาพ", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
    ("ทุกไฟล์", "*.*"),
]


def resource_path(rel: str) -> str:
    """คืน path ของ resource ให้ใช้ได้ทั้งตอนรันปกติและตอนแพ็กเป็น exe."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


class MarkItDownApp(ctk.CTk, _dnd_base()):
    def __init__(self) -> None:
        super().__init__()
        self.title("MarkItSwift")
        self.geometry("1040x680")
        self.minsize(820, 520)

        # ไอคอนหน้าต่าง/แอป (ไม่พังถ้าไม่พบไฟล์)
        try:
            self.iconbitmap(resource_path("app.ico"))
        except Exception:  # noqa: BLE001
            pass

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # เปิดใช้งานความสามารถ drag & drop (ถ้ามี tkinterdnd2)
        self._dnd_ready = False
        if _DND_AVAILABLE:
            try:
                self.TkdndVersion = TkinterDnD._require(self)
                self._dnd_ready = True
            except Exception:  # noqa: BLE001 - รันต่อได้แม้ DnD โหลดไม่สำเร็จ
                self._dnd_ready = False

        self._converter = MarkItDown(enable_plugins=False) if MarkItDown else None
        self._selected_path: str | None = None
        self._markdown: str = ""
        self._queue: "queue.Queue[tuple]" = queue.Queue()

        self._build_ui()
        self.after(100, self._poll_queue)

        if self._converter is None:
            self._set_status("ไม่พบแพ็กเกจ markitdown — ติดตั้งด้วย: pip install \"markitdown[all]\"", "error")

    # ---------- UI ----------
    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 4))
        ctk.CTkLabel(
            header, text="MarkItSwift",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="เลือกหรือลากไฟล์ PDF, Word, Excel, PowerPoint, รูปภาพ ฯลฯ แล้วแปลงเป็น Markdown",
            text_color="gray70",
        ).pack(anchor="w")

        # Controls
        bar = ctk.CTkFrame(self)
        bar.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(bar, text="เลือกไฟล์...", width=120, command=self._choose_file).grid(
            row=0, column=0, padx=(12, 8), pady=12)
        self.file_label = ctk.CTkLabel(bar, text="ยังไม่ได้เลือกไฟล์", anchor="w", text_color="gray70")
        self.file_label.grid(row=0, column=1, sticky="ew", padx=8)

        self.convert_btn = ctk.CTkButton(
            bar, text="แปลงเป็น Markdown", width=170,
            command=self._start_convert, state="disabled")
        self.convert_btn.grid(row=0, column=2, padx=(8, 12))

        # Drop zone (ลาก-วางไฟล์)
        self.drop_zone = ctk.CTkFrame(self, height=64, fg_color="gray17",
                                      border_width=2, border_color="gray30")
        self.drop_zone.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 8))
        self.drop_zone.grid_propagate(False)
        self.drop_zone.grid_columnconfigure(0, weight=1)
        self.drop_zone.grid_rowconfigure(0, weight=1)
        hint = ("⬇  ลากไฟล์มาวางที่นี่เพื่อแปลง"
                if self._dnd_ready else
                "ติดตั้ง tkinterdnd2 เพื่อเปิดใช้งานลาก-วางไฟล์  (pip install tkinterdnd2)")
        self.drop_label = ctk.CTkLabel(self.drop_zone, text=hint, text_color="gray60",
                                       font=ctk.CTkFont(size=14))
        self.drop_label.grid(row=0, column=0)
        if self._dnd_ready:
            self._register_dnd(self.drop_zone)
            self._register_dnd(self.drop_label)

        # Output area
        out = ctk.CTkFrame(self)
        out.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 8))
        out.grid_columnconfigure(0, weight=1)
        out.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(out, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        ctk.CTkLabel(toolbar, text="ผลลัพธ์ Markdown",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        self.copy_btn = ctk.CTkButton(toolbar, text="คัดลอก", width=90,
                                      command=self._copy, state="disabled")
        self.copy_btn.pack(side="right", padx=4)
        self.save_btn = ctk.CTkButton(toolbar, text="บันทึก .md", width=110,
                                      command=self._save, state="disabled")
        self.save_btn.pack(side="right", padx=4)
        self.clear_btn = ctk.CTkButton(toolbar, text="ล้าง", width=70, fg_color="gray30",
                                       hover_color="gray40", command=self._clear)
        self.clear_btn.pack(side="right", padx=4)

        self.textbox = ctk.CTkTextbox(out, wrap="word",
                                      font=ctk.CTkFont(family="Consolas", size=13))
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        if self._dnd_ready:
            self._register_dnd(self.textbox)

        # Status bar
        status = ctk.CTkFrame(self, height=30)
        status.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 12))
        status.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(status, text="พร้อมใช้งาน", anchor="w", text_color="gray70")
        self.status_label.grid(row=0, column=0, sticky="ew", padx=12, pady=4)
        self.progress = ctk.CTkProgressBar(status, width=160, mode="indeterminate")
        self.progress.grid(row=0, column=1, padx=12, pady=4)
        self.progress.set(0)

    # ---------- Actions ----------
    def _choose_file(self) -> None:
        path = filedialog.askopenfilename(title="เลือกไฟล์ที่จะแปลง", filetypes=SUPPORTED)
        if path:
            self._set_file(path)

    # ---------- Drag & drop ----------
    def _register_dnd(self, widget) -> None:
        widget.drop_target_register(DND_FILES)
        widget.dnd_bind("<<Drop>>", self._on_drop)
        widget.dnd_bind("<<DragEnter>>", self._on_drag_enter)
        widget.dnd_bind("<<DragLeave>>", self._on_drag_leave)

    def _on_drag_enter(self, _event) -> None:
        self.drop_zone.configure(border_color="#0ea5e9", fg_color="gray23")
        self.drop_label.configure(text="⬇  วางเพื่อแปลง", text_color="#38bdf8")

    def _on_drag_leave(self, _event) -> None:
        self.drop_zone.configure(border_color="gray30", fg_color="gray17")
        self.drop_label.configure(text="⬇  ลากไฟล์มาวางที่นี่เพื่อแปลง", text_color="gray60")

    def _on_drop(self, event) -> None:
        self._on_drag_leave(event)
        # event.data อาจมีหลายไฟล์และมี { } ครอบ path ที่มีช่องว่าง — ใช้ splitlist แยก
        try:
            paths = list(self.tk.splitlist(event.data))
        except Exception:  # noqa: BLE001
            paths = [event.data.strip("{}")]
        if not paths:
            return
        path = paths[0]
        if not os.path.isfile(path):
            self._set_status("ลากได้เฉพาะไฟล์เท่านั้น", "error")
            return
        if len(paths) > 1:
            self._set_status(f"เลือกไฟล์แรกจาก {len(paths)} ไฟล์: {os.path.basename(path)}")
        self._set_file(path)
        # แปลงให้อัตโนมัติเมื่อวางไฟล์
        self._start_convert()

    def _set_file(self, path: str) -> None:
        self._selected_path = path
        self.file_label.configure(text=os.path.basename(path), text_color="white")
        self.convert_btn.configure(state="normal" if self._converter else "disabled")
        self._set_status(f"เลือกไฟล์: {os.path.basename(path)}")

    def _start_convert(self) -> None:
        if not self._selected_path or not self._converter:
            return
        self.convert_btn.configure(state="disabled")
        self.progress.start()
        self._set_status("กำลังแปลง...")
        threading.Thread(target=self._convert_worker,
                         args=(self._selected_path,), daemon=True).start()

    def _convert_worker(self, path: str) -> None:
        try:
            result = self._converter.convert(path)
            self._queue.put(("done", result.text_content or ""))
        except Exception as exc:  # noqa: BLE001 - report any converter error to the UI
            self._queue.put(("error", f"{exc}\n\n{traceback.format_exc()}"))

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                self.progress.stop()
                self.progress.set(0)
                self.convert_btn.configure(state="normal")
                if kind == "done":
                    self._markdown = payload
                    self.textbox.delete("1.0", "end")
                    self.textbox.insert("1.0", payload)
                    ok = bool(payload.strip())
                    self.copy_btn.configure(state="normal" if ok else "disabled")
                    self.save_btn.configure(state="normal" if ok else "disabled")
                    self._set_status(
                        f"แปลงสำเร็จ — {len(payload):,} ตัวอักษร" if ok
                        else "แปลงสำเร็จ แต่ไม่มีเนื้อหาข้อความ", "ok")
                elif kind == "error":
                    self._set_status("แปลงไฟล์ไม่สำเร็จ", "error")
                    messagebox.showerror("แปลงไฟล์ไม่สำเร็จ", payload)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _copy(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.textbox.get("1.0", "end-1c"))
        self._set_status("คัดลอกไปยังคลิปบอร์ดแล้ว", "ok")

    def _save(self) -> None:
        default = "output"
        if self._selected_path:
            default = os.path.splitext(os.path.basename(self._selected_path))[0]
        path = filedialog.asksaveasfilename(
            title="บันทึกเป็น Markdown", defaultextension=".md",
            initialfile=f"{default}.md",
            filetypes=[("Markdown", "*.md"), ("ทุกไฟล์", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.textbox.get("1.0", "end-1c"))
            self._set_status(f"บันทึกแล้ว: {os.path.basename(path)}", "ok")
        except OSError as exc:
            messagebox.showerror("บันทึกไม่สำเร็จ", str(exc))

    def _clear(self) -> None:
        self.textbox.delete("1.0", "end")
        self._markdown = ""
        self._selected_path = None
        self.file_label.configure(text="ยังไม่ได้เลือกไฟล์", text_color="gray70")
        self.convert_btn.configure(state="disabled")
        self.copy_btn.configure(state="disabled")
        self.save_btn.configure(state="disabled")
        self._set_status("พร้อมใช้งาน")

    def _set_status(self, text: str, kind: str = "info") -> None:
        colors = {"info": "gray70", "ok": "#34d399", "error": "#f87171"}
        self.status_label.configure(text=text, text_color=colors.get(kind, "gray70"))


def main() -> None:
    app = MarkItDownApp()
    app.mainloop()


if __name__ == "__main__":
    main()
