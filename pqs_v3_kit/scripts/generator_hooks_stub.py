# generator_hooks_stub.py — 生成器挂钩示例（把结构化段落/JSON‑LD/图片回写）
from pathlib import Path
import json

def attach_images(article_md:str, assignment:dict)->str:
    """把 SmartImageManager 的 hero/inline 写回 front‑matter 与正文占位。"""
    return article_md

def render_jsonld(article_meta:dict, article_tpl_path:str, faq_tpl_path:str)->str:
    tpl = Path(article_tpl_path).read_text(encoding='utf-8')
    return tpl

def ensure_sections(article_md:str)->str:
    # 若缺少对比/兼容/安装/FAQ/Sources/Disclosure 等，按 templates/markdown_injections.md 填充
    return article_md
