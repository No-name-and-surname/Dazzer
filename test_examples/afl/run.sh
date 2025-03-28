#!/bin/bash
# Компиляция с инструментацией AFL
afl-gcc -o target target.c -ljson-c

# Запуск фаззинга
afl-fuzz -i input_testcases -o output_dir ./target @@
