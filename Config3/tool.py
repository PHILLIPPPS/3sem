import re
import sys
import toml

# Класс для обработки синтаксических ошибок
class SyntaxError(Exception):
    pass


# Лексер: разбиение входного текста на токены
def lexer(input_text):
    token_specification = [
        ('MCOMMENT_START', r'\(comment'),  # Начало многострочного комментария
        ('MCOMMENT_END', r'\)'),  # Конец многострочного комментария
        ('ARRAY_START', r'<<'),  # Начало массива
        ('ARRAY_END', r'>>'),  # Конец массива
        ('COMMA', r','),  # Запятая
        ('NAME', r'[a-zA-Z][_a-zA-Z0-9]*'),  # Имена
        ('NUMBER', r'\d+'),  # Числа
        ('STRING', r"'[^']*'"),  # Строки
        ('CONST_DECL', r':'),  # Объявление константы
        ('EXPR_START', r'\?\['),  # Начало выражения
        ('EXPR_END', r'\]'),  # Конец выражения
        ('DICT_START', r'\['),  # Открывающая скобка словаря
        ('DICT_KEY', r'[a-zA-Z][_a-zA-Z0-9]*'),  # Ключ словаря
        ('DICT_VALUE', r"'[^']*'"),  # Значение словаря
        ('DICT_END', r'\]'),  # Закрывающая скобка словаря
        ('OPERATOR', r'[+\-*/]'),  # Операторы
        ('FUNC', r'len'),  # Функция len
        ('COMMENT', r'%.*'),  # Однострочный комментарий
        ('SKIP', r'[ \t\n]+'),  # Пропуски
        ('MISMATCH', r'.'),  # Любой другой символ
    ]
    tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in token_specification)
    tokens = []
    in_multiline_comment = False
    line_number = 1

    for mo in re.finditer(tok_regex, input_text):
        kind = mo.lastgroup
        value = mo.group()

        if kind == 'SKIP':
            line_number += value.count('\n')
            continue

        if in_multiline_comment:
            if kind == 'MCOMMENT_END':
                in_multiline_comment = False
            continue

        if kind == 'MCOMMENT_START':
            in_multiline_comment = True
            continue

        if kind == 'COMMENT':
            continue  # Игнорируем однострочные комментарии

        if kind == 'MISMATCH':
            raise SyntaxError(f'Unexpected character: {value} at line {line_number}')

        tokens.append((kind, value))

    if in_multiline_comment:
        raise SyntaxError('Unclosed multi-line comment. Ensure every "(comment" has a closing ")".')

    return tokens


