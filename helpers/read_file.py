import json
import os


def read_file(path: str):
    with open(path, 'r') as file:
        return file.read()


def read_json(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
