
## <a id="title0">Dazzer</a>

Dazzer - это мутационный фаззер с открытым исходным кодом

![Image alt](https://github.com/No-name-and-surname/imagere/raw/main/pix.png)

## <a id="title1">Как работает?</a>

Мой фаззер является мутационным, следовательно, он работает за счет преобразования изначальных входных данных с помощью одного из мутационных алгоритмов. 
Состоит фаззер из 3 частей:
   * Калибратор ([`calibrator.py`](calibrator.py)) - главный модуль по работе с целью. Он занимается "общением" с ней, сбором покрытия, сохранением тесткейсов.
   * Мутатор ([`mutator.py`](mutator.py)) - модуль состоящий из мутационных алгоритмов. На данный момент реализованы: Xor, Change_length, Change_symbol, Interesting, Dict.
   * Основной блок ([`main.py`](main.py)) - самый главный модуль. В нем инициализируются потоки, считаются вероятности мутаций, отображается статистика.
Помимо них, так же есть:
   * Конфигурационный файл ([`config.py`](config.py)) - файл через который настраивается фаззер (подробнее см. [тут](#title3))

Приведу несколько скриншотов Dazzer:

![Image alt](https://github.com/user-attachments/assets/76ad5a97-2905-48c7-9acd-77dd7bfc7bd3)

![Image alt](https://github.com/No-name-and-surname/imagere/blob/main/Screenshot%20from%202025-03-16%2016-20-54.png)


## <a id="title2">Установка</a>

Установить Dazzer не сложно, достаточно просто выполнить следующие команды:

### Debian/Ubuntu

```
   git clone git@github.com:No-name-and-surname/Dazzer.git
   cd Dazzer

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


## <a id="title3">Get started</a>

Firstly, you should pay attention to  `config.py`  file.
It contains a lot variables: 
    * FUZZ - constant variable, which one should be inserted in place of the element specifically that you want to fuzz separately from other elements in the initially specified test. (args) 
    * args - a list there should be inserted initial test input. ❗IMPORTANT❗ if you'll set less or more input data than the program requires, the fuzzer won't work.
    * file_name - here should be inserted the name of programm you want fuzz. By default it is  `Test_examples/trees`. (one of the test programms)
    * output_file - a file in which the results are saved after the program is execute. By default it is  `output.txt`, but you can create your own file.
    * dict_name - by default it is equal to the pre-downloaded dictionary. But you can download yours and change it.
   
After you've finished previous part, you should just run:

```
   python3 main.py
```
Then just follow the instructions
After Dazzer finish you should look into output_file

Some results:

![Image alt](https://github.com/No-name-and-surname/imagere/raw/main/Screenshot%20from%202024-07-30%2014-53-03.png)

## 
                              
