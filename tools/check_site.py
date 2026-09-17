"""Check local HTML/CSS references without requiring a browser or dependencies."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
CSS_URL = re.compile(r'url\(\s*[\'\"]?([^\'\")]+)[\'\"]?\s*\)', re.I)


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.refs = []
        self.ids = set()
        self.feed(text)
        self.refs.extend(CSS_URL.findall(text))

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value and key in ('href', 'src', 'poster', 'data-src'):
                self.refs.append(value)
            if value and key == 'id':
                self.ids.add(value)


def local_target(base, ref, boundary):
    parts = urlsplit(ref.strip())
    if parts.scheme or parts.netloc:
        if parts.scheme == 'file':
            raise ValueError('Contains a local file URL')
        return None
    path = unquote(parts.path)
    if path.startswith('/'):
        raise ValueError('Absolute URL path is unsuitable for a project Pages site')
    target = (base.parent / path).resolve() if path else base.resolve()
    if not target.is_relative_to(boundary.resolve()):
        raise ValueError('Reference leaves website directory')
    return target


def check(site=SITE):
    errors, warnings = [], []
    private_rules = ROOT / '.local/privacy-rules.json'
    blocked = json.loads(private_rules.read_text()).get('forbidden_text', []) if private_rules.exists() else []
    email_pattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
    pages = {p.resolve(): Page(p.read_text()) for p in site.rglob('*.html')}
    if not (site / 'index.html').is_file():
        errors.append('Missing index.html')
    for file in sorted(site.rglob('*')):
        if not file.is_file():
            continue
        if file.suffix in ('.html', '.css', '.js', '.json', '.svg', '.txt'):
            text = file.read_text()
            if email_pattern.search(text) or 'mailto:' in text.lower():
                errors.append(f'{file.name}: public email/contact link is not permitted')
            if any(value.lower() in text.lower() for value in blocked):
                errors.append(f'{file.name}: private identity found; replace before publishing')
        if file.suffix not in ('.html', '.css'):
            continue
        refs = pages[file.resolve()].refs if file.suffix == '.html' else CSS_URL.findall(file.read_text())
        for ref in refs:
            try:
                target = local_target(file, ref, site)
            except ValueError as e:
                errors.append(f'{file.name}: {e}: {ref}')
                continue
            if target is None:
                continue
            if not target.is_file():
                errors.append(f'{file.name}: missing {ref}')
                continue
            fragment = unquote(urlsplit(ref).fragment)
            if fragment and target in pages and fragment not in pages[target].ids:
                warnings.append(f'{file.name}: missing section {ref}')
    return sorted(set(errors)), sorted(set(warnings))


if __name__ == '__main__':
    errors, warnings = check()
    for message in warnings:
        print('SECTION WARNING:', message)
    for message in errors:
        print('ERROR:', message)
    print(f'Checked {len(list(SITE.rglob("*.html")))} pages; {len(errors)} missing/invalid file references; {len(warnings)} section warnings.')
    sys.exit(bool(errors or warnings))
