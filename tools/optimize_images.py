"""Build responsive WebP previews while retaining original artwork for zooming.

Run on freshly exported HTML, not the editing source. Pillow is needed only
when exporting; the deployed site and the GitHub validation need no packages.
"""
from hashlib import sha256
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import json
import os

from PIL import Image, ImageOps
from check_site import local_target

WIDTHS = (480, 800, 1280)
QUALITY = 86
VERSION = 'webp-v1'
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}


def sizes_for(classes):
    if 'hero-expression' in classes:
        return '110px'
    if 'character-sheet' in classes:
        return '(max-width: 767px) 35vw, 200px'
    if 'wall-card' in classes:
        return '(max-width: 767px) 48vw, 300px'
    if 'archive-sheet' in classes:
        return '(max-width: 767px) 66vw, (max-width: 1100px) 30vw, 380px'
    if 'account-preview' in classes:
        return '(max-width: 767px) 48vw, 240px'
    if 'asset' in classes or 'avatar-shell' in classes:
        return '(max-width: 767px) 190px, 300px'
    # These images are wider than their visible crop, so allow for the overscan.
    if {'recent-note-media', 'content-example-media'} & classes:
        return '(max-width: 767px) calc(175vw - 84px), (max-width: 1100px) 85vw, 850px'
    return '(max-width: 767px) calc(100vw - 48px), (max-width: 1100px) 50vw, 520px'


class PreviewBuilder:
    def __init__(self, site):
        self.site = site.resolve()
        self.directory = self.site / '_images'
        self.directory.mkdir(exist_ok=True)
        self.assets = {}
        self.generated = set()

    def variants(self, source):
        relative = source.relative_to(self.site).as_posix()
        if relative in self.assets:
            return self.assets[relative]
        fingerprint = sha256(source.read_bytes() + f'{VERSION}:{QUALITY}:{WIDTHS}'.encode()).hexdigest()[:16]
        with Image.open(source) as original:
            if getattr(original, 'is_animated', False):
                return None
            artwork = ImageOps.exif_transpose(original)
            width, height = artwork.size
            artwork = artwork.convert('RGBA' if 'A' in artwork.getbands() or 'transparency' in artwork.info else 'RGB')
            variants = []
            for target_width in sorted({min(width, size) for size in WIDTHS}):
                target_height = max(1, round(height * target_width / width))
                destination = self.directory / f'{fingerprint}-{target_width}.webp'
                if not destination.exists():
                    resized = artwork.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    temporary = destination.with_suffix('.tmp')
                    # Do not copy EXIF, ICC or other source metadata into previews.
                    resized.save(temporary, format='WEBP', quality=QUALITY, method=5)
                    temporary.replace(destination)
                self.generated.add(destination)
                variants.append({'path': destination.relative_to(self.site).as_posix(),
                                 'width': target_width, 'height': target_height,
                                 'bytes': destination.stat().st_size})
        result = {'original': relative, 'original_bytes': source.stat().st_size,
                  'width': width, 'height': height, 'variants': variants}
        self.assets[relative] = result
        return result


class ImageRewriter(HTMLParser):
    def __init__(self, text, page, builder):
        super().__init__(convert_charrefs=False)
        self.text, self.page, self.builder = text, page, builder
        self.stack, self.edits, self.images = [], [], []
        self.priority_assigned = False
        self.line_offsets = [0]
        for line in text.splitlines(keepends=True):
            self.line_offsets.append(self.line_offsets[-1] + len(line))
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'img' and attrs.get('src') and not any(t == 'dialog' for t, _ in self.stack):
            source = local_target(self.page, attrs['src'], self.builder.site)
            if source is not None and source.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}:
                asset = self.builder.variants(source)
                if asset:
                    self.replace_image(attrs, asset)
        if tag not in VOID:
            self.stack.append((tag, attrs))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def replace_image(self, attrs, asset):
        classes = set(attrs.get('class', '').split())
        for _, ancestor in self.stack:
            classes.update(ancestor.get('class', '').split())
        hero = 'hero' in classes or 'archive-sheets' in classes
        variants = asset['variants']
        default = next((v for v in variants if v['width'] >= 800), variants[-1])

        def relative_url(variant):
            return Path(os.path.relpath(self.builder.site / variant['path'], self.page.parent)).as_posix()

        attrs['data-original-src'] = attrs['src']
        attrs['src'] = relative_url(default)
        attrs['srcset'] = ', '.join(f'{relative_url(v)} {v["width"]}w' for v in variants)
        attrs['sizes'] = sizes_for(classes)
        attrs['width'], attrs['height'] = str(asset['width']), str(asset['height'])
        attrs['loading'] = 'eager' if hero else 'lazy'
        attrs['decoding'] = 'async'
        attrs.pop('fetchpriority', None)
        if hero and not self.priority_assigned:
            attrs['fetchpriority'] = 'high'
            self.priority_assigned = True
        replacement = '<img ' + ' '.join(key if value is None else f'{key}="{escape(value, quote=True)}"'
                                          for key, value in attrs.items()) + '>'
        line, column = self.getpos()
        start = self.line_offsets[line - 1] + column
        self.edits.append((start, start + len(self.get_starttag_text()), replacement))
        self.images.append({'original': asset['original'], 'eager': hero,
                            'default': default['path'], 'default_bytes': default['bytes']})

    def rewritten(self):
        result = self.text
        for start, end, replacement in reversed(self.edits):
            result = result[:start] + replacement + result[end:]
        return result


def optimize(site, pages, report_path=None):
    site = site.resolve()
    builder = PreviewBuilder(site)
    page_reports = {}
    for name in pages:
        page = site / name
        rewriter = ImageRewriter(page.read_text(), page, builder)
        page.write_text(rewriter.rewritten())
        page_reports[name] = rewriter.images
    # This reserved directory only contains generated previews.
    for stale in builder.directory.glob('*.webp'):
        if stale not in builder.generated:
            stale.unlink()
    report = {'version': VERSION, 'quality': QUALITY, 'widths': WIDTHS,
              'assets': builder.assets, 'pages': page_reports}
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    original_bytes = sum(item['original_bytes'] for item in builder.assets.values())
    default_bytes = sum(next((v['bytes'] for v in item['variants'] if v['width'] >= 800),
                             item['variants'][-1]['bytes']) for item in builder.assets.values())
    print(f'Optimized {len(builder.assets)} display images: default previews {default_bytes:,} bytes '
          f'(originals {original_bytes:,} bytes); {len(builder.generated)} responsive files.')
    return report
