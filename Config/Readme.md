# Работы по конфигурационному управлению
## Индивидуальное задание

Разработать эмулятор для языка оболочки ОС. Необходимо сделать работу эмулятора как можно более похожей на сеанс shell в UNIX-подобной ОС.
Эмулятор должен запускаться из реальной командной строки, а файл с виртуальной файловой системой не нужно распаковывать у пользователя.
Эмулятор принимает образ виртуальной файловой системы в виде файла формата zip. Эмулятор должен работать в режиме CLI.

### Ключами командной строки задаются:

  • Имя пользователя для показа в приглашении к вводу.
  
  • Имя компьютера для показа в приглашении к вводу.
  
  • Путь к архиву виртуальной файловой системы.
  
  • Путь к лог-файлу.
  
  • Путь к стартовому скрипту.
  
Лог-файл имеет формат csv и содержит все действия во время последнего сеанса работы с эмулятором. Для каждого действия указаны дата и время. Для каждого действия указан пользователь.
Стартовый скрипт служит для начального выполнения заданного списка команд из файла.

#### Необходимо поддержать в эмуляторе команды ls, cd и exit, а также следующие команды:

1. mkdir.
2. find.
3. tail.

Все функции эмулятора должны быть покрыты тестами, а для каждой из поддерживаемых команд необходимо написать 2 теста.

## Успешное выполнение тестов
![image](https://github.com/user-attachments/assets/045d3f50-b0ae-4f9e-b79c-d2914a6e11a1)

## Тестирование функций 
![image](https://github.com/user-attachments/assets/e333c3b1-ed96-456f-ad42-3c5cccc5eaf6)

![image](https://github.com/user-attachments/assets/e53012a8-541c-4b02-aa33-72b4aff490cd)

![image](https://github.com/user-attachments/assets/eca5ab23-09cb-4b77-9109-5332391dc256)

![image](https://github.com/user-attachments/assets/8d678adf-7e53-4773-9e13-4358cb3860d4)

![image](https://github.com/user-attachments/assets/6ed3792e-a877-474a-b5af-0434f6f1f454)

![image](https://github.com/user-attachments/assets/ad93e01b-c085-4b41-b97e-c5f63d947a81)

![image](https://github.com/user-attachments/assets/8e08bb81-f339-4267-84ef-1cdd41e4c84b)

<div id="header" align="center">
  <img src="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExb2h0anFyeHZyaHI1anljYWdkYjl3cG56Z3UxNGhzZDhocnZwZHZ6dyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/YITvqkRzjBb2KRklUw/giphy-downsized-large.gif" width="200"/>
</div>
