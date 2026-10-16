#!/usr/bin/env python3
"""Load an existing profile's send environment, then exec official hermes send.

No transport implementation, credential copying, network request or retries.
Configuration is profile-private. This agent-readable loader is not a security
boundary; actual credential/mount/provider permissions remain authoritative.
"""
import json
import os
from pathlib import Path
import sys


def send_environment(config, inherited):
    env = dict(inherited)
    token_file = Path(config['telegram_bot_token_file'])
    if not token_file.is_absolute(): raise ValueError('Token reference must be an absolute path')
    token = token_file.read_text().strip()
    if not token or '\n' in token or '\r' in token: raise ValueError('Invalid configured token file')
    home = str(config['telegram_home_channel']).strip()
    if not home: raise ValueError('Missing configured Telegram home channel')
    env['TELEGRAM_BOT_TOKEN'] = token
    env['TELEGRAM_HOME_CHANNEL'] = home
    # The native CLI may load dotenv afterward. Profile operators must ensure
    # it doesn't contain conflicting/stale credentials; never silently add any.
    return env


def main():
    try:
        home = Path(os.environ.get('HERMES_HOME', str(Path.home()/'.hermes')))
        config = json.loads((home/'native-messaging.json').read_text())
        cli = Path(config['hermes_executable'])
        if not cli.is_absolute() or not cli.is_file(): raise ValueError('Invalid native CLI path')
        env = send_environment(config, os.environ)
        os.execve(str(cli), [str(cli), 'send', *sys.argv[1:]], env)
    except (OSError, ValueError, KeyError) as exc:
        # Do not log token contents, argv or the environment on failure.
        print(json.dumps({'success': False, 'error': 'Native send environment unavailable',
                          'error_type': type(exc).__name__}), file=sys.stderr)
        raise SystemExit(2)


if __name__ == '__main__': main()
