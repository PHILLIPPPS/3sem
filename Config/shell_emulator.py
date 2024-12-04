import zipfile
import os
import stat
from tempfile import TemporaryDirectory


class ShellEmulator:
    def __init__(self, zip_path):
        self.zip_path = zip_path
        self.temp_dir = TemporaryDirectory()  # Временная директория для работы
        self.cwd = "/"  # Корень виртуальной файловой системы
        self.archive = zipfile.ZipFile(zip_path, 'a')  # Открытие ZIP-архива

    def __del__(self):
        # Закрываем архив и удаляем временную директорию
        self.archive.close()
        self.temp_dir.cleanup()

    def run_command(self, command):
        parts = command.split()
        cmd = parts[0]
        args = parts[1:]

        if cmd == "ls":
            return self.ls(args)
        elif cmd == "cd":
            return self.cd(args[0] if args else "/")
        elif cmd == "exit":
            return self.exit()
        elif cmd == "mkdir":
            return self.mkdir(args[0] if args else "")
        elif cmd == "find":
            return self.find(args)
        elif cmd == "tail":
            return self.tail(args[0] if args else "")
        else:
            return "Command not found"

    def ls(self, args):
        detailed = "-l" in args
        entries = self.archive.namelist()

        dirs = set()  # Уникальные директории
        files = set()

        # Разделяем директории и файлы
        for entry in entries:
            if entry.startswith(self.cwd.strip("/")):
                rel_path = entry[len(self.cwd.strip("/")):].strip("/")
                if "/" in rel_path:  # Это директория
                    dirs.add(rel_path.split("/")[0])
                elif rel_path:  # Это файл
                    files.add(rel_path)

        if detailed:
            result = []
            for entry in sorted(dirs | files):  # Перебираем директории и файлы
                if entry in dirs:
                    result.append(f"drwxr-xr-x 0 {entry}")
                else:
                    # Получаем информацию о файле
                    info = next((i for i in self.archive.infolist() if i.filename == f"{self.cwd.strip('/')}/{entry}"),
                                None)
                    size = info.file_size if info else 0
                    result.append(f"-rw-r--r-- {size} {entry}")
            return "\n".join(result)
        else:
            return "\n".join(sorted(dirs | files))

    def cd(self, path):
        if not path:
            path = "/"  # Если путь пустой, возвращаемся в корень

        # Обрабатываем команду 'cd ..'
        if path == "..":
            # Если мы уже в корне, не можем подняться выше
            if self.cwd == "/":
                return "Already at root directory"

            # Разделяем текущий путь по слешам и убираем последний элемент (переходим на уровень выше)
            new_path = '/'.join(self.cwd.strip('/').split('/')[:-1])
            if new_path == "":
                new_path = "/"  # Если путь пустой, значит, мы вернулись в корень
            self.cwd = "/" + new_path.lstrip("/")  # Обновляем текущий путь
            return ""

        # Нормализуем путь относительно текущего каталога
        new_path = os.path.normpath(os.path.join(self.cwd.strip("/"), path)).replace("\\", "/")

        # Проверяем, существует ли каталог в архиве
        entries = self.archive.namelist()
        matched_dirs = [entry for entry in entries if entry.startswith(new_path + "/")]

        if matched_dirs:
            # Убедимся, что путь всегда начинается с одного слэша
            self.cwd = "/" + new_path.lstrip("/")  # Обновляем текущий путь
            return ""
        else:
            return f"No such directory: {path}"

    def mkdir(self, path):
        # Убираем лишние символы `/` в начале и конце пути
        directory = os.path.normpath(os.path.join(self.cwd.strip("/"), path)).strip("/") + "/"

        # Проверяем, существует ли уже такая директория
        if any(entry == directory or entry.startswith(directory) for entry in self.archive.namelist()):
            return f"Directory '{path}' already exists"

        # Добавляем директорию в архив
        self.archive.writestr(directory, "")
        return f"Directory '{path}' created"

    def find(self, args):
        if not args:
            return "Error: find command requires a search term"

        search_term = args[0]
        matches = [entry for entry in self.archive.namelist() if search_term in entry]
        return "\n".join(matches) if matches else f"No files or directories found matching '{search_term}'"

    def tail(self, path, lines=5):
        # Формируем полный путь к файлу относительно текущего каталога
        file_path = os.path.normpath(os.path.join(self.cwd.strip("/"), path)).strip("/")

        # Проверяем, существует ли файл в архиве
        if file_path not in self.archive.namelist():
            return f"No such file: {path}"

        # Читаем последние строки из файла
        try:
            with self.archive.open(file_path) as f:
                # Читаем весь файл, а затем берем последние `lines` строк
                lines_content = f.readlines()[-lines:]
            return ''.join(line.decode('utf-8') for line in lines_content)
        except Exception as e:
            return f"Error: {str(e)}"

    def exit(self):
        return "Exiting shell..."

    def get_current_path(self):
        return self.cwd


# Основной цикл эмулятора командной строки
if __name__ == "__main__":
    zip_path = "vfs.zip"  # ZIP-архив
    emulator = ShellEmulator(zip_path)  # Инициализация эмулятора

    while True:
        current_path = emulator.get_current_path()
        print(f"vfs{current_path} $ ", end="")

        command = input().strip()

        if command == "exit":
            print(emulator.run_command(command))
            break

        output = emulator.run_command(command)
        print(output)
