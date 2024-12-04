import unittest
import os
import zipfile
from tempfile import TemporaryDirectory
from shell_emulator import ShellEmulator  # Импортируем эмулятор

class TestShellEmulator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем временный ZIP-архив для тестов"""
        cls.temp_zip = TemporaryDirectory()
        cls.zip_path = os.path.join(cls.temp_zip.name, "vfs.zip")
        # Создаем пустой ZIP-архив для тестов
        with zipfile.ZipFile(cls.zip_path, 'w') as archive:
            archive.writestr('file1.txt', 'Hello, world!')
            archive.writestr('dir1/file2.txt', 'Sample content')

    @classmethod
    def tearDownClass(cls):
        """Удаляем временный ZIP-архив"""
        cls.temp_zip.cleanup()

    def setUp(self):
        """Создаем новый экземпляр эмулятора для каждого теста"""
        self.emulator = ShellEmulator(self.zip_path)

    def tearDown(self):
        """Удаляем эмулятор после каждого теста"""
        del self.emulator

    # Тесты для команды ls
    def test_ls_files(self):
        """Тест на команду ls для вывода файлов"""
        result = self.emulator.run_command("ls")
        self.assertIn('file1.txt', result)
        self.assertIn('dir1', result)

    def test_ls_detailed(self):
        """Тест на команду ls с флагом -l для подробного вывода"""
        result = self.emulator.run_command("ls -l")
        self.assertIn('file1.txt', result)
        self.assertIn('dir1', result)

    # Тесты для команды cd
    def test_cd_success(self):
        """Тест на команду cd для перехода в директорию"""
        result = self.emulator.run_command("cd dir1")
        self.assertEqual(self.emulator.get_current_path(), "/dir1")

    def test_cd_failure(self):
        """Тест на команду cd для перехода в несуществующую директорию"""
        result = self.emulator.run_command("cd non_existing_dir")
        self.assertEqual(result, "No such directory: non_existing_dir")

    # Тесты для команды mkdir
    def test_mkdir_success(self):
        """Тест на команду mkdir для создания новой директории"""
        result = self.emulator.run_command("mkdir new_dir")
        self.assertIn("Directory 'new_dir' created", result)

    def test_mkdir_failure(self):
        """Тест на команду mkdir для создания существующей директории"""
        self.emulator.run_command("mkdir existing_dir")
        result = self.emulator.run_command("mkdir existing_dir")
        self.assertIn("Directory 'existing_dir' already exists", result)

    # Тесты для команды find
    def test_find_success(self):
        """Тест на команду find для поиска файла"""
        result = self.emulator.run_command("find file1")
        self.assertIn('file1.txt', result)

    def test_find_no_results(self):
        """Тест на команду find для поиска несуществующего файла"""
        result = self.emulator.run_command("find non_existing_file")
        self.assertEqual(result, "No files or directories found matching 'non_existing_file'")

    # Тесты для команды tail
    def test_tail_success(self):
        """Тест на команду tail для вывода последних строк файла"""
        result = self.emulator.run_command("tail file1.txt")
        self.assertEqual(result, "Hello, world!")

    def test_tail_failure(self):
        """Тест на команду tail для попытки чтения несуществующего файла"""
        result = self.emulator.run_command("tail non_existing_file.txt")
        self.assertEqual(result, "No such file: non_existing_file.txt")

    # Тесты для команды exit
    def test_exit(self):
        """Тест на команду exit для выхода из оболочки"""
        result = self.emulator.run_command("exit")
        self.assertEqual(result, "Exiting shell...")

if __name__ == "__main__":
    unittest.main()
