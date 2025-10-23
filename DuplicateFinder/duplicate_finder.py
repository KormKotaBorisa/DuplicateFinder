import os
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Menu
from threading import Thread, Event
import time
import re
import subprocess
import random
import logging
from send2trash import send2trash

# Настройка логирования
logging.basicConfig(filename='duplicate_finder.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class DuplicateFinder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔮 DuplicateFinder")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)
        self.theme = 0
        self.protected_paths = [
            'Windows', 'Program Files', 'Program Files (x86)',
            'System Volume Information', '$RECYCLE.BIN'
        ]
        self.protected_exts = ['.dll', '.sys', 'pagefile.sys']
        self.duplicates_data = []
        self.filtered_data = []
        self.sort_column = None
        self.sort_reverse = False
        self.pause_event = Event()
        self.pause_event.set()
        self.scan_in_progress = False
        self._prev_theme = 0
        self.active_filters = set()
        self.cat_color = "#0000ff"
        self.cat_animation = None
        self.dynamic_file_types = set()
        self.keep_count = 0
        self.title_label = None
        self.donate_btn = None
        self.cat_label = None
        self.status = None
        self.scan_btn = None
        self.folder_btn = None
        self.progress = None
        self.pause_btn = None
        self.pause_check = None
        self.preview_btn = None
        self.stats_btn = None
        self.mass_delete_btn = None
        self.filter_photo = None
        self.filter_music = None
        self.filter_docs = None
        self.filter_video = None
        self.filter_folder = None
        self.clear_filter = None
        self.filter_dynamic = None
        self.tree = None
        self.path_var = None
        self.reset_keep_btn = None
        self.show_initial_warning()

    def show_initial_warning(self):
        if messagebox.askokcancel("⚠️ Предупреждение", "Ваш ПК может работать чуть медленнее из-за нагрузки на диск. Продолжить?"):
            self.setup_ui()
        else:
            self.root.destroy()

    def setup_ui(self):
        menubar = Menu(self.root, bg='#1C2526', fg='#5D7A8C', relief='flat', bd=0)
        theme_menu = Menu(menubar, tearoff=0, bg='#1C2526', fg='#5D7A8C', relief='flat', bd=0)
        theme_menu.add_command(label="Светлая тема", command=lambda: self.switch_theme(0))
        theme_menu.add_command(label="Темная тема", command=lambda: self.switch_theme(1))
        theme_menu.add_command(label="Розовая тема", command=lambda: self.switch_theme(2))
        menubar.add_cascade(label="🌞 Тема", menu=theme_menu)
        self.root.config(menu=menubar)

        header_frame = tk.Frame(self.root, bg=self.root.cget('bg'), height=80, bd=0, highlightthickness=0)
        header_frame.pack(fill='x', padx=20, pady=10)
        header_frame.pack_propagate(False)
        title_frame = tk.Frame(header_frame, bg=self.root.cget('bg'), bd=0, highlightthickness=0)
        title_frame.pack(side=tk.LEFT)
        self.title_label = tk.Label(title_frame, text="🔮 DuplicateFinder",
                                  font=('Segoe UI', 28, 'bold'), bg=self.root.cget('bg'))
        self.title_label.pack(side=tk.LEFT)
        self.donate_btn = tk.Button(title_frame, text="💖 Поддержка",
                                  command=self.show_donate_menu, font=('Segoe UI', 12), width=12, relief='flat', bd=0, highlightthickness=0)
        self.donate_btn.pack(side=tk.LEFT, padx=10)
        self.cat_label = tk.Label(title_frame, text="", font=('Segoe UI', 28), bg=self.root.cget('bg'))
        self.cat_label.pack(side=tk.LEFT)
        self.cat_label.bind("<Button-1>", self.start_cat_animation)

        control_frame = tk.Frame(self.root, bg=self.root.cget('bg'), relief='flat', bd=0, highlightthickness=0)
        control_frame.pack(fill='x', padx=20, pady=10)
        btn_frame = tk.Frame(control_frame, bg=self.root.cget('bg'), bd=0, highlightthickness=0)
        btn_frame.pack(pady=15)
        self.scan_btn = tk.Button(btn_frame, text="🚀 СКАНИРОВАТЬ ДИСК",
                                 command=self.start_scan, font=('Segoe UI', 14, 'bold'), width=20, height=2, relief='flat', bd=0, highlightthickness=0)
        self.scan_btn.pack(side=tk.LEFT, padx=10, pady=5)
        self.folder_btn = tk.Button(btn_frame, text="📁 Выбрать папку",
                                   command=self.choose_folder, font=('Segoe UI', 12), width=15, relief='flat', bd=0, highlightthickness=0)
        self.folder_btn.pack(side=tk.LEFT, padx=10, pady=5)
        self.path_var = tk.StringVar(value="C:\\")
        path_entry = tk.Entry(control_frame, textvariable=self.path_var, width=70, font=('Segoe UI', 11), relief='flat', bd=0, highlightthickness=0)
        path_entry.pack(pady=10)

        progress_frame = tk.Frame(control_frame, bg=self.root.cget('bg'), bd=0, highlightthickness=0)
        progress_frame.pack(pady=10, fill='x')
        self.progress = ttk.Progressbar(progress_frame, length=800, mode='determinate', style='TProgressbar')
        self.progress.pack(fill='x', expand=True)
        self.pause_btn = tk.Button(progress_frame, text="⏸️ ПАУЗА",
                                 command=self.toggle_pause, font=('Segoe UI', 12), width=10, relief='flat', bd=0, highlightthickness=0)
        self.pause_btn.pack(pady=5, side=tk.RIGHT)
        self.pause_check = tk.Label(progress_frame, text="", font=('Segoe UI', 12), bg=self.root.cget('bg'))
        self.pause_check.pack(pady=5, side=tk.RIGHT, padx=5)
        self.status = tk.Label(progress_frame, text="🛡️ СИСТЕМА ЗАЩИЩЕНА | Готов к сканированию",
                              font=('Segoe UI', 11), bg=self.root.cget('bg'))
        self.status.pack(pady=5, fill='x')

        action_frame = tk.Frame(self.root, bg=self.root.cget('bg'), relief='flat', bd=0, highlightthickness=0)
        action_frame.pack(fill='x', padx=20, pady=10)
        self.preview_btn = tk.Button(action_frame, text="👁️ ПРЕДВАРИТЕЛЬНАЯ ПРОВЕРКА",
                                   command=self.preview_deletion, font=('Segoe UI', 12, 'bold'), width=25, relief='flat', bd=0, highlightthickness=0)
        self.preview_btn.pack(side=tk.LEFT, padx=10, pady=5)
        self.stats_btn = tk.Button(action_frame, text="📊 СТАТИСТИКА",
                                  command=self.show_detailed_stats, font=('Segoe UI', 12), width=15, relief='flat', bd=0, highlightthickness=0)
        self.stats_btn.pack(side=tk.LEFT, padx=10, pady=5)
        self.mass_delete_btn = tk.Button(action_frame, text="🔒 УДАЛИТЬ (3 подтверждения)",
                                       command=self.final_delete, font=('Segoe UI', 12, 'bold'), width=25, relief='flat', bd=0, highlightthickness=0)
        self.mass_delete_btn.pack(side=tk.LEFT, padx=10, pady=5)

        filter_frame = tk.LabelFrame(action_frame, text="🎯 ПРОДВИНУТЫЙ ФИЛЬТР - ЧТО ОСТАВИТЬ",
                                   font=('Segoe UI', 12, 'bold'), bg=self.root.cget('bg'), fg='#5D7A8C',
                                   relief='flat', bd=0, highlightthickness=0, padx=10, pady=5)
        filter_frame.pack(pady=10, fill='x', padx=20)
        filter_btn_frame = tk.Frame(filter_frame, bg=self.root.cget('bg'), bd=0, highlightthickness=0)
        filter_btn_frame.pack(pady=5)
        self.filter_photo = tk.Button(filter_btn_frame, text="🖼️ ФОТО",
                                     command=lambda: self.toggle_filter('photo'), width=9, relief='flat', bd=0, highlightthickness=0)
        self.filter_photo.pack(side=tk.LEFT, padx=3, pady=3)
        self.filter_music = tk.Button(filter_btn_frame, text="🎵 МУЗЫКА",
                                     command=lambda: self.toggle_filter('music'), width=9, relief='flat', bd=0, highlightthickness=0)
        self.filter_music.pack(side=tk.LEFT, padx=3, pady=3)
        self.filter_docs = tk.Button(filter_btn_frame, text="📄 ДОКУМЕНТЫ",
                                    command=lambda: self.toggle_filter('docs'), width=10, relief='flat', bd=0, highlightthickness=0)
        self.filter_docs.pack(side=tk.LEFT, padx=3, pady=3)
        self.filter_video = tk.Button(filter_btn_frame, text="🎥 ВИДЕО",
                                     command=lambda: self.toggle_filter('video'), width=9, relief='flat', bd=0, highlightthickness=0)
        self.filter_video.pack(side=tk.LEFT, padx=3, pady=3)
        self.filter_folder = tk.Button(filter_btn_frame, text="📁 ПАПКА",
                                      command=self.filter_by_folder, width=9, relief='flat', bd=0, highlightthickness=0)
        self.filter_folder.pack(side=tk.LEFT, padx=3, pady=3)
        self.filter_dynamic = tk.Button(filter_btn_frame, text="⭐ Расширение",
                                      command=self.show_dynamic_filter, width=11, relief='flat', bd=0, highlightthickness=0)
        self.filter_dynamic.pack(side=tk.LEFT, padx=3, pady=3)
        self.clear_filter = tk.Button(filter_btn_frame, text="🧹 ОЧИСТИТЬ",
                                     command=self.clear_filters, width=9, relief='flat', bd=0, highlightthickness=0)
        self.clear_filter.pack(side=tk.LEFT, padx=3, pady=3)

        columns = ("№", "Оставить ✓", "🗑️ Удалить", "Размер", "Путь", "Тип", "Хэш", "Открыть")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=25, style='Treeview')
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=150 if col == "Оставить ✓" else 140 if col != "Открыть" else 80)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview, style='Vertical.TScrollbar')
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        self.tree.bind("<Double-1>", self.open_file)
        self.tree.bind("<Button-1>", self.toggle_keep)

        reset_frame = tk.Frame(self.root, bg=self.root.cget('bg'), bd=0, highlightthickness=0)
        reset_frame.pack(pady=5)
        self.reset_keep_btn = tk.Button(reset_frame, text="🧹 Сбросить отмеченные",
                                      command=self.reset_keep, font=('Segoe UI', 12), width=15, relief='flat', bd=0, highlightthickness=0)
        self.reset_keep_btn.pack(side=tk.LEFT, padx=20)

        self.update_styles()

    def update_styles(self):
        if self.theme == 0:
            bg_color = '#f5ede1'
            text_color = '#1a1a2e'
            button_bg = bg_color
            progress_trough = '#d9c8b6'
            table_bg = '#e0e0e0'
            table_text = '#000000'
            header_bg = '#d9c8b6'
            check_color = '#32CD32'
        elif self.theme == 1:
            bg_color = '#1C2526'
            text_color = '#5D7A8C'
            button_bg = '#2D3A3E'
            progress_trough = '#2D3A3E'
            table_bg = '#2D3A3E'
            table_text = '#FFFFFF'
            header_bg = '#1C2526'
            check_color = '#32CD32'
        else:
            bg_color = '#ffe6f0'
            text_color = '#1a1a2e'
            button_bg = bg_color
            progress_trough = '#ffd1e0'
            table_bg = '#e0e0e0'
            table_text = '#000000'
            header_bg = bg_color
            check_color = '#32CD32'

        if self.theme != self._prev_theme:
            self.stop_cat_animation()
            self._interpolate_styles(bg_color, text_color, button_bg, progress_trough, table_bg)
            self._prev_theme = self.theme
            if self.theme == 2:
                self.start_cat_animation(None)

        self.root.configure(bg=bg_color)
        style = ttk.Style()
        style.configure('TButton', font=('Segoe UI', 11), padding=10, background=button_bg,
                        foreground=text_color, borderwidth=0, highlightthickness=0)
        style.configure('TLabel', font=('Segoe UI', 12), background=bg_color, foreground=text_color)
        style.configure('Treeview', background=table_bg, foreground=table_text, fieldbackground=table_bg)
        style.configure('Treeview.Heading', background=header_bg, foreground='#000000', font=('Segoe UI', 10, 'bold'))
        style.configure('TProgressbar', background='#5D7A8C', troughcolor=progress_trough)
        style.configure('TLabelFrame', background=bg_color, foreground=text_color, borderwidth=0, highlightthickness=0)
        style.configure('TLabelFrame.Label', background=bg_color, foreground=text_color)
        style.configure('Vertical.TScrollbar', background=bg_color, troughcolor=bg_color, borderwidth=0)

        if self.title_label: self.title_label.config(bg=bg_color, fg=text_color)
        if self.donate_btn: self.donate_btn.config(bg=button_bg, fg=text_color, highlightthickness=0)
        if self.cat_label:
            self.cat_label.config(bg=bg_color, fg=self.cat_color, text="🐱🐾" if self.theme == 2 else "")
        if self.status: self.status.config(bg=bg_color, fg=text_color)
        if self.scan_btn: self.scan_btn.config(bg=button_bg, fg=text_color)
        if self.folder_btn: self.folder_btn.config(bg=button_bg, fg=text_color)
        if self.progress: self.progress.config(style='TProgressbar')
        if self.pause_btn: self.pause_btn.config(bg=button_bg, fg=text_color)
        if self.pause_check: self.pause_check.config(bg=bg_color, fg=check_color, text="✅" if not self.scan_in_progress else "")
        if self.preview_btn: self.preview_btn.config(bg=button_bg, fg=text_color)
        if self.stats_btn: self.stats_btn.config(bg=button_bg, fg=text_color)
        if self.mass_delete_btn: self.mass_delete_btn.config(bg=button_bg, fg=text_color)
        if self.filter_photo: self.filter_photo.config(bg=button_bg, fg=text_color)
        if self.filter_music: self.filter_music.config(bg=button_bg, fg=text_color)
        if self.filter_docs: self.filter_docs.config(bg=button_bg, fg=text_color)
        if self.filter_video: self.filter_video.config(bg=button_bg, fg=text_color)
        if self.filter_folder: self.filter_folder.config(bg=button_bg, fg=text_color)
        if self.filter_dynamic: self.filter_dynamic.config(bg=button_bg, fg=text_color)
        if self.clear_filter: self.clear_filter.config(bg=button_bg, fg=text_color)
        if self.reset_keep_btn: self.reset_keep_btn.config(bg=button_bg, fg=text_color)
        if self.tree: self.tree.configure(style='Treeview')

        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.config(bg=bg_color, bd=0, highlightthickness=0)
            elif isinstance(widget, tk.Entry):
                widget.config(bg='#2D3A3E' if self.theme == 1 else '#d9c8b6' if self.theme == 0 else '#ffd1e0', fg=text_color, bd=0, highlightthickness=0)
            elif isinstance(widget, tk.LabelFrame):
                widget.config(bg=bg_color, fg=text_color, bd=0, highlightthickness=0)

    def _interpolate_styles(self, bg_color, text_color, button_bg, progress_trough, table_bg):
        current_bg = self.root.cget('bg')
        for _ in range(10):
            r1, g1, b1 = self._hex_to_rgb(current_bg)
            r2, g2, b2 = self._hex_to_rgb(bg_color)
            r = int(r1 + (r2 - r1) / 10)
            g = int(g1 + (g2 - g1) / 10)
            b = int(b1 + (b2 - b1) / 10)
            interp_bg = f'#{r:02x}{g:02x}{b:02x}'
            self.root.configure(bg=interp_bg)
            self.root.update()
            time.sleep(0.01)

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def switch_theme(self, theme_index):
        if self.scan_in_progress:
            messagebox.showwarning("⚠️", "Подождите завершения предыдущего сканирования!")
            return
        self.theme = theme_index
        self.update_styles()

    def show_donate_menu(self):
        if self.theme == 0:
            bg_color = '#f5ede1'
            text_color = '#1a1a2e'
        elif self.theme == 1:
            bg_color = '#1C2526'
            text_color = '#5D7A8C'
        else:
            bg_color = '#ffe6f0'
            text_color = '#1a1a2e'
        donate_menu = tk.Toplevel(self.root)
        donate_menu.title("💖 Поддержка разработчика")
        donate_menu.geometry("300x150")
        donate_menu.config(bg=bg_color, bd=0, highlightthickness=0)
        donate_menu.transient(self.root)
        donate_menu.grab_set()
        label = tk.Label(donate_menu, text="Спасибо за поддержку!\nПеревод на карту:\n2200702064664738",
                        font=('Segoe UI', 12), bg=bg_color, fg=text_color, justify='center')
        label.pack(expand=True, pady=20)
        close_btn = tk.Button(donate_menu, text="Закрыть", command=donate_menu.destroy,
                             bg='#5D7A8C' if self.theme == 1 else '#ff87b2' if self.theme == 2 else bg_color,
                             fg='#FFFFFF' if self.theme == 1 else 'white' if self.theme == 2 else text_color,
                             font=('Segoe UI', 10), relief='flat', bd=0, highlightthickness=0)
        close_btn.pack(pady=10)

    def is_protected_file(self, filepath):
        path = os.path.dirname(filepath).lower()
        filename = os.path.basename(filepath).lower()
        ext = os.path.splitext(filename)[1].lower()

        for protected in self.protected_paths:
            if protected.lower() in path:
                logging.info(f"Пропущен защищённый путь: {filepath}")
                return True

        if ext in self.protected_exts:
            logging.info(f"Пропущено защищённое расширение: {filepath}")
            return True

        if re.search(r'\$nt\w+\$', path) or 'boot' in path:
            logging.info(f"Пропущен системный файл: {filepath}")
            return True

        return False

    def choose_folder(self):
        if self.scan_in_progress:
            messagebox.showwarning("⚠️", "Подождите завершения предыдущего сканирования!")
            return
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)

    def get_file_hash(self, filepath):
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logging.error(f"Ошибка при хэшировании файла {filepath}: {e}")
            return None

    def start_scan(self):
        if self.scan_in_progress:
            messagebox.showwarning("⚠️", "Подождите завершения предыдущего сканирования!")
            return
        self.scan_in_progress = True
        self.pause_event.set()
        self.dynamic_file_types.clear()
        self.keep_count = 0
        Thread(target=self.scan_files, daemon=True).start()
        self.folder_btn.config(state="disabled")
        if self.pause_btn: self.pause_btn.config(state="normal")
        if self.pause_check: self.pause_check.config(text="")

    def toggle_pause(self):
        if not self.scan_in_progress:
            return
        if self.pause_event.is_set():
            self.pause_event.clear()
            if self.pause_btn: self.pause_btn.config(text="▶️ ПРОДОЛЖИТЬ")
            if self.status: self.status.config(text="⏸️ Сканирование на паузе...")
        else:
            self.pause_event.set()
            if self.pause_btn: self.pause_btn.config(text="⏸️ ПАУЗА")
            if self.status: self.status.config(text="▶️ Сканирование продолжается...")
            self.root.update()

    def scan_files(self):
        start_time = time.time()
        scan_path = self.path_var.get()
        if self.status: self.status.config(text="🔍 Сканирую с ЗАЩИТОЙ системы...")
        if self.scan_btn: self.scan_btn.config(state="disabled")
        if self.progress: self.progress['value'] = 0
        files = []
        hash_dict = {}
        try:
            for root, dirs, filenames in os.walk(scan_path):
                logging.info(f"Сканирую директорию: {root}")
                if any(protected.lower() in root.lower() for protected in self.protected_paths):
                    logging.info(f"Пропущена защищённая директория: {root}")
                    continue
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    if self.is_protected_file(filepath):
                        continue
                    try:
                        size = os.path.getsize(filepath)
                        ext = os.path.splitext(filename)[1].lower()
                        self.dynamic_file_types.add(ext)
                        files.append((filepath, size))
                        logging.info(f"Добавлен файл для сканирования: {filepath}")
                    except OSError as e:
                        logging.error(f"Ошибка при обработке файла {filepath}: {e}")
                        continue
        except Exception as e:
            logging.error(f"Ошибка при сканировании директории {scan_path}: {e}")
            messagebox.showerror("Ошибка", f"Ошибка при сканировании: {e}")
            self.finalize_scan(start_time)
            return

        if self.progress: self.progress['maximum'] = len(files)
        for i, (filepath, size) in enumerate(files):
            if not self.pause_event.is_set():
                self.pause_event.wait()
            if self.progress: self.progress['value'] = i + 1
            self.root.update()
            file_hash = self.get_file_hash(filepath)
            if file_hash:
                if file_hash not in hash_dict:
                    hash_dict[file_hash] = []
                hash_dict[file_hash].append((filepath, size))
        self.duplicates_data = []
        for file_hash, file_list in hash_dict.items():
            if len(file_list) > 1:
                file_list.sort(key=lambda x: len(os.path.dirname(x[0])))
                keep_file = file_list[0]
                for filepath, size in file_list[1:]:
                    file_type = self.get_file_type(filepath)
                    self.duplicates_data.append({
                        'id': len(self.duplicates_data) + 1,
                        'keep': os.path.basename(keep_file[0]),
                        'delete': os.path.basename(filepath),
                        'size': "{:.1f} KB".format(size/1024),
                        'path': filepath,
                        'hash': file_hash[:8],
                        'type': file_type,
                        'keep_path': keep_file[0],
                        'selected_to_keep': False,
                        'keep_count': 0
                    })
        self.filtered_data = self.duplicates_data.copy()
        self.apply_active_filters()
        self.refresh_table()
        self.finalize_scan(start_time)

    def finalize_scan(self, start_time):
        elapsed = time.time() - start_time
        total_to_delete = len(self.duplicates_data)
        total_space = sum(float(d['size'].split()[0]) for d in self.duplicates_data)
        if self.status: self.status.config(text=f"🛡️ ЗАЩИЩЕНО: {total_to_delete} дубликатов | {round(total_space)} KB | {round(elapsed,1)}с")
        if self.scan_btn: self.scan_btn.config(state="normal")
        if self.pause_btn: self.pause_btn.config(state="disabled")
        self.scan_in_progress = False
        self.folder_btn.config(state="normal")
        messagebox.showinfo("✅", "Сканирование завершено!")
        if self.pause_check: self.pause_check.config(text="✅")
        logging.info(f"Сканирование завершено: найдено {total_to_delete} дубликатов, {round(total_space)} KB, время: {round(elapsed,1)}с")

    def get_file_type(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        photo_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        music_exts = ['.mp3', '.wav', '.flac', '.m4a']
        doc_exts = ['.pdf', '.doc', '.docx', '.txt']
        video_exts = ['.mp4', '.avi', '.mkv', '.mov']
        if ext in photo_exts: return '🖼️ Фото'
        if ext in music_exts: return '🎵 Музыка'
        if ext in doc_exts: return '📄 Документ'
        if ext in video_exts: return '🎥 Видео'
        return f'📁 {ext.upper()}'

    def toggle_filter(self, ftype):
        if ftype in self.active_filters:
            self.active_filters.remove(ftype)
        else:
            self.active_filters.add(ftype)
        self.apply_active_filters()

    def apply_active_filters(self):
        if not self.active_filters:
            self.filtered_data = self.duplicates_data.copy()
        else:
            self.filtered_data = []
            for data in self.duplicates_data:
                file_ext = os.path.splitext(data['path'])[1].lower()
                if any(file_ext == ext for ext in self.active_filters) or \
                   ('photo' in self.active_filters and '🖼️ Фото' in data['type']) or \
                   ('music' in self.active_filters and '🎵 Музыка' in data['type']) or \
                   ('docs' in self.active_filters and '📄 Документ' in data['type']) or \
                   ('video' in self.active_filters and '🎥 Видео' in data['type']):
                    self.filtered_data.append(data)
        self.refresh_table()
        if self.status: self.status.config(text=f"🎯 ФИЛЬТРЫ: {', '.join(self.active_filters)} | {len(self.filtered_data)} файлов")

    def show_dynamic_filter(self):
        if not self.dynamic_file_types:
            messagebox.showinfo("ℹ️", "Сначала выполните сканирование для определения расширений!")
            return
        if self.theme == 0:
            bg_color = '#f5ede1'
            text_color = '#1a1a2e'
        elif self.theme == 1:
            bg_color = '#1C2526'
            text_color = '#5D7A8C'
        else:
            bg_color = '#ffe6f0'
            text_color = '#1a1a2e'
        selected_ext = tk.Toplevel(self.root)
        selected_ext.title("Выберите расширения")
        selected_ext.geometry("200x300")
        selected_ext.transient(self.root)
        selected_ext.grab_set()
        options = sorted(list(self.dynamic_file_types))
        var_dict = {ext: tk.BooleanVar() for ext in options}
        scrollbar = ttk.Scrollbar(selected_ext, orient="vertical", style='Vertical.TScrollbar')
        canvas = tk.Canvas(selected_ext, bg=bg_color, bd=0, highlightthickness=0, yscrollcommand=scrollbar.set)
        frame = tk.Frame(canvas, bg=bg_color, bd=0, highlightthickness=0)
        scrollbar.config(command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.create_window((0, 0), window=frame, anchor="nw")
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        frame.bind("<Configure>", on_frame_configure)
        for ext in options:
            check = tk.Checkbutton(frame, text=f".{ext[1:]}", variable=var_dict[ext], bg=bg_color, fg=text_color, bd=0, highlightthickness=0)
            check.pack(anchor='w', pady=2)
        def apply_filter(event=None):
            selected_exts = [ext for ext, var in var_dict.items() if var.get()]
            if selected_exts:
                self.active_filters.update(selected_exts)
                self.apply_active_filters()
            selected_ext.destroy()
        def reset_filter():
            self.active_filters.clear()
            self.apply_active_filters()
            selected_ext.destroy()
        selected_ext.bind('<Return>', apply_filter)
        btn_frame = tk.Frame(selected_ext, bg=bg_color, bd=0, highlightthickness=0)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Подтвердить", command=apply_filter, relief='flat', bd=0, highlightthickness=0, bg=bg_color, fg=text_color).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Сбросить", command=reset_filter, relief='flat', bd=0, highlightthickness=0, bg=bg_color, fg=text_color).pack(side=tk.LEFT, padx=5)

    def filter_by_folder(self):
        folder = filedialog.askdirectory(title="Выбери папку для сохранения")
        if folder:
            self.filtered_data = []
            for data in self.duplicates_data:
                if folder.lower() in data['keep_path'].lower():
                    data['selected_to_keep'] = True
                    continue
                self.filtered_data.append(data)
            self.refresh_table()

    def clear_filters(self):
        self.active_filters.clear()
        self.filtered_data = self.duplicates_data.copy()
        self.refresh_table()
        if self.status: self.status.config(text="🛡️ Все фильтры очищены")

    def refresh_table(self):
        if self.tree:
            for item in self.tree.get_children():
                self.tree.delete(item)
            for i, data in enumerate(self.filtered_data):
                keep_mark = "✅" if data['selected_to_keep'] else "❌"
                count = str(data['keep_count']) if data['selected_to_keep'] and data['keep_count'] > 0 else ""
                self.tree.insert("", "end", values=(
                    data['id'], f"{keep_mark} {count}", data['delete'], data['size'],
                    os.path.dirname(data['path']), data['type'], data['hash'], "📂"
                ), iid=i)

    def toggle_keep(self, event):
        if not self.scan_in_progress:
            col = self.tree.identify_column(event.x)
            if col == "#2":
                row = self.tree.identify_row(event.y)
                if row:
                    index = int(self.tree.index(row))
                    current_data = self.filtered_data[index]
                    if not current_data['selected_to_keep']:
                        self.keep_count += 1
                        current_data['keep_count'] = self.keep_count
                    else:
                        self.keep_count -= 1
                        current_data['keep_count'] = 0
                        for i, data in enumerate(self.filtered_data):
                            if data['selected_to_keep'] and data['keep_count'] > current_data['keep_count']:
                                data['keep_count'] -= 1
                    current_data['selected_to_keep'] = not current_data['selected_to_keep']
                    keep_mark = "✅" if current_data['selected_to_keep'] else "❌"
                    count = str(current_data['keep_count']) if current_data['selected_to_keep'] and current_data['keep_count'] > 0 else ""
                    self.tree.set(row, "#2", f"{keep_mark} {count}")
                    self.root.update()

    def reset_keep(self):
        if not self.scan_in_progress and any(data['selected_to_keep'] for data in self.filtered_data):
            self.keep_count = 0
            for data in self.filtered_data:
                data['selected_to_keep'] = False
                data['keep_count'] = 0
            self.refresh_table()
            if self.status: self.status.config(text="🛡️ Отмеченные файлы сброшены")

    def sort_by_column(self, col):
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
            self.sort_column = col
        reverse = -1 if self.sort_reverse else 1
        if col == 'Размер':
            self.filtered_data.sort(key=lambda x: float(x['size'].split()[0]), reverse=(reverse == -1))
        elif col == 'Путь':
            self.filtered_data.sort(key=lambda x: x['path'], reverse=(reverse == -1))
        elif col == 'Тип':
            self.filtered_data.sort(key=lambda x: x['type'], reverse=(reverse == -1))
        elif col == 'Хэш':
            self.filtered_data.sort(key=lambda x: x['hash'], reverse=(reverse == -1))
        elif col == '№':
            self.filtered_data.sort(key=lambda x: x['id'], reverse=(reverse == -1))
        elif col == 'Оставить ✓':
            self.filtered_data.sort(
                key=lambda x: (x['selected_to_keep'], x['keep_count'] if x['selected_to_keep'] else float('inf'), x['path']),
                reverse=(reverse == -1)
            )
        self.refresh_table()

    def open_file(self, event):
        if self.tree and self.status:
            item = self.tree.identify_row(event.y)
            if item and self.tree.identify_column(event.x) == '#8':
                index = int(self.tree.index(item))
                filepath = self.filtered_data[index]['path']
                if os.path.exists(filepath):
                    try:
                        subprocess.Popen(['start', '', filepath], shell=True)
                        self.status.config(text="📂 Файл открыт системным приложением!")
                        logging.info(f"Открыт файл: {filepath}")
                    except Exception as e:
                        messagebox.showerror("Ошибка", f"Не удалось открыть файл: {e}")
                        logging.error(f"Ошибка при открытии файла {filepath}: {e}")

    def preview_deletion(self):
        if self.filtered_data and self.status:
            total = len(self.filtered_data)
            space = sum(float(d['size'].split()[0]) for d in self.filtered_data if not d['selected_to_keep'])
            preview = f"🔮 ПРЕДВАРИТЕЛЬНАЯ ПРОВЕРКА\n\n🛡️ СИСТЕМА ЗАЩИЩЕНА!\n📋 К УДАЛЕНИЮ: {sum(1 for d in self.filtered_data if not d['selected_to_keep'])} файлов\n💾 Освободит: {round(space)} KB\n\nПЕРВЫЕ 5:\n"
            for i, data in enumerate([d for d in self.filtered_data if not d['selected_to_keep']][:5], 1):
                preview += f"{i}. {data['delete']} ({data['size']})\n"
            messagebox.showinfo("👁️ ПРОВЕРКА", preview)

    def show_detailed_stats(self):
        if self.filtered_data:
            total = len(self.filtered_data)
            messagebox.showinfo("📊 СТАТИСТИКА", f"Фильтр: {total} файлов")

    def final_delete(self):
        if self.filtered_data:
            total = sum(1 for d in self.filtered_data if not d['selected_to_keep'])
            if total == 0:
                messagebox.showinfo("ℹ️", "Нет файлов для удаления!")
                return
            if messagebox.askyesno("1/3", f"Переместить в корзину {total} файлов?"):
                if messagebox.askyesno("2/3", "Второй раз - УВЕРЕН?"):
                    if messagebox.askyesno("3/3", "ТРЕТИЙ РАЗ - НАВСЕГДА!"):
                        self.execute_deletion(total)

    def execute_deletion(self, total):
        deleted = 0
        errors = []
        for data in self.filtered_data:
            if not data['selected_to_keep']:
                filepath = data['path']
                path_length = len(filepath)
                logging.info(f"Попытка удаления файла: {filepath}, длина пути: {path_length}")
                try:
                    if os.path.exists(filepath):
                        # Нормализация пути для устранения префикса \\?\
                        normalized_path = os.path.normpath(filepath)
                        if path_length > 260:
                            short_path = self._get_short_path(normalized_path)
                            if short_path:
                                normalized_path = short_path
                                logging.info(f"Использован укороченный путь: {short_path}")
                        send2trash(normalized_path)
                        deleted += 1
                        logging.info(f"Перемещён в корзину: {normalized_path}")
                    else:
                        errors.append(f"Файл не найден: {filepath}")
                        logging.error(f"Файл не найден: {filepath}")
                except Exception as e:
                    errors.append(f"Ошибка при перемещении {filepath}: {str(e)}")
                    logging.error(f"Ошибка при перемещении файла {filepath}: {str(e)}")
        if deleted > 0:
            messagebox.showinfo("✅", f"Перемещено в корзину: {deleted} файлов")
        if errors:
            messagebox.showerror("⚠️ Ошибки", "\n".join(errors))

    def _get_short_path(self, long_path):
        """Получение короткого пути для длинных путей на Windows."""
        try:
            import win32api
            return win32api.GetShortPathName(long_path)
        except Exception:
            return None

    def start_cat_animation(self, event):
        if self.theme == 2 and not self.cat_animation:
            self.cat_animation = self.root.after(1000, self.animate_cat)

    def animate_cat(self):
        if self.theme == 2:
            colors = ['#FF4500', '#FFD700', '#00CED1', '#FF69B4']
            self.cat_color = random.choice(colors)
            self.cat_label.config(fg=self.cat_color, text="🐾🐱" if random.random() > 0.5 else "🐱🐾")
            self.cat_animation = self.root.after(1000, self.animate_cat)

    def stop_cat_animation(self):
        if self.cat_animation:
            self.root.after_cancel(self.cat_animation)
            self.cat_animation = None
            self.cat_label.config(text="🐱🐾")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = DuplicateFinder()
    app.run()