#!/usr/bin/env python3
"""
Content Uniqueness Guard

Checks a target Markdown article against recent articles for near-duplicate content
using a two-stage check:
  1) SimHash fingerprint (fast near-duplicate precheck)
  2) TF‑IDF cosine similarity (precise check)

Exits non‑zero if either SimHash indicates near-duplicate (by Hamming distance)
or TF‑IDF similarity exceeds the configured threshold.

Usage:
  python scripts/content_uniqueness_guard.py --target content/articles/foo.md --threshold 0.30 --days 90 \
    --cache data/content_fingerprints.json --update-cache
"""
import os
import re
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import hashlib
import yaml

FINGERPRINT_VERSION = 1


def strip_front_matter(text: str) -> str:
    # Remove YAML front matter and code fences
    text = re.sub(r"^---[\s\S]*?---\s+", "", text, flags=re.M)
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def word_ngrams(text: str, n: int = 5):
    words = re.findall(r"[A-Za-z0-9']+", text.lower())
    return [" ".join(words[i:i+n]) for i in range(len(words)-n+1)] if len(words) >= n else words


def simhash64(tokens) -> int:
    """Compute a 64-bit SimHash from iterable tokens."""
    if not tokens:
        return 0
    bits = [0] * 64
    for tok in tokens:
        h = int(hashlib.md5(tok.encode('utf-8')).hexdigest(), 16) & ((1 << 64) - 1)
        for i in range(64):
            bits[i] += 1 if (h >> i) & 1 else -1
    out = 0
    for i in range(64):
        if bits[i] > 0:
            out |= (1 << i)
    return out


def hamming_distance64(a: int, b: int) -> int:
    x = a ^ b
    # Kernighan's algorithm
    cnt = 0
    while x:
        x &= x - 1
        cnt += 1
    return cnt


def load_cache(cache_path: str):
    if not cache_path or not os.path.exists(cache_path):
        return {"version": FINGERPRINT_VERSION, "items": []}
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, dict) or 'items' not in data:
                return {"version": FINGERPRINT_VERSION, "items": []}
            return data
    except Exception:
        return {"version": FINGERPRINT_VERSION, "items": []}


def save_cache(cache_path: str, data):
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_recent_articles(dir_path: str, days: int = 30) -> List[str]:
    docs = []
    if not os.path.exists(dir_path):
        return docs
    cutoff = datetime.now() - timedelta(days=days)
    for name in os.listdir(dir_path):
        if not name.endswith('.md'):
            continue
        path = os.path.join(dir_path, name)
        try:
            ts = datetime.fromtimestamp(os.path.getctime(path))
        except Exception:
            continue
        if ts < cutoff:
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                docs.append(strip_front_matter(f.read()))
        except Exception:
            continue
    return docs


def strip_boilerplate_sections(text: str, exclude_headings: List[str]) -> str:
    """Remove sections whose headings match any of exclude_headings (case-insensitive).
    A section is defined as from a heading line (## or #) until the next heading or end.
    """
    if not text:
        return text
    lines = text.splitlines()
    out = []
    skip = False
    to_exclude = {h.strip().lower() for h in exclude_headings}
    for i, line in enumerate(lines):
        stripped = line.strip()
        is_heading = stripped.startswith('## ') or stripped.startswith('# ')
        if is_heading:
            title = stripped.lstrip('#').strip()
            if title.lower() in to_exclude:
                skip = True
                continue
            else:
                skip = False
        if not skip:
            out.append(line)
    return "\n".join(out)


def split_sections(text: str):
    """Split text into list of (heading, content) where heading is the '## ...' title or 'BODY' for preface.
    """
    lines = text.splitlines()
    sections = []
    current_title = 'BODY'
    current_buf = []
    for line in lines:
        if line.strip().startswith('## '):
            # flush previous
            if current_buf:
                sections.append((current_title, "\n".join(current_buf).strip()))
            current_title = line.strip()[3:].strip() or 'UNTITLED'
            current_buf = []
        else:
            current_buf.append(line)
    # flush last
    if current_buf:
        sections.append((current_title, "\n".join(current_buf).strip()))
    return sections


