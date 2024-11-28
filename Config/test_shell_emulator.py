import unittest
import os
import shutil
from shell_emulator import ShellEmulator  # Предполагается, что ваш эмулятор в файле shell_emulator.py

class TestShellEmulator(unittest.TestCase):
    def setUp(self):
        """Создание временной файловой системы для тестов."""
        self.test_vfs = "test_vfs"
        os.makedirs(self.test_vfs, exist_ok=True)
        self.emulator = ShellEmulator(self.test_vfs)

    def tearDown(self):
        """Удаление временной файловой системы."""
        shutil.rmtree(self.test_vfs)

    def test_ls_basic(self):
        """Проверяем базовую работу ls."""
        os.makedirs(os.path.join(self.test_vfs, "dir1"))
        os.makedirs(os.path.join(self.test_vfs, "dir2"))
        output = self.emulator.run_command("ls")
        self.assertIn("dir1", output)
        self.assertIn("dir2", output)

    def test_ls_empty_directory(self):
        """Проверяем ls в пустой директории."""
        output = self.emulator.run_command("ls")
        self.assertEqual(output.strip(), "")

    def test_cd_valid_directory(self):
        """Проверяем переход в существующую директорию."""
        os.makedirs(os.path.join(self.test_vfs, "dir1"))
        self.emulator.run_command("cd dir1")
        self.assertEqual(self.emulator.get_current_path(), "/dir1")

    def test_cd_invalid_directory(self):
        """Проверяем переход в несуществующую директорию."""
        output = self.emulator.run_command("cd non_existent")
        self.assertIn("No such directory", output)

    def test_mkdir_create_directory(self):
        """Проверяем создание директории."""
        output = self.emulator.run_command("mkdir dir1")
        self.assertIn("created", output)
        self.assertTrue(os.path.isdir(os.path.join(self.test_vfs, "dir1")))

    def test_mkdir_existing_directory(self):
        """Проверяем создание существующей директории."""
        os.makedirs(os.path.join(self.test_vfs, "dir1"))
        output = self.emulator.run_command("mkdir dir1")
        self.assertIn("created", output)
    def test_find_existing_item(self):
        """Проверяем поиск существующего элемента."""
        os.makedirs(os.path.join(self.test_vfs, "dir1"))
        output = self.emulator.run_command("find dir1")
        self.assertIn("dir1", output)

    def test_find_non_existing_item(self):
        """Проверяем поиск несуществующего элемента."""
        output = self.emulator.run_command("find non_existent")
        self.assertIn("No files or directories found", output)
    def test_tail_existing_file(self):
        """Проверяем вывод последних строк файла."""
        file_path = os.path.join(self.test_vfs, "file.txt")
        with open(file_path, "w") as f:
            f.write("line1\nline2\nline3\nline4\nline5\nline6\n")
        output = self.emulator.run_command("tail file.txt")
        self.assertIn("line6", output)
        self.assertIn("line5", output)

    def test_tail_non_existing_file(self):
        """Проверяем ошибку при попытке прочитать несуществующий файл."""
        output = self.emulator.run_command("tail non_existent.txt")
        self.assertIn("Error", output)
    def test_exit(self):
        """Проверяем команду выхода."""
        output = self.emulator.run_command("exit")
        self.assertIn("Exiting shell", output)

