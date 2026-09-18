"""Regression checks for responsive exports and full-resolution image links."""
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image
from check_site import Page, check, local_target, srcset_urls
from optimize_images import optimize


class Images(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.images = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.images.append(dict(attrs))


class ImageExportTests(unittest.TestCase):
    def test_srcset_candidates_are_validated_individually(self):
        self.assertEqual(list(srcset_urls('small.webp 480w, large.webp 1280w')),
                         ['small.webp', 'large.webp'])
        self.assertEqual(list(srcset_urls('data:image/png;base64,AAAA 1x, high.webp 2x')),
                         ['data:image/png;base64,AAAA', 'high.webp'])
        with TemporaryDirectory() as directory:
            site = Path(directory)
            page = site / 'index.html'
            (site / 'small.webp').touch()
            page.write_text('<img src="small.webp" srcset="small.webp 480w, missing.webp 1280w">')
            errors, _ = check(site)
            self.assertTrue(any('missing.webp' in error for error in errors))
            with self.assertRaises(ValueError):
                local_target(page, '../outside.webp', site)

    def test_export_preserves_copy_originals_and_transparency(self):
        with TemporaryDirectory() as directory:
            site = Path(directory)
            original = site / 'art.png'
            Image.new('RGBA', (1600, 2400), (20, 80, 120, 0)).save(original)
            Image.new('RGB', (200, 300), 'green').save(site / 'small.png')
            original_bytes = original.read_bytes()
            content = ('<!doctype html><h1>作品内容保持原样</h1>'
                       '<section class="hero"><img src="art.png" alt="首屏作品"></section>'
                       '<section><a href="art.png" data-lightbox><img src="art.png" alt="原图入口"></a>'
                       '<img src="small.png" alt="小尺寸素材"></section>'
                       '<dialog><img id="preview" alt=""></dialog>'
                       '<script>const source = "unchanged";</script>')
            page = site / 'index.html'
            page.write_text(content)
            report = optimize(site, ['index.html'])
            result = page.read_text()
            images = Images(result).images
            self.assertEqual(original.read_bytes(), original_bytes)
            self.assertIn('<h1>作品内容保持原样</h1>', result)
            self.assertIn('<script>const source = "unchanged";</script>', result)
            self.assertIn('<a href="art.png" data-lightbox>', result)
            self.assertEqual(images[0]['loading'], 'eager')
            self.assertEqual(images[0]['fetchpriority'], 'high')
            self.assertEqual(images[1]['loading'], 'lazy')
            self.assertNotIn('fetchpriority', images[1])
            self.assertEqual(images[1]['data-original-src'], 'art.png')
            self.assertEqual((images[0]['width'], images[0]['height']), ('1600', '2400'))
            self.assertEqual(images[-1], {'id': 'preview', 'alt': ''})
            self.assertEqual(len(report['assets']), 2)
            self.assertEqual(len(report['assets']['small.png']['variants']), 1)
            for ref in srcset_urls(images[0]['srcset']):
                with Image.open(site / ref) as preview:
                    self.assertEqual(preview.format, 'WEBP')
                    self.assertEqual(preview.getpixel((0, 0))[3], 0)
                    self.assertLessEqual(preview.width, 1280)
                    self.assertAlmostEqual(preview.height / preview.width, 1.5, places=2)
            self.assertEqual(check(site), ([], []))
            # Re-exporting the same source reuses the exact same image files.
            paths = sorted((site / '_images').glob('*.webp'))
            mtimes = [p.stat().st_mtime_ns for p in paths]
            page.write_text(content)
            optimize(site, ['index.html'])
            self.assertEqual(result, page.read_text())
            self.assertEqual(mtimes, [p.stat().st_mtime_ns for p in paths])


if __name__ == '__main__':
    unittest.main()
