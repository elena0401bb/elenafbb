"""Export the eight active pages and only their referenced assets."""
from pathlib import Path
import argparse
import json
import shutil
from check_site import Page, CSS_URL, local_target, ROOT, SITE, check
from optimize_images import optimize

PAGES = [
    'portfolio-yangcong-draft.html',
    'project-folder-teacher-ip-yangcong-draft.html',
    'project-folder-guoer-ip-yangcong-draft.html',
    'project-folder-houhou-ip-yangcong-draft.html',
    'project-folder-houda-official-yangcong-draft.html',
    'project-folder-fakao-meme-yangcong-draft.html',
    'project-folder-9r9-yangcong-draft.html',
    'project-folder-growth-yangcong-draft.html',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT.parent / '.superpowers/brainstorm/81473-1787796986/content')
    args = parser.parse_args()
    source = args.source.resolve()
    pending = [source / name for name in PAGES]
    found = set()
    while pending:
        file = pending.pop().resolve()
        if file in found:
            continue
        if not file.is_file():
            raise SystemExit(f'Missing source file: {file.name}')
        if not file.is_relative_to(source):
            raise SystemExit('Source dependency leaves website directory')
        if file.suffix == '.html' and file.name not in PAGES:
            raise SystemExit(f'Unlisted HTML page: {file.name}; review before exporting')
        found.add(file)
        if file.suffix not in ('.html', '.css'):
            continue
        text = file.read_text()
        refs = Page(text).refs if file.suffix == '.html' else CSS_URL.findall(text)
        for ref in refs:
            target = local_target(file, ref, source)
            if target is not None and target not in found:
                pending.append(target)
    SITE.mkdir(exist_ok=True)
    current = {file.relative_to(source).as_posix() for file in found}
    local = ROOT / '.local'
    local.mkdir(exist_ok=True)
    record = local / 'exported-files.json'
    previous = set(json.loads(record.read_text())) if record.exists() else set()
    for file in sorted(found):
        destination = SITE / file.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, destination)
    # Only remove files listed in the previous export, never unrelated local files.
    for relative in previous - current:
        old = (SITE / relative).resolve()
        if old.is_relative_to(SITE.resolve()) and old.is_file():
            old.unlink()
    optimize(SITE, PAGES, local / 'image-optimization.json')
    shutil.copy2(SITE / PAGES[0], SITE / 'index.html')
    (SITE / '.nojekyll').touch()
    record.write_text(json.dumps(sorted(current), ensure_ascii=False, indent=2) + '\n')
    errors, warnings = check()
    for message in errors + warnings:
        print(message)
    print(f'Exported {len(current)} source files plus the homepage entry; {len(errors)} file errors, {len(warnings)} section warnings.')
    if errors or warnings:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
