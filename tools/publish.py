"""Export, validate, commit and push one finished update to the portfolio repo."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_REMOTE = 'https://github.com/elena0401bb/elenafbb.git'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--message', required=True, help='Describe the completed update')
    parser.add_argument('--prepare-only', action='store_true', help='Prepare the commit for pushing through GitHub Desktop')
    args = parser.parse_args()
    apple_git = Path('/Library/Developer/CommandLineTools/usr/bin/git')
    git = str(apple_git) if apple_git.is_file() else shutil.which('git')
    if not git:
        raise SystemExit('Git is required.')
    def run(*parts, capture=False):
        return subprocess.run([git, *parts], cwd=ROOT, check=True,
                              capture_output=capture, text=True,
                              env={**os.environ, 'GIT_TERMINAL_PROMPT':'0'})
    remote = run('remote', 'get-url', 'origin', capture=True).stdout.strip()
    if remote != EXPECTED_REMOTE:
        raise SystemExit('The configured remote does not match the portfolio repository.')
    subprocess.run([sys.executable, str(ROOT/'tools/sync_from_workspace.py')], check=True)
    # Deliberately stage only publishable project paths, never the workspace root.
    run('add', '--', 'site', 'tools', '.github', '.gitignore', 'README.md', 'LICENSE', 'CONTENT_NOTICE.md')
    staged = run('diff', '--cached', '--name-only', capture=True).stdout.strip()
    if staged:
        run('commit', '-m', args.message)
    else:
        print('No new file changes; retrying any previous unpushed commit.')
    if args.prepare_only:
        print('Ready to publish. In GitHub Desktop, open this repository and choose Push origin.')
        return
    run('push', '-u', 'origin', 'HEAD:main')
    print('Pushed to GitHub. Check the Publish portfolio workflow for the website deployment result.')


if __name__ == '__main__':
    main()
