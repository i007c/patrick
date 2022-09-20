import json
import sys
from pathlib import Path
from time import sleep

from httpx import Client

from utils import BASE_DIR, SECRETS, ZN, get_message_content, iosafe
from utils import print_json


BASE_URL = 'https://discord.com/api/v10'
HEADERS = {'Authorization': 'Bot ' + SECRETS['TOKEN']}
client = Client(base_url=BASE_URL, headers=HEADERS)

KNOWN_GUILDS = {}

CHANNELS = [
    875474473640394833,
    865323958802972682
]


def verify_channel(data: dict) -> bool:
    sleep(0.25)

    cid = data['id']
    print(cid, data['name'], end=' ')

    response = client.get(f'/channels/{cid}/messages', params={'limit': 1})

    if response.status_code == 403:
        print('❌')
        return False

    if response.status_code == 429:
        timeout = response.json()['retry_after']
        print(f'\n--- timeout: {timeout} ---')
        sleep(timeout)
        return verify_channel(before=data)

    print('✔')
    return True


def get_avialable_channels():
    data = {}

    user_info = client.get(f'/users/@me').json()
    data['bot'] = user_info['username']

    guilds_info = client.get('/users/@me/guilds').json()
    guilds = list(map(lambda g: (g['id'], g['name']), guilds_info))
    data['guilds'] = guilds

    guilds_len = len(guilds)

    for gidx, (gid, gname) in enumerate(guilds):
        gdx = ZN(gidx + 1, guilds_len)
        print(f'------- [{gdx}/{guilds_len}] {gname} -------')

        avialable_channels = []

        channels = client.get(f'/guilds/{gid}/channels').json()
        channels = list(filter(lambda c: c['type'] == 0, channels))
        ch_len = len(channels)

        for idx, c in enumerate(channels):
            cdx = ZN(idx + 1, ch_len)
            print(f'[{cdx}/{ch_len}] ', end='')

            if verify_channel(c):
                avialable_channels.append((c['id'], c['name']))

        data[f'X-{gname}'] = avialable_channels

    with open(BASE_DIR / 'avialable-channels.json', 'w') as f:
        json.dump(data, f, indent=4)


##################################################


def messages_getter(cid):

    def decorator(before=None):
        # sleep(0.27)
        params = {'limit': 100}

        if before:
            params['before'] = before

        response = client.get(f'/channels/{cid}/messages', params=params)

        if response.status_code == 429:
            timeout = response.json()['retry_after']
            print(f'timeout: {timeout}')
            sleep(timeout)
            return decorator(before)

        return response

    return decorator


def guild_name_by_id(gid):
    global KNOWN_GUILDS
    gid = str(gid)
    name = KNOWN_GUILDS.get(gid)

    if name:
        return name

    response = client.get(f'/guilds/{gid}').json()

    name = response['name']
    KNOWN_GUILDS[gid] = name

    return name


def get_channel_content(cid):
    channel = client.get(f'/channels/{cid}').json()
    gname = guild_name_by_id(channel['guild_id'])
    dir_name = BASE_DIR / 'guilds' / iosafe(gname)
    filename = dir_name / (channel['name'] + '.json')

    if not dir_name.exists():
        dir_name.mkdir(parents=True)

    messages = []
    get_messages = messages_getter(channel['id'])

    response = get_messages()
    n = 0

    while True:
        data = response.json()

        if not data:
            break

        messages += list(map(get_message_content, data))

        for index, msg in enumerate(data):
            print(
                f'[{(n * 100)+(index + 1)}] {msg["author"]["username"]}: '
                f'{msg["timestamp"]}'
            )

        n += 1
        response = get_messages(data[-1]['id'])

        if response.status_code != 200:
            print(response.status_code)
            print(response.text)
            break

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(messages, f, indent=True)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'a':
        get_avialable_channels()
    else:
        for cid in CHANNELS:
            get_channel_content(cid)


if __name__ == '__main__':
    main()
