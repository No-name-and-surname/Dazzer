#!/bin/bash
# Компиляция с поддержкой LibFuzzer
clang++ -g -O1 -fsanitize=fuzzer,address target.cpp -o json_fuzzer -ljsoncpp

# Запуск фаззинга
./json_fuzzer corpus_dir -max_len=4096
