#!/usr/bin/env python3
"""Restore this project's VSCodium folder override after a Renku image rebuild.

Uses authentication from the installed Renku skill helper. Does not launch,
stop, or rebuild sessions. Run with --dry-run to preview the command.
"""
import argparse
import copy
import importlib.util
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launcher', default='01M7A3QW52ANYXERJJCX69M6R6')
    parser.add_argument('--helper', type=Path, default=Path.home() / '.agents/skills/renku/scripts/renku_agent.py')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('renku_helper', args.helper)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.assert_not_admin()
    path = f'/session_launchers/{args.launcher}'
    before = helper.http_json('GET', path)
    environment = before['environment']
    if environment.get('environment_image_source') != 'build' or environment.get('build_parameters', {}).get('frontend_variant') != 'vscodium':
        raise SystemExit('Expected a built-from-code VSCodium launcher; nothing changed.')
    script = '''set -eo pipefail
source "$HOME/.bashrc"
data_dir="$RENKU_MOUNT_DIR/.vscode"
mkdir -p "$data_dir/extensions" || data_dir="$RENKU_MOUNT_DIR/.vscode_"
exec codium-server --server-base-path "${RENKU_BASE_URL_PATH%/}" --host "${RENKU_SESSION_IP:-0.0.0.0}" --port "${RENKU_SESSION_PORT:-8888}" --extensions-dir "$data_dir/extensions" --server-data-dir "$data_dir" --without-connection-token --accept-server-license-terms --telemetry-level off --default-folder /home/renku/work/ogb-hiraku
'''
    command = ['/cnb/lifecycle/launcher', '--']
    command_args = ['tini', '-g', '--', 'bash', '-c', script]
    payload = {'environment': {'build_parameters': environment['build_parameters'], 'command': command, 'args': command_args}}
    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return
    if environment.get('command') != command or environment.get('args') != command_args:
        helper.http_json('PATCH', path, body=payload)
    after = helper.http_json('GET', path)
    if after['environment'].get('command') != command or after['environment'].get('args') != command_args:
        raise SystemExit('API readback did not retain the entrypoint override.')
    def without_entrypoint(launcher):
        result = copy.deepcopy(launcher)
        result['environment'].pop('command', None)
        result['environment'].pop('args', None)
        return result
    if without_entrypoint(before) != without_entrypoint(after):
        raise SystemExit('Unexpected change outside command/args detected; inspect the launcher.')
    print('Verified: CNB entrypoint preserved; VSCodium default folder is /home/renku/work/ogb-hiraku.')
    print('All other launcher fields are unchanged. No sessions were started or stopped.')


if __name__ == '__main__':
    main()
