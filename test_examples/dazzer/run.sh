#!/bin/bash
# Запуск фаззинга с Dazzer
python main.py --target=target.py --function=target --corpus=json_corpus --output=findings
