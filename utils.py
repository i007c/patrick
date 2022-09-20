import json
import string
from pathlib import Path

from httpx import Response


IO_CHARS = string.ascii_letters + string.digits + '-_.'


BASE_DIR = Path(__file__).parent

with open(BASE_DIR / 'secrets.json') as f:
    SECRETS = json.load(f)


def print_json(data: dict | str | Response):
    if isinstance(data, str):
        data = json.load(data)
    elif isinstance(data, Response):
        data = data.json()

    print(json.dumps(data, indent=4))


def ZN(number, max):
    return str(number).zfill(len(str(max)))


def iosafe(name: str):
    new_name = ''

    for c in name:
        if c in IO_CHARS:
            new_name += c

        if c == ' ':
            new_name += '_'

    return new_name


def get_message_content(msg: dict):
    return {
        'content': msg['content'],
        'author': msg['author']['username'],
        'attachments': msg['attachments'],
        'embeds': msg['embeds']
    }
