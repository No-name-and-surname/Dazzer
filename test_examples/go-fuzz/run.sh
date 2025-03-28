#!/bin/bash
# Подготовка
go get -u github.com/dvyukov/go-fuzz/...
go-fuzz-build

# Запуск фаззинга
go-fuzz -bin=./json-fuzz.zip -workdir=fuzz_output