def check_uniqueness(target_path: str, pool_dir: str, days: int, threshold: float,
                     cache_path: str = None, simhash_hamm_dist: int = 16,
                     update_cache: bool = False,
                     exclude_headings: List[str] = None,
                     section_threshold: float = None,
                     section_min_words: int = 200) -> dict:
    """
    Returns dict with keys: max_cosine, max_simhash_sim, simhash_hit(bool).
    simhash similarity = 1 - hamming_distance/64.
    Duplicate if simhash_hit or max_cosine >= threshold.
    """
    with open(target_path, 'r', encoding='utf-8') as f:
        target_text = strip_front_matter(f.read())
    if exclude_headings:
        target_text = strip_boilerplate_sections(target_text, exclude_headings)

    cache = load_cache(cache_path) if cache_path else {"version": FINGERPRINT_VERSION, "items": []}

    # Build pool simhashes from cache where possible
    pool_paths = []
    if os.path.isdir(pool_dir):
        for name in os.listdir(pool_dir):
            if name.endswith('.md'):
                p = os.path.join(pool_dir, name)
                try:
                    ts = datetime.fromtimestamp(os.path.getctime(p))
                    if ts >= datetime.now() - timedelta(days=days):
                        pool_paths.append(p)
                except Exception:
                    continue

    cache_items = {it.get('path'): it for it in cache.get('items', [])}

    def ensure_simhash(path: str) -> int:
        it = cache_items.get(path)
        if it and isinstance(it.get('simhash'), str) and it.get('version') == FINGERPRINT_VERSION:
            try:
                return int(it['simhash'], 16)
            except Exception:
                pass
        try:
            with open(path, 'r', encoding='utf-8') as f:
                txt = strip_front_matter(f.read())
            tokens = word_ngrams(txt, n=5)
            sh = simhash64(tokens)
            cache_items[path] = {
                'path': path,
                'simhash': f"{sh:016x}",
                'size': os.path.getsize(path),
                'ctime': datetime.fromtimestamp(os.path.getctime(path)).isoformat(),
                'version': FINGERPRINT_VERSION
            }
            return sh
        except Exception:
            return 0

    # Compute target simhash
    target_tokens = word_ngrams(target_text, n=5)
    target_sh = simhash64(target_tokens)

    # Simhash stage: compute max similarity against pool
    max_simhash_sim = 0.0
    simhash_hit = False
    for p in pool_paths:
        sh = ensure_simhash(p)
        if sh == 0 or target_sh == 0:
            continue
        dist = hamming_distance64(sh, target_sh)
        sim = 1.0 - (dist / 64.0)
        if sim > max_simhash_sim:
            max_simhash_sim = sim
        if dist <= simhash_hamm_dist:
            simhash_hit = True

    # TF‑IDF document-level stage
    pool_texts = []
    for p in pool_paths:
        try:
            with open(p, 'r', encoding='utf-8') as f:
                txt = strip_front_matter(f.read())
                if exclude_headings:
                    txt = strip_boilerplate_sections(txt, exclude_headings)
                pool_texts.append(txt)
        except Exception:
            continue

    max_cosine = 0.0
    if pool_texts:
        corpus = pool_texts + [target_text]
        vec = TfidfVectorizer(stop_words='english', max_df=0.9)
        X = vec.fit_transform(corpus)
        sims = cosine_similarity(X[-1], X[:-1]).flatten()
        if sims.size:
            max_cosine = float(sims.max())

    section_hit = None
    max_section_sim = 0.0
    if section_threshold and pool_texts and max_cosine < threshold:
        # Only run section-level check if doc-level passed
        sections = split_sections(target_text)
        for title, content in sections:
            words = re.findall(r"[A-Za-z0-9']+", content)
            if len(words) < section_min_words:
                continue
            corpus = pool_texts + [content]
            vec = TfidfVectorizer(stop_words='english', max_df=0.9)
            X = vec.fit_transform(corpus)
            sims = cosine_similarity(X[-1], X[:-1]).flatten()
            if sims.size:
                sec_sim = float(sims.max())
                if sec_sim > max_section_sim:
                    max_section_sim = sec_sim
                if sec_sim >= section_threshold:
                    section_hit = {'title': title, 'similarity': round(sec_sim, 4)}
                    break

    # After checks, optionally update cache with target
    if cache_path and update_cache:
        items = list(cache_items.values())
        # keep only recent days to bound file size
        cutoff = datetime.now() - timedelta(days=days)
        filtered = []
        for it in items:
            try:
                if datetime.fromisoformat(it.get('ctime', '1970-01-01T00:00:00')) >= cutoff:
                    filtered.append(it)
            except Exception:
                continue
        # add target
        filtered.append({
            'path': target_path,
            'simhash': f"{target_sh:016x}",
            'size': os.path.getsize(target_path),
            'ctime': datetime.now().isoformat(),
            'version': FINGERPRINT_VERSION
        })
        save_cache(cache_path, {'version': FINGERPRINT_VERSION, 'items': filtered})

    return {
        'max_cosine': round(max_cosine, 4),
        'max_simhash_sim': round(max_simhash_sim, 4),
        'simhash_hit': simhash_hit,
        'section_hit': section_hit,
        'max_section_sim': round(max_section_sim, 4)
    }


