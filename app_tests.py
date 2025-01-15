import unittest
from app import ResourceMonitorApp
import customtkinter as ctk
import sqlite3
from unittest.mock import patch

class TestResourceMonitorApp(unittest.TestCase):
    def setUp(self):
        self.root = ctk.CTk()  # Создаем корневое окно
        self.app = ResourceMonitorApp(self.root, db_connector=self.mock_db_connector())  # Инициализируем приложение

    def mock_db_connector(self):
        # Создаем временную базу данных в памяти для тестирования
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute(""" 
            CREATE TABLE resource_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                cpu_usage REAL,
                ram_usage REAL,
                disk_usage REAL,
                record_number INTEGER
            )
        """)
        conn.commit()
        return conn

    def test_initialization(self):
        # Проверяем, что приложение инициализируется правильно
        self.assertEqual(self.app.root.title(), "Мониторинг системы")
        self.assertEqual(self.app.update_interval, 1000)

    def test_setup_database(self):
        # Проверяем, что база данных настраивается правильно
        self.app.setup_database()
        cursor = self.app.db_connector.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='resource_usage'")
        table_exists = cursor.fetchone()
        self.assertIsNotNone(table_exists)  # Убедимся, что таблица существует

    def test_start_recording(self):
        self.app.start_recording()
        self.assertTrue(self.app.recording)  # Убедимся, что запись активна
        self.assertIsNotNone(self.app.timer_label)

    def test_stop_recording(self):
        self.app.start_recording()
        self.app.stop_recording()
        self.assertFalse(self.app.recording)  # Убедимся, что запись остановлена

    def test_record_usage(self):
        self.app.start_recording()
        self.app.record_usage()  # Симулируем запись использования
        cursor = self.app.db_connector.cursor()
        cursor.execute("SELECT COUNT(*) FROM resource_usage")
        count = cursor.fetchone()[0]
        self.assertGreater(count, 0)  # Убедимся, что записи добавлены

    def test_record_number_increment(self):
        self.app.start_recording()
        self.app.record_usage()  # Начинаем запись
        self.app.stop_recording()
        self.app.start_recording()  # Начинаем запись снова
        self.app.record_usage()  # Записываем снова
        cursor = self.app.db_connector.cursor()
        cursor.execute("SELECT MAX(record_number) FROM resource_usage")
        max_record_number = cursor.fetchone()[0]
        self.assertEqual(max_record_number, 2)  # Убедимся, что номер записи увеличился

    def test_view_records(self):
        self.app.start_recording()
        self.app.record_usage()  # Симулируем запись использования
        self.app.stop_recording()
        self.app.view_records()  # Открываем окно просмотра записей
        cursor = self.app.db_connector.cursor()
        cursor.execute("SELECT COUNT(*) FROM resource_usage")
        count = cursor.fetchone()[0]
        self.assertGreater(count, 0)  # Убедимся, что есть записи для просмотра

    def tearDown(self):
        self.app.db_connector.close()  # Закрываем соединение с базой данных после тестов

if __name__ == "__main__":
    unittest.main()  # Запускаем тесты