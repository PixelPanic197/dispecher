import customtkinter as ctk
import psutil
import time
import sqlite3
from tkinter import messagebox, Scrollbar, Text

class ResourceMonitorApp:
    def __init__(self, root, db_connector=None, psutil_module=None):
        self.root = root
        self.db_connector = db_connector or self.default_db_connector()
        self.psutil_module = psutil_module or psutil
        self.root.title("Мониторинг системы")
        self.root.geometry("400x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.update_interval = 1000
        self.setup_database()

        # Заголовок
        title_label = ctk.CTkLabel(root, text="Мониторинг ресурсов", font=("Arial", 20))
        title_label.pack(pady=10)

        # Кнопка для просмотра записей
        self.view_records_button = ctk.CTkButton(root, text="Просмотр записей", command=self.view_records)
        self.view_records_button.pack(side="top", anchor="ne", padx=10, pady=10)

        # Прогресс-бар для ЦП
        self.cpu_label = ctk.CTkLabel(root, text="Загруженность ЦП", font=("Arial", 14))
        self.cpu_label.pack(pady=5)
        self.cpu_progress = ctk.CTkProgressBar(root, width=300)
        self.cpu_progress.pack(pady=5)
        self.cpu_value = ctk.CTkLabel(root, text="0%", font=("Arial", 12))
        self.cpu_value.pack(pady=5)

        # Отображение данных для ОЗУ
        self.ram_label = ctk.CTkLabel(root, text="Использование ОЗУ", font=("Arial", 14))
        self.ram_label.pack(pady=5)
        self.ram_value = ctk.CTkLabel(root, text="0/0", font=("Arial", 12))
        self.ram_value.pack(pady=5)

        # Отображение данных для ПЗУ
        self.disk_label = ctk.CTkLabel(root, text="Использование ПЗУ", font=("Arial", 14))
        self.disk_label.pack(pady=5)
        self.disk_value = ctk.CTkLabel(root, text="0/0", font=("Arial", 12))
        self.disk_value.pack(pady=5)

        # Поле ввода интервала
        self.interval_label = ctk.CTkLabel(root, text="Интервал обновления (мс):", font=("Arial", 12))
        self.interval_label.pack(pady=10)

        self.interval_entry = ctk.CTkEntry(root, placeholder_text="1000", width=100)
        self.interval_entry.insert(0, "1000")
        self.interval_entry.pack(pady=5)

        self.set_interval_button = ctk.CTkButton(root, text="Установить интервал", command=self.set_interval)
        self.set_interval_button.pack(pady=10)

        # Кнопки записи
        self.button_frame = ctk.CTkFrame(root)
        self.button_frame.pack(pady=10)

        self.record_button = ctk.CTkButton(self.button_frame, text="Начать запись", command=self.start_recording)
        self.record_button.pack(side="left", padx=10)

        self.stop_button = ctk.CTkButton(self.button_frame, text="Остановить запись", command=self.stop_recording)
        self.stop_button.pack(side="left", padx=10)
        self.stop_button.pack_forget()

        self.timer_label = ctk.CTkLabel(root, text="Время записи: 0 секунд", font=("Arial", 10))
        self.timer_label.pack(pady=5)
        self.timer_label.pack_forget 
        self.recording = False
        self.record_number = 0  # Номер текущей записи

        # Запуск обновления данных
        self.update_metrics()

    def default_db_connector(self):
        return sqlite3.connect("resources.db", check_same_thread=False)

    def setup_database(self):
        self.conn = self.db_connector
        self.cursor = self.conn.cursor()
        self.cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS resource_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                cpu_usage REAL,
                ram_usage REAL,
                disk_usage REAL,
                record_number INTEGER
            )
        """)
        self.conn.commit()

    def start_recording(self):
        if not self.recording:
            self.recording = True
            self.record_button.pack_forget()
            self.stop_button.pack(side="left", padx=10)
            self.timer_label.pack(pady=5)
            self.timer = 0  # Сброс таймера
            self.record_number += 1  # Увеличение номера записи
            self.record_usage()

    def stop_recording(self):
        if self.recording:
            self.recording = False
            self.stop_button.pack_forget()
            self.record_button.pack(side="left", padx=10)
            self.timer_label.pack_forget()

    def record_usage(self):
        if self.recording:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            cpu_usage = self.psutil_module.cpu_percent()
            ram_usage = self.psutil_module.virtual_memory().percent
            disk_usage = self.psutil_module.disk_usage('/').percent

            self.cursor.execute("INSERT INTO resource_usage (timestamp, cpu_usage, ram_usage, disk_usage, record_number) VALUES (?, ?, ?, ?, ?)",
                                (timestamp, cpu_usage, ram_usage, disk_usage, self.record_number))
            self.conn.commit()

            self.timer += 1
            self.timer_label.configure(text=f"Время записи: {self.timer} секунд")
            self.root.after(1000, self.record_usage)

    def set_interval(self):
        try:
            new_interval = int(self.interval_entry.get())
            if new_interval < 0:
                raise ValueError("Интервал не может быть отрицательным.")
            self.update_interval = new_interval
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное значение интервала")

    def update_metrics(self):
        cpu_usage = self.psutil_module.cpu_percent()
        ram = self.psutil_module.virtual_memory()
        disk = self.psutil_module.disk_usage('/')

        self.cpu_progress.set(cpu_usage / 100)
        self.cpu_value.configure(text=f"{cpu_usage}%")
        self.ram_value.configure(text=f"{ram.used // (1024 ** 2)}/{ram.total // (1024 ** 2)} МБ")
        self.disk_value.configure(text=f"{disk.used // (1024 ** 2)}/{disk.total // (1024 ** 2)} МБ")

        self.root.after(1000, self.update_metrics)

    def view_records(self):
        records_window = ctk.CTkToplevel(self.root)
        records_window.title("Записи ресурсов")
        records_window.geometry("400x300")

        text_area = Text(records_window)
        text_area.pack(expand=True, fill='both')

        self.cursor.execute("SELECT * FROM resource_usage")
        records = self.cursor.fetchall()

        for record in records:
            text_area.insert('end', f"{record}\n")

        scrollbar = Scrollbar(records_window, command=text_area.yview)
        text_area.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

if __name__ == "__main__":
    root = ctk.CTk()
    app = ResourceMonitorApp(root)
    root.mainloop()