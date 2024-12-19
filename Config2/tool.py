import os
import csv
import datetime
import argparse
import zlib

def load_config(config_path):
    """Загружает конфигурацию из CSV-файла."""
    config = {}
    with open(config_path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 2:
                key, value = row
                config[key.strip()] = value.strip()
    return config

def get_branches(repo_path):
    """Получает список всех веток репозитория."""
    heads_path = os.path.join(repo_path, '.git', 'refs', 'heads')
    return [branch for branch in os.listdir(heads_path) if os.path.isfile(os.path.join(heads_path, branch))]

def read_git_object(repo_path, object_hash):
    """Читает и разжимает объект Git по его хэшу."""
    object_path = os.path.join(repo_path, '.git', 'objects', object_hash[:2], object_hash[2:])
    if not os.path.exists(object_path):
        return None
    with open(object_path, 'rb') as f:
        compressed_data = f.read()
    try:
        return zlib.decompress(compressed_data)
    except zlib.error as e:
        print(f"Ошибка разжатия данных для объекта {object_hash}: {e}")
        return None

def parse_commit_object(raw_data):
    """Парсит объект коммита из сырых данных."""
    raw_text = raw_data.decode(errors='replace')
    lines = raw_text.split('\n')
    commit_info = {
        'tree': None,
        'parents': [],
        'author': None,
        'date': None,
        'message': ''
    }
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('tree '):
            commit_info['tree'] = line.split()[1]
        elif line.startswith('parent '):
            commit_info['parents'].append(line.split()[1])
        elif line.startswith('author '):
            try:
                parts = line.split()
                commit_info['author'] = ' '.join(parts[1:-2])  # Имя автора
                commit_info['date'] = int(parts[-2])  # UNIX-временная метка
            except (ValueError, IndexError):
                print(f"Ошибка при обработке строки author: {line}")
                commit_info['author'] = None
                commit_info['date'] = None
        elif line == '':
            commit_info['message'] = '\n'.join(lines[i + 1:]).strip()
            break
        i += 1
    return commit_info

def get_commit_history(repo_path, tag_commit_hash):
    """Собирает историю коммитов начиная с указанного хэша."""
    all_commits = {}
    commit_hash = tag_commit_hash

    while commit_hash:
        if commit_hash in all_commits:
            break
        raw_data = read_git_object(repo_path, commit_hash)
        if raw_data is None:
            break
        commit_info = parse_commit_object(raw_data)
        if commit_info['date'] is None:
            print(f"Пропускаем коммит {commit_hash}: отсутствует или некорректная дата.\nCommit Info: {commit_info}")
            break
        # Не добавляем дату и время в результат
        all_commits[commit_hash] = {
            'hash': commit_hash,
            'author': commit_info['author'],
            'message': commit_info['message'],
            'parents': commit_info['parents'],
        }
        commit_hash = commit_info['parents'][0] if commit_info['parents'] else None

    return all_commits


def build_dependency_graph(repo_path, commits):
    """Формирует граф зависимостей на основе данных о коммитах."""
    graph = []
    unique_nodes = set()

    for commit_hash, commit_data in commits.items():
        # Добавляем хэш коммита
        if commit_hash not in unique_nodes:
            graph.append(f'"{commit_hash}" : commit')
            unique_nodes.add(commit_hash)

        # Читаем дерево для каждого коммита
        tree_data = read_git_object(repo_path, commit_hash)
        if tree_data:
            tree_lines = tree_data.decode(errors='replace').split('\n')
            for line in tree_lines:
                parts = line.strip().split()
                if len(parts) > 1 and parts[-1]:  # Проверка валидности имени файла
                    file_path = parts[-1]
                    # Фильтруем подозрительные или ненужные узлы
                    if "+0300" not in file_path and not file_path.startswith(' '):
                        if file_path not in unique_nodes:
                            graph.append(f'"{file_path}" : file/folder')
                            unique_nodes.add(file_path)
                        graph.append(f'"{commit_hash}" --> "{file_path}" : modifies')

    return graph

def group_files_in_packages(graph):
    """Группирует файлы и папки в пакеты."""
    grouped = {}
    for line in graph:
        if " --> " in line:
            commit, file_path = line.split(" --> ")
            file_path = file_path.split(" :")[0]  # Убираем часть после :
            folder, file = os.path.split(file_path.strip('"'))
            folder = folder.strip()  # Убираем лишние пробелы
            if folder:  # Пропускаем пустые папки
                if folder not in grouped:
                    grouped[folder] = []
                if file not in grouped[folder]:
                    grouped[folder].append(file)

    plantuml_code = ["@startuml", "left to right direction"]
    for folder, files in grouped.items():
        plantuml_code.append(f'package "{folder}" {{')
        for file in files:
            plantuml_code.append(f'"{folder}/{file}" : file')  # Корректное форматирование
        plantuml_code.append("}")

    # Добавляем исходные связи
    plantuml_code.extend(graph)
    plantuml_code.append("@enduml")
    return "\n".join(plantuml_code)

def generate_plantuml_code(graph):
    """Генерирует код PlantUML для графа."""
    plantuml_code = ["@startuml"]
    plantuml_code.extend(graph)  # Просто добавляем связи коммитов и файлов
    plantuml_code.append("@enduml")
    return '\n'.join(plantuml_code)

def save_to_file(content, file_path):
    """Сохраняет содержимое в файл."""
    with open(file_path, 'w') as file:
        file.write(content)

def visualize_graph(plantuml_tool_path, file_path):
    """Открывает граф с помощью PlantUML."""
    os.system(f'java -jar {plantuml_tool_path} {file_path}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Построение графа зависимостей для коммитов Git.")
    parser.add_argument("--config", required=True, help="Путь к конфигурационному файлу CSV.")
    args = parser.parse_args()

    # Загружаем конфигурацию
    config = load_config(args.config)

    # Извлекаем параметры из конфигурации
    plantuml_tool = config.get("plantuml_tool")
    repo_path = config.get("repo_path")
    tag_name = config.get("tag_name")
    output_path = config.get("output_path", "output.puml")

    if not (plantuml_tool and repo_path and tag_name):
        raise ValueError("Конфигурационный файл должен содержать параметры 'plantuml_tool', 'repo_path' и 'tag_name'.")

    # Получаем хэш коммита тега
    tag_ref_path = os.path.join(repo_path, ".git", "refs", "tags", tag_name)
    if not os.path.exists(tag_ref_path):
        raise ValueError(f"Тег {tag_name} не найден в репозитории.")

    with open(tag_ref_path, 'r') as f:
        tag_commit_hash = f.read().strip()

    # Получаем историю коммитов
    commit_history = get_commit_history(repo_path, tag_commit_hash)

    # Строим граф зависимостей
    graph = build_dependency_graph(repo_path, commit_history)

    # Группируем файлы в пакеты
    plantuml_code = group_files_in_packages(graph)

    # Сохраняем результат
    save_to_file(plantuml_code, output_path)

    # Визуализируем граф
    visualize_graph(plantuml_tool, output_path)

