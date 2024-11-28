import os
import shutil
import getpass
import stat

class ShellEmulator:
    def __init__(self, vfs_path):
        self.cwd = vfs_path
        self.username = getpass.getuser()
        self.base_dir = os.path.abspath(vfs_path)
        self.cwd = self.base_dir

    def run_command(self, command):
        parts = command.split()
        cmd = parts[0]
        args = parts[1:]

        if cmd == "ls":
            return self.ls(args)
        elif cmd == "cd":
            return self.cd(args[0] if args else "")
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
        entries = os.listdir(self.cwd)
        if detailed:
            result = []
            for entry in entries:
                full_path = os.path.join(self.cwd, entry)
                permissions = stat.filemode(os.stat(full_path).st_mode)
                size = os.path.getsize(full_path)
                result.append(f"{permissions} {size} {entry}")
            return "\n".join(result)
        else:
            return "\n".join(entries)

    def cd(self, path):
        if not path:
            path = self.base_dir

        new_path = os.path.abspath(os.path.join(self.cwd, path))
        if not new_path.startswith(self.base_dir):
            return "Error: out of range directory"

        if os.path.isdir(new_path):
            self.cwd = new_path
            return ""
        else:
            return f"No such directory: {path}"

    def exit(self):
        return "Exiting shell..."

    def mkdir(self, path):
        try:
            os.makedirs(os.path.join(self.cwd, path), exist_ok=True)
            return f"Directory '{path}' created"
        except Exception as e:
            return f"Error: {str(e)}"

    def find(self, args):
        if not args:
            return "Error: find command requires a search term"

        search_term = args[0]
        matches = []
        for root, dirs, files in os.walk(self.cwd):
            for name in files + dirs:
                if search_term in name:
                    matches.append(os.path.relpath(os.path.join(root, name), self.base_dir))

        if matches:
            return "\n".join(matches)
        else:
            return f"No files or directories found matching '{search_term}'"

    def tail(self, path, lines=5):
        try:
            file_path = os.path.join(self.cwd, path)
            with open(file_path, 'r') as f:
                lines_content = f.readlines()[-lines:]
            return ''.join(lines_content)
        except Exception as e:
            return f"Error: {str(e)}"

    def get_current_path(self):
        # Преобразуем путь в Unix-формат
        relative_path = os.path.relpath(self.cwd, self.base_dir)
        if relative_path == ".":
            relative_path = "/"  # Если текущий путь - корень, показываем "/"
        else:
            relative_path = "/" + relative_path.replace("\\", "/")
        return relative_path


# Основной цикл эмулятора командной строки
if __name__ == "__main__":
    vfs_path = "vfs"  # Путь к вашей виртуальной файловой системе
    emulator = ShellEmulator(vfs_path)  # Инициализация эмулятора

    while True:
        # Отображаем текущий путь с учетом изменений
        current_path = emulator.get_current_path()
        print(f"vfs{current_path} $ ", end="")

        # Чтение команды от пользователя
        command = input().strip()

        # Выход из эмулятора
        if command == "exit":
            print(emulator.run_command(command))
            break

        # Выполнение команды
        output = emulator.run_command(command)
        print(output)
