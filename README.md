
## <a id="title0">Dazzer</a>

Dazzer - это мутационный фаззер с открытым исходным кодом

![Image alt](https://github.com/No-name-and-surname/imagere/raw/main/pix.png)

## <a id="title1">Как это работает?</a>

Мой фаззер является мутационным, следовательно, он работает за счет преобразования изначальных входных данных с помощью одного из мутационных алгоритмов. 
Состоит фаззер из 3 частей:
   * Калибратор ([`calibrator.py`](calibrator.py)) - главный модуль по работе с целью. Он занимается "общением" с ней, сбором покрытия, сохранением тесткейсов.
   * Мутатор ([`mutator.py`](mutator.py)) - модуль состоящий из мутационных алгоритмов. На данный момент реализованы: Xor, Change_length, Change_symbol, Interesting, Dict.
   * Основной блок ([`main.py`](main.py)) - самый главный модуль. В нем инициализируются потоки, считаются вероятности мутаций, отображается статистика.
Помимо них, так же есть:
   * Конфигурационный файл ([`config.py`](config.py)) - файл через который настраивается фаззер (подробнее см. [тут](#title3))

Приведу несколько скриншотов Dazzer:

![Image alt](https://github.com/user-attachments/assets/76ad5a97-2905-48c7-9acd-77dd7bfc7bd3)

![Image alt](![изображение](https://github.com/user-attachments/assets/9cbfa249-8b0b-456e-a781-96fda2e59d4e)


## <a id="title2">Установка</a>

Установить Dazzer не сложно, достаточно просто выполнить следующие команды:

### Debian/Ubuntu

```
   git clone git@github.com:No-name-and-surname/Dazzer.git
   cd Dazzer
   sudo apt-get update
   sudo apt-get install -y gcc g++ lcov gcovr valgrind strace linux-tools-common linux-tools-generic
   pip install -r requirements.txt
```

### Fedora

```
   git clone git@github.com:No-name-and-surname/Dazzer.git
   cd Dazzer
   sudo dnf install -y gcc gcc-c++ gcovr lcov valgrind strace perf
   pip install -r requirements.txt
```

### Arch Linux

```
   git clone git@github.com:No-name-and-surname/Dazzer.git
   cd Dazzer
   sudo pacman -Sy gcc gcovr lcov valgrind strace perf
   pip install -r requirements.txt
```

### NixOS

```
   git clone git@github.com:No-name-and-surname/Dazzer.git
   cd Dazzer
   nix-shell -p gcc gcovr lcov valgrind strace linuxPackages.perf python3 python3Packages.pip
   pip install -r requirements.txt
```

### Windows (в wsl)

```
   pacman -Syu
   pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-lcov
   git clone git@github.com:No-name-and-surname/Dazzer.git
   cd Dazzer
   pip install -r requirements.txt
```


## <a id="title3">Быстрый старт</a>

Первым делом вам стоит обратить внимание на файл [`config.py`](config.py).
Он содержит основные настройки фаззера. Ниже приведено мини-описание каждого параметра:

### Основные параметры
  * FUZZ - Специальный маркер, используемый в аргументах, который указывает, где должна происходить мутация входных данных. При обнаружении этой строки в аргументах она заменяется на мутированные данные.
  * __FUZZING_TYPE (тип фаззинга):__
    * White - доступ к исходному коду
    * Black - без доступа к исходному коду, по сети
    * Gray - без доступа к исходному коду, только к бинарному файлу
  * __Директории и пути к файлам:__
    * BASE_DIR - Абсолютный путь к директории, где расположен скрипт.
    * TEST_DIR - Путь к директории с тестовыми примерами.
    * OUT_DIR - Путь к директории для сохранения результатов работы.
    * file_name - Путь к тестируемому исполняемому файлу.
    * source_file - Путь к исходному коду тестируемой программы (для режима White Box).
### Настройки тестирования
  * args - Список аргументов командной строки для передачи тестируемой программе.
  * TARGET_HOST - Хост для тестирования по сети (для режима Black Box).
  * TARGET_PORT - Порт для тестирования по сети (для режима Black Box).
  * TIMEOUT - Максимальное время ожидания ответа от программы в секундах.
### Сохранение результатов
  * output_file - Имя файла для сохранения вывода фаззера.
  * dict_name - Имя файла словаря, из которого берутся интересные входные данные.
  * Corpus_dir - Директория для сохранения найденных интересных тестовых примеров (корпуса).
### Производительность
  * NUM_THREADS - Количество параллельных потоков для одновременного выполнения фаззинга. Увеличение этого значения может повысить производительность на многоядерных системах.

После того, как вы закончите настройку, запустите:

```
   python3 main.py
```

Дальше просто следуйте инструкциям указаным на экране

Пример результатов:

![Image alt](https://github.com/No-name-and-surname/imagere/blob/main/Screenshot%20from%202025-03-16%2016-22-34.png)

На скриншоте указан результат работы фаззера в 8 потоков. Что бы посмотреть тесты которые обрабатывались в каждом из них, достаточно просто открыть папку tests-Thread-n__fuzzing_thread_,  где n - номер потока. Пример теста:

![Image alt](https://github.com/user-attachments/assets/3d3dc00e-7999-4d88-8a5a-c2babd2b70f8)


## 
                              
