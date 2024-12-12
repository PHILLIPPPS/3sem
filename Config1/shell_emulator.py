import zipfile
import os
import csv
import sys
from tempfile import TemporaryDirectory
from datetime import datetime

class ShellEmulator:
    COLORS = {"directory": "\033[36m", "txt_file": "\033[31m",  "csv_file": "\033[32m", "reset": "\033[0m"}

    def __init__(self, zip_path, log_file, user):
        self.zip_path = zip_path
        self.log_file = log_file
        self.user = user
        self.temp_dir = TemporaryDirectory()
        self.cwd = "/"
        self.archive = zipfile.ZipFile(zip_path, 'a')

        with open(log_file, mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Date", "Time", "User", "Command", "Result"])

    def __del__(self):
        self.archive.close()
        self.temp_dir.cleanup()

    def log_command(self, command, result):
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")
        with open(self.log_file, mode='a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([date, time, self.user, command, result])

    def run_command(self, command):
        parts = command.split()
        cmd = parts[0] if parts else ""
        args = parts[1:]

        if cmd == "ls":
            result = self.ls(args)
        elif cmd == "cd":
            result = self.cd(args[0] if args else "/")
        elif cmd == "exit":
            result = self.exit()
        elif cmd == "mkdir":
            result = self.mkdir(args[0] if args else "")
        elif cmd == "find":
            result = self.find(args)
        elif cmd == "tail":
            result = self.tail(args)
        else:
            result = "Command not found"

        self.log_command(command, result)
        return result
    def ls(self, args):
        detailed = "-l" in args
        entries = self.archive.namelist()

        dirs = set()
        files = {}

        for entry in entries:
            if entry.startswith(self.cwd.strip("/")):
                rel_path = entry[len(self.cwd.strip("/")):].strip("/")
                if "/" in rel_path:
                    dirs.add(rel_path.split("/")[0])
                elif rel_path:
                    files[rel_path] = os.path.splitext(rel_path)[1]

        if detailed:
            result = []
            for entry in sorted(dirs | files.keys()):
                if entry in dirs:
                    result.append(f"{self.COLORS['directory']}drwxr-xr-x 0 {entry}{self.COLORS['reset']}")
                else:
                    file_type = files[entry]
                    color = (
                        self.COLORS['txt_file'] if file_type == ".txt"
                        else self.COLORS['csv_file'] if file_type == ".csv"
                        else self.COLORS['reset']
                    )
                    info = next((i for i in self.archive.infolist() if i.filename == f"{self.cwd.strip('/')}/{entry}"), None)
                    size = info.file_size if info else 0
                    result.append(f"{color}-rw-r--r-- {size} {entry}{self.COLORS['reset']}")
            return "\n".join(result)
        else:
            output = []
            for entry in sorted(dirs | files.keys()):
                if entry in dirs:
                    output.append(f"{self.COLORS['directory']}{entry}{self.COLORS['reset']}")
                else:
                    file_type = files[entry]
                    color = (
                        self.COLORS['txt_file'] if file_type == ".txt"
                        else self.COLORS['csv_file'] if file_type == ".csv"
                        else self.COLORS['reset']
                    )
                    output.append(f"{color}{entry}{self.COLORS['reset']}")
            return "\n".join(output)

    def cd(self, path):
        if not path:
            path = "/"

        if path == "..":
            if self.cwd == "/":
                return "Already at root directory"

            new_path = '/'.join(self.cwd.strip('/').split('/')[:-1])
            if new_path == "":
                new_path = "/"
            self.cwd = "/" + new_path.lstrip("/")
            return ""

        new_path = os.path.normpath(os.path.join(self.cwd.strip("/"), path)).replace("\\", "/")

        entries = self.archive.namelist()
        matched_dirs = [entry for entry in entries if entry.startswith(new_path + "/")]

        if matched_dirs:
            self.cwd = "/" + new_path.lstrip("/")
            return ""
        else:
            return f"No such directory: {path}"

    def mkdir(self, path):
        directory = os.path.normpath(os.path.join(self.cwd.strip("/"), path)).strip("/") + "/"

        if any(entry == directory or entry.startswith(directory) for entry in self.archive.namelist()):
            return f"Directory '{path}' already exists"

        self.archive.writestr(directory, "")
        return f"Directory '{path}' created"

    def find(self, args):
        if not args:
            return "Error: find command requires a search term"

        search_term = args[0]
        matches = [entry for entry in self.archive.namelist() if search_term in entry]
        return "\n".join(matches) if matches else f"No files or directories found matching '{search_term}'"

    def tail(self, args):
        if not args:
            return "Error: tail command requires a file path"

        lines = 10
        path = None

        try:
            if "-n" in args:
                n_index = args.index("-n")
                lines = int(args[n_index + 1])
                path = args[n_index + 2] if len(args) > n_index + 2 else None
            else:
                path = args[0]
        except (ValueError, IndexError):
            return "Error: invalid usage of -n"

        if path not in self.archive.namelist():
            return f"No such file: {path}"

        try:
            with self.archive.open(path) as f:
                lines_content = f.readlines()[-lines:]
            return ''.join(line.decode('utf-8') for line in lines_content)
        except Exception as e:
            return f"Error: {str(e)}"

    def exit(self):
        return "Exiting shell..."

    def get_current_path(self):
        return self.cwd

def main():
    if len(sys.argv) < 5:
        print("Usage: python shell_emulator.py user localhost vfs.zip log.csv [script.sh]")
        return

    user = sys.argv[1]
    zip_path = sys.argv[3]
    log_file = sys.argv[4]
    script_args = sys.argv[5:] if len(sys.argv) > 5 else []

    emulator = ShellEmulator(zip_path, log_file, user)

    if script_args:
        script_file = script_args[0]
        with open(script_file, 'r') as f:
            for line in f:
                command = line.strip()
                if command:
                    current_path = emulator.get_current_path()
                    print(f"vfs{current_path} $ {command}")
                    output = emulator.run_command(command)
                    print(output)

    while True:
        current_path = emulator.get_current_path()
        print(f"vfs{current_path} $ ", end="")
        command = input().strip()

        if command == "exit":
            print(emulator.run_command(command))
            break

        output = emulator.run_command(command)
        print(output)

if __name__ == "__main__":
    main()
