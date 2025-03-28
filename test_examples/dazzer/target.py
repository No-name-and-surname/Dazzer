# target.py
import json

def parse_json(data):
    try:
        result = json.loads(data)
        return True
    except json.JSONDecodeError:
        return False

# Функция-мишень для Dazzer
def target(input_data):
    return parse_json(input_data)
