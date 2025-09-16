#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, re, json, os, math, argparse, pathlib
from datetime import datetime
try:
    import yaml
except Exception:
    print("Please `pip install pyyaml`", file=sys.stderr); sys.exit(2)

IMG_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
LINK_RE = re.compile(r'\[([^\]]+)\]\((https?://[^)]+)\)')
H1_RE = re.compile(r'^\s*#\s+.+', re.M)
H2_RE = re.compile(r'^\s*##\s+.+', re.M)
JSONLD_HIT = re.compile(r'"@type"\s*:\s*"Article"|@type"\s*:\s*"FAQPage"', re.I)

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def read_file(p):
    try:
        return pathlib.Path(p).read_text(encoding='utf-8')
    except Exception:
        return ""

def extract_front_matter(md):
    if md.startswith('---'):
        end = md.find('\n---', 3)
        if end != -1:
            fm = md[3:end].strip()
            body = md[end+4:]
            try:
                data = yaml.safe_load(fm) or {}
            except Exception:
                data = {}
            return data, body
    return {}, md

def word_count(s):
    tokens = re.findall(r'\w+', s)
    return len(tokens)

def density(text, kw):
    if not kw: return 0.0
    wc = max(1, word_count(text))
    cnt = len(re.findall(re.escape(kw.lower()), text.lower()))
    return cnt / wc

def find_entities_hits(text, tokens):
    t = text.lower()
    return [tok for tok in tokens if tok.lower() in t]

def score_readability(text):
    sents = re.split(r'[。！？.!?]+', text)
    valid = [s for s in sents if s.strip()]
    if not valid: return 5.0
    avg_len = sum(len(s) for s in valid) / len(valid)
    h2 = len(H2_RE.findall(text))
    score = 100 - min(70, avg_len) + min(10, h2*2)
    return max(0, min(10, score/10))

def check_article(md_path, cfg):
    md = read_file(md_path)
    fm, body = extract_front_matter(md)
    text = body

    report = {"file": str(md_path), "errors": [], "warn": [], "score": 0, "subs": {}}

    featured = fm.get('featured_image')
    images = IMG_RE.findall(text)
    if not featured or len(images) < cfg['thresholds']['min_inline_images']:
        report["errors"].append("images: need featured + >=2 inline")
    for alt, _src in images:
        if not alt or len(alt) < 8 or len(alt) > 120:
            report["errors"].append("images: alt length out of range")

    cat = (fm.get('category') or fm.get('categories') or fm.get('slug') or 'generic')
    cat = cat[0] if isinstance(cat, list) else cat
    tokens = set(cfg['entities_tokens'].get(cat, []) + cfg['entities_tokens']['generic'])
    if images:
        ok = any(any(tok.lower() in alt.lower() for tok in tokens) for alt,_ in images)
        if not ok:
            report["errors"].append("images: alt must include at least one entity token")

    links = LINK_RE.findall(text)
    if len(links) < 2:
        report["errors"].append("evidence: need >=2 external links")

    if not JSONLD_HIT.search(md):
        report["errors"].append("schema: Article / FAQPage JSON-LD missing")

    has_table = '|' in text and re.search(r'\n\|', text)
    has_itemlist = 'ItemList' in md
    has_framework = re.search(r'(?i)(who should buy|who should not buy|alternatives)', text) is not None
    if not (has_table or has_itemlist or has_framework):
        report["errors"].append("comparison/framework: need table(>=6 rows) or ItemList or who/why/alt block")
    if has_table:
        rows = [ln for ln in text.splitlines() if ln.strip().startswith('|')]
        if len(rows) < 8:
            report["errors"].append("comparison: table rows < 6")

    claims = re.search(r'(?i)(we tested|hands-on|our testing|lab results)', text)
    has_method = re.search(r'(?i)(how we evaluate|methodology)', text)
    if claims and not has_method:
        report["errors"].append("honesty: testing claims require methodology section")

    primary_kw = fm.get('keyword') or fm.get('title','').split('|')[0]
    if primary_kw:
        if density(text, primary_kw) > cfg['thresholds']['keyword_density_max']:
            report["errors"].append("keyword_density: too high")

    entity_hits = find_entities_hits(text, list(tokens))
    if len(set(entity_hits)) < 3:
        report["errors"].append("entity_coverage: need >=3 entities")

    depth = 0
    if re.search(r'(?i)(conclusion|summary)', text): depth += 6
    if has_table or has_itemlist: depth += 8
    if re.search(r'(?i)(alternatives|who should buy|who should not buy)', text): depth += 8
    if re.search(r'(?i)(risks|watch out|considerations)', text): depth += 8
    depth = min(30, depth)

    evidence = min(20, len(links)*5)
    images_score = min(15, (len(images)>=2)*7 + 8) if featured else 0
    structure = 0
    if H1_RE.search(text): structure += 5
    if len(H2_RE.findall(text)) >= 4: structure += 5
    if re.search(r'(?i)\[(.+)\]\((\/[^)]+)\)', text): structure += 5
    readability = score_readability(text)
    compliance = 0
    if fm.get('author') and fm.get('date'): compliance += 4
    if re.search(r'(?i)(affiliate disclosure|as an amazon associate|披露)', text): compliance += 3
    if re.search(r'(?i)(about|review policy)', text): compliance += 3
    total = depth + evidence + images_score + structure + readability + compliance
    total = max(0, min(100, total))

    report["score"] = total
    report["subs"] = {
        "depth": depth, "evidence": evidence, "images": images_score,
        "structure": structure, "readability": readability, "compliance": compliance
    }
    return report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Markdown file or directory")
    ap.add_argument("--config", default="config/pqs_config.yml")
    ap.add_argument("--out", default="pqs_report.json")
    args = ap.parse_args()

    cfg = load_config(args.config)
    p = pathlib.Path(args.path)
    files = []
    if p.is_dir():
        for ext in ("*.md", "*.markdown"):
            files += list(p.rglob(ext))
    else:
        files = [p]

    reports = []
    failed = 0
    for f in files:
        rep = check_article(f, cfg)
        reports.append(rep)
        if rep["errors"]:
            failed += 1
            print(f"[FAIL] {f}: hard-gate errors: {rep['errors']}")
        else:
            if rep["score"] < cfg["thresholds"]["publish_score"]:
                failed += 1
                print(f"[FAIL] {f}: score {rep['score']} < {cfg['thresholds']['publish_score']}")
            else:
                print(f"[OK] {f}: score {rep['score']}")
    with open(args.out, "w", encoding="utf-8") as w:
        json.dump({"generated_at": datetime.utcnow().isoformat(), "reports": reports}, w, ensure_ascii=False, indent=2)
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
