import os
import tempfile
import warnings
warnings.filterwarnings("ignore")

import urllib.request
import urllib.parse
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
import easyocr

_reader = None

def get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], verbose=False)
    return _reader

def resolve_reddit_url(url):
    if "reddit.com/media" in url:
        params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if "url" in params:
            return params["url"][0]
    return url

def download_url(url):
    url = resolve_reddit_url(url)
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or ".jpg"
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        tmp.write(resp.read())
    tmp.close()
    return tmp.name

def make_variants(src_path):
    img = Image.open(src_path)
    gray = img.convert("L")
    scale2 = gray.resize((gray.width * 2, gray.height * 2), Image.LANCZOS)
    contrast_inv = ImageOps.invert(ImageEnhance.Contrast(scale2).enhance(3.0))

    def save(im, suffix):
        tmp = tempfile.NamedTemporaryFile(suffix=f"_{suffix}.png", delete=False)
        im.save(tmp.name)
        return tmp.name

    return {
        "original":     src_path,
        "scale2":       save(scale2,       "scale2"),
        "contrast_inv": save(contrast_inv, "contrast_inv"),
    }

def run_easyocr(image_path):
    downloaded = None
    if image_path.startswith("http://") or image_path.startswith("https://"):
        image_path = download_url(image_path)
        downloaded = image_path

    try:
        variants = make_variants(image_path)
        tmp_paths = [p for name, p in variants.items() if name != "original"]

        reader = get_reader()
        best_text = ""

        for path in variants.values():
            detections = reader.readtext(np.array(Image.open(path)))
            text = " ".join(d[1] for d in detections).strip()
            if len(text) > len(best_text):
                best_text = text

        for p in tmp_paths:
            os.unlink(p)
    finally:
        if downloaded:
            os.unlink(downloaded)

    lines = [l.strip() for l in best_text.splitlines() if l.strip()][:3]
    while len(lines) < 3:
        lines.append("")
    return lines