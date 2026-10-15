import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PLACE_ID = 85419519353403
GAME_URL = 'https://www.roblox.com/games/85419519353403/Egg-Farm-Simulator-Remastered'
STATE_FILE = Path('release_state.json')
WEBHOOK = os.environ.get('DISCORD_WEBHOOK_URL', '').strip()


def get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'RobloxReleaseMonitor/1.0', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def universe_id():
    url = f'https://apis.roblox.com/universes/v1/places/{PLACE_ID}/universe'
    result = get_json(url)
    uid = result.get('universeId')
    if not isinstance(uid, int) or uid <= 0:
        raise ValueError(f'Universe ID missing: {result}')
    return uid


def playable(uid):
    query = urllib.parse.urlencode({'universeIds': str(uid)})
    result = get_json('https://games.roblox.com/v1/games/multiget-playability-status?' + query)
    if not isinstance(result, list):
        raise ValueError(f'Unexpected playability response: {result}')
    record = next((x for x in result if str(x.get('universeId')) == str(uid)), None)
    if not record:
        raise ValueError(f'No matching universe in playability response: {result}')
    # Only explicit affirmative status counts as playable; never infer from player count.
    value = record.get('isPlayable')
    if type(value) is not bool:
        raise ValueError(f'No explicit boolean isPlayable status: {record}')
    return value


def notify():
    if not WEBHOOK:
        raise RuntimeError('DISCORD_WEBHOOK_URL GitHub secret is missing')
    payload = json.dumps({'content': '🥚 **Egg Farm Simulator Remastered is playable!** 🎮\n' + GAME_URL, 'allowed_mentions': {'parse': []}}).encode()
    request = urllib.request.Request(WEBHOOK, data=payload, headers={'Content-Type': 'application/json', 'User-Agent': 'RobloxReleaseMonitor/1.0'}, method='POST')
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status not in (200, 204):
            raise RuntimeError(f'Discord returned HTTP {response.status}')


def main():
    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {'notified': False}
    if state.get('notified'):
        print('Already notified. Nothing to do.')
        return
    uid = universe_id()
    is_playable = playable(uid)
    print(f'Universe {uid}: isPlayable={is_playable}')
    if not is_playable:
        return
    notify()
    STATE_FILE.write_text(json.dumps({'notified': True, 'universeId': uid}, indent=2) + '\n')
    print('Discord notification sent; state saved.')


if __name__ == '__main__':
    try:
        main()
    except (urllib.error.URLError, ValueError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(f'Check failed (no release notification sent): {exc}', file=sys.stderr)
        sys.exit(1)
