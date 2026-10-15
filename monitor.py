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
    result = get_json(f'https://apis.roblox.com/universes/v1/places/{PLACE_ID}/universe')
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
    if not record or type(record.get('isPlayable')) is not bool:
        raise ValueError(f'No explicit playability status: {result}')
    return record['isPlayable']


def notify(message, ping_everyone=False):
    if not WEBHOOK:
        raise RuntimeError('DISCORD_WEBHOOK_URL GitHub secret is missing')
    payload = json.dumps({
        'content': message,
        'allowed_mentions': {'parse': ['everyone'] if ping_everyone else []},
    }).encode('utf-8')
    req = urllib.request.Request(
        WEBHOOK, data=payload,
        headers={'Content-Type': 'application/json', 'User-Agent': 'RobloxReleaseMonitor/1.0'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        if response.status not in (200, 204):
            raise RuntimeError(f'Discord returned HTTP {response.status}')


def main():
    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {'notified': False}
    if state.get('notified'):
        print('Release alert already sent. Monitoring finished.')
        return

    uid = universe_id()
    is_playable = playable(uid)
    print(f'Universe {uid}: isPlayable={is_playable}')
    if not is_playable:
        notify('🔍 **Egg Farm Simulator Remastered**\n❌ Game is not playable yet.\nNext check: approximately 10 minutes.')
        print('Discord status update sent (no ping).')
        return

    notify('@everyone 🚨 **GAME RELEASED!** 🎉\n🥚 **Egg Farm Simulator Remastered is now playable!**\n' + GAME_URL, ping_everyone=True)
    STATE_FILE.write_text(json.dumps({'notified': True, 'universeId': uid}, indent=2) + '\n')
    print('Discord release alert sent with @everyone; state saved.')


if __name__ == '__main__':
    try:
        main()
    except (urllib.error.URLError, ValueError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(f'Check failed: {exc}', file=sys.stderr)
        sys.exit(1)