def main():
    p = argparse.ArgumentParser(description='Check article uniqueness against recent posts')
    p.add_argument('--target', required=True, help='Path to target Markdown file')
    p.add_argument('--pool', default='content/articles', help='Directory of existing articles')
    p.add_argument('--days', type=int, default=30, help='Lookback window in days')
    p.add_argument('--threshold', type=float, default=0.85, help='Max allowed cosine similarity (0-1)')
    p.add_argument('--cache', default='data/content_fingerprints.json', help='Path to fingerprint cache JSON')
    p.add_argument('--simhash-hamm', type=int, default=16, help='Max allowed Hamming distance (64-bit) for near-duplicate precheck')
    p.add_argument('--update-cache', action='store_true', help='Update cache with the target if not duplicate')
    p.add_argument('--config', default='config/uniqueness.yml', help='Path to YAML config to override defaults')
    args = p.parse_args()

    if not os.path.exists(args.target):
        print(f"Target not found: {args.target}")
        return 2

    # Load YAML config if present
    cfg = {}
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f) or {}
        except Exception:
            cfg = {}

    threshold = float(cfg.get('tfidf_threshold', args.threshold))
    days = int(cfg.get('days_window', args.days))
    simhash_hamm = int(cfg.get('simhash_hamm', args.simhash_hamm))
    exclude_headings = cfg.get('exclude_headings', []) or []
    section_threshold = cfg.get('section_tfidf_threshold')
    section_min_words = int(cfg.get('section_min_words', 200))

    res = check_uniqueness(
        args.target, args.pool, days, threshold,
        cache_path=args.cache, simhash_hamm_dist=simhash_hamm,
        update_cache=args.update_cache, exclude_headings=exclude_headings,
        section_threshold=section_threshold, section_min_words=section_min_words
    )
    out = {
        'max_cosine': res['max_cosine'],
        'max_simhash_sim': res['max_simhash_sim'],
        'threshold': threshold,
        'simhash_hit': res['simhash_hit'],
        'section_hit': res['section_hit'],
        'max_section_sim': res['max_section_sim']
    }
    print(json.dumps(out))
    if res['simhash_hit']:
        print(f"Too similar (SimHash near-duplicate)")
        return 3
    if res['max_cosine'] >= threshold:
        print(f"Too similar (TF‑IDF): {res['max_cosine']:.3f} >= {threshold:.2f}")
        return 3
    if res['section_hit'] and section_threshold is not None:
        print(f"Too similar (Section TF‑IDF): {res['section_hit']['similarity']:.3f} >= {float(section_threshold):.2f} in [{res['section_hit']['title']}]")
        return 3
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