def parse(tokens):
    config = {}
    index = 0

    def parse_value():
        nonlocal index
        if index >= len(tokens):
            raise SyntaxError('Unexpected end of input')
        kind, value = tokens[index]
        if kind == 'NUMBER':
            index += 1
            return int(value)
        elif kind == 'STRING':
            index += 1
            return value.strip("'")
        elif kind == 'ARRAY_START':
            return parse_array()
        elif kind == 'DICT_START':
            return parse_dict()
        elif kind == 'EXPR_START':
            return parse_expression()
        else:
            raise SyntaxError(f'Unexpected value: {value}')

    def parse_dict():
        nonlocal index
        dictionary = {}
        if tokens[index][0] != 'DICT_START':
            raise SyntaxError('Expected DICT_START')
        index += 1  # Пропустить '['

        while index < len(tokens) and tokens[index][0] != 'EXPR_END':  # Используйте правильный конец
            if tokens[index][0] == 'NAME':
                key = tokens[index][1]
                index += 1
                if tokens[index][0] != 'DICT_START':
                    raise SyntaxError('Expected "[" after key')
                index += 1  # Пропустить '['
                if tokens[index][0] != 'STRING':
                    raise SyntaxError('Expected STRING value for dictionary')
                value = tokens[index][1].strip("'")
                index += 1
                if tokens[index][0] != 'EXPR_END':
                    raise SyntaxError('Expected "]" to close key-value pair')
                index += 1  # Пропустить ']'
                dictionary[key] = value
            elif tokens[index][0] == 'SKIP':
                index += 1  # Пропустить пробелы
            else:
                raise SyntaxError(f'Unexpected token in dictionary: {tokens[index]}')

        if index >= len(tokens) or tokens[index][0] != 'EXPR_END':
            raise SyntaxError('Expected "]" to close dictionary')
        index += 1  # Пропустить ']'

        return dictionary

    def parse_array():
        nonlocal index
        array = []
        if tokens[index][0] != 'ARRAY_START':
            raise SyntaxError('Expected ARRAY_START')
        index += 1  # Пропустить '<<'
        while index < len(tokens) and tokens[index][0] != 'ARRAY_END':
            if tokens[index][0] == 'COMMA':
                index += 1  # Пропустить запятую
            else:
                array.append(parse_value())  # Рекурсивно обработать элементы массива
        if index >= len(tokens) or tokens[index][0] != 'ARRAY_END':
            raise SyntaxError('Expected ARRAY_END')
        index += 1  # Пропустить '>>'
        return array

    def parse_expression():
        nonlocal index
        if tokens[index][0] != 'EXPR_START':
            raise SyntaxError('Expected EXPR_START')
        index += 1  # Пропустить '?['
        expr = []
        while index < len(tokens) and tokens[index][0] != 'EXPR_END':
            kind, value = tokens[index]
            if kind in ('NUMBER', 'NAME', 'OPERATOR', 'FUNC'):
                expr.append(value)
            else:
                raise SyntaxError(f'Unexpected token in expression: {value}')
            index += 1
        if index >= len(tokens) or tokens[index][0] != 'EXPR_END':
            raise SyntaxError('Expected EXPR_END')
        index += 1  # Пропустить ']'
        return evaluate_expression(expr, config)

    def parse_constant():
        nonlocal index
        if tokens[index][0] != 'NAME':
            raise SyntaxError('Expected a name')
        name = tokens[index][1]
        index += 1
        if tokens[index][0] != 'CONST_DECL':
            raise SyntaxError('Expected ":"')
        index += 1
        value = parse_value()
        config[name] = value

    while index < len(tokens):
        parse_constant()

    return config


# Вычисление выражений
def evaluate_expression(expr, config):
    def to_rpn(expression):
        precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
        output = []
        operators = []
        for token in expression:
            if token.isdigit():
                output.append(int(token))
            elif token in config:
                output.append(config[token])
            elif token == 'len':
                operators.append(token)  # Добавляем функцию как оператор
            elif token in precedence:
                while (operators and operators[-1] in precedence and
                       precedence[token] <= precedence[operators[-1]]):
                    output.append(operators.pop())
                operators.append(token)
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    output.append(operators.pop())
                operators.pop()  # Убираем '('
        while operators:
            output.append(operators.pop())
        return output

    def evaluate_rpn(rpn):
        stack = []
        for token in rpn:
            if isinstance(token, int):
                stack.append(token)
            elif isinstance(token, list):  # Если это массив (например, `skills`)
                stack.append(token)
            elif token == 'len':  # Обрабатываем функцию len
                a = stack.pop()
                stack.append(len(a))
            elif token in '+-*/':
                b = stack.pop()
                a = stack.pop()
                if token == '+':
                    stack.append(a + b)
                elif token == '-':
                    stack.append(a - b)
                elif token == '*':
                    stack.append(a * b)
                elif token == '/':
                    if b == 0:
                        raise SyntaxError("Division by zero")
                    stack.append(a / b)
            else:
                raise SyntaxError(f"Unknown token in RPN: '{token}'")
        if len(stack) != 1:
            raise SyntaxError(f"Invalid RPN: leftover stack {stack}")
        return stack[0]
    rpn = to_rpn(expr)
    return evaluate_rpn(rpn)


# Преобразование в TOML
def to_toml(config):
    toml_string = toml.dumps(config)
    # Удаление лишних запятых в массивах, если они есть
    toml_string = re.sub(r',\s*\]', ']', toml_string)
    toml_string = re.sub(r',\s*\}', '}', toml_string)
    return toml_string

def main():
    if len(sys.argv) > 1:
        # Открытие файла с явной кодировкой
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            input_text = f.read()
    else:
        # Чтение из стандартного ввода
        input_text = sys.stdin.read()

    try:
        tokens = lexer(input_text)
        config = parse(tokens)
        print(to_toml(config))
    except SyntaxError as e:
        print(f"Syntax error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()