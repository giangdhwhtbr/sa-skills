"""Render a deck as one self-contained HTML file: 1280x720 slides, keyboard navigation, a speaker-notes
panel, and a print stylesheet that gives one slide per PDF page."""

from __future__ import annotations

import base64
import html
import re
from pathlib import Path

from .assets import Chip, SlideImage
from .model import Block, Deck, DiagramRef, Slide

PLACEHOLDER = "Diagram not exported: run /sa-diagrams --png"
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
_BOLD = re.compile(r"\*\*(.+?)\*\*")


def rich(text: str) -> str:
    """Escape, then turn **x** into <b>x</b>."""
    return _BOLD.sub(r"<b>\1</b>", html.escape(text, quote=False))


def _data_uri(path: Path) -> str:
    mime = MIME.get(path.suffix.lower(), "image/png")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def clock(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


def _chips(chips: list[Chip]) -> str:
    out = []
    for chip in chips:
        if chip.kind == "edge":
            dash = ' stroke-dasharray="5 3"' if chip.dashed else ""
            symbol = (f'<svg width="34" height="10" aria-hidden="true"><line x1="1" y1="5" x2="27" y2="5" '
                      f'stroke="{chip.stroke}" stroke-width="2.5"{dash}/>'
                      f'<polygon points="27,1 34,5 27,9" fill="{chip.stroke}"/></svg>')
        else:
            border = "dashed" if chip.dashed else "solid"
            symbol = f'<span class="sw" style="background:{chip.fill};border:1.5px {border} {chip.stroke}"></span>'
        out.append(f'<span class="chip">{symbol}{html.escape(chip.label)}</span>')
    return f'<div class="leg">{"".join(out)}</div>'


def _merged_chips(images: list[SlideImage]) -> list[Chip]:
    seen: list[Chip] = []
    for image in images:
        for chip in image.chips:
            if all((c.kind, c.label) != (chip.kind, chip.label) for c in seen):
                seen.append(chip)
    return seen


def _picture(image: SlideImage, cls: str = "") -> str:
    if image.path is None:
        return f'<div class="dia ph {cls}">{PLACEHOLDER}</div>'
    return f'<div class="dia {cls}"><img src="{_data_uri(image.path)}" alt=""></div>'


def _items(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{rich(i)}</li>" for i in items) + "</ul>"


def _agenda(deck: Deck, slide: Slide) -> str:
    rows = []
    for title in deck.sections:
        if title == slide.section:
            continue
        numbers = [s.number for s in deck.slides if s.section == title]
        pages = f"{numbers[0]}" if len(numbers) == 1 else f"{numbers[0]}–{numbers[-1]}"
        rows.append(f'<div class="ag-item"><span class="n">{len(rows) + 1}</span>'
                    f'<span class="t">{html.escape(title)}</span><span class="pg">{pages}</span></div>')
    half = (len(rows) + 1) // 2
    left, right = "".join(rows[:half]), "".join(rows[half:])
    return f'<div class="agenda"><div class="col">{left}</div><div class="col">{right}</div></div>'


def _block(deck: Deck, slide: Slide, images: dict[DiagramRef, SlideImage], design_dir: Path) -> str:
    block: Block | None = slide.block
    if block is None:
        return ""
    if block.kind == "bullets":
        return f'<div class="bul">{_items(block.items)}</div>'
    if block.kind == "table":
        cols = ""
        if block.widths:
            total = sum(block.widths)
            cols = "<colgroup>" + "".join(f'<col style="width:{w / total * 100:.1f}%">' for w in block.widths) + \
                "</colgroup>"
        head = "".join(f"<th>{rich(h)}</th>" for h in block.header)
        body = "".join("<tr>" + "".join(f"<td>{rich(c)}</td>" for c in row) + "</tr>" for row in block.rows)
        return f'<table class="tbl">{cols}<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'
    if block.kind == "diagram":
        image = images[block.diagrams[0]]
        return _picture(image) + _chips(image.chips)
    if block.kind == "diagrams":
        pair = [images[ref] for ref in block.diagrams]
        return f'<div class="two">{_picture(pair[0], "half")}{_picture(pair[1], "half")}</div>' + \
            _chips(_merged_chips(pair))
    if block.kind == "diagram-text":
        image = images[block.diagrams[0]]
        return f'<div class="dt">{_picture(image, "wide")}<div class="side">{_items(block.items)}</div></div>' + \
            _chips(image.chips)
    if block.kind == "agenda":
        return _agenda(deck, slide)
    if block.kind == "image" and block.file:
        return f'<div class="dia"><img src="{_data_uri(design_dir / "deck" / block.file)}" alt=""></div>'
    return ""


def _notes(slide: Slide) -> str:
    return f'<aside class="notes">{html.escape(slide.notes, quote=False)}</aside>'


def _cover(deck: Deck, slide: Slide, design_dir: Path) -> str:
    logo = ""
    if deck.theme.logo:
        logo = f'<img class="logo" src="{_data_uri(design_dir / "deck" / deck.theme.logo)}" alt="">'
    lines = "".join(f'<div class="{cls}">{html.escape(text)}</div>'
                    for cls, text in (("presenter", deck.presenter), ("date", deck.date)) if text)
    return (f'<section class="slide cover" data-n="{slide.number}">{logo}<div class="rule"></div>'
            f'<h1>{rich(slide.title)}</h1><div class="msg">{rich(slide.message)}</div>{lines}{_notes(slide)}</section>')


def _content(deck: Deck, slide: Slide, images: dict[DiagramRef, SlideImage], design_dir: Path) -> str:
    footer = f'<div class="foot">{html.escape(deck.theme.footer)}</div>' if deck.theme.footer else ""
    return (f'<section class="slide" data-n="{slide.number}"><h1>{rich(slide.title)}</h1>'
            f'<div class="msg">{rich(slide.message)}</div>'
            f'<div class="body">{_block(deck, slide, images, design_dir)}</div>'
            f'{footer}<div class="num">{slide.number}</div>{_notes(slide)}</section>')


CSS = """
:root{--primary:%(primary)s;--accent:%(accent)s;--text:%(text)s;--muted:%(muted)s;
 --font:%(font)s,'Segoe UI',Arial,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%%;background:#1b1b1f;font-family:var(--font);color:var(--text)}
#stage{position:absolute;left:50%%;top:50%%;width:1280px;height:720px;transform-origin:center center}
.slide{position:absolute;inset:0;background:#fff;visibility:hidden;overflow:hidden}
.slide.on{visibility:visible}
.slide:not(.on) *{visibility:hidden!important}
.slide h1{position:absolute;left:34px;top:18px;width:1180px;font-size:32px;font-weight:600;color:var(--primary);
 line-height:1.15}
.slide .msg{position:absolute;left:34px;top:62px;width:1180px;font-size:16px;color:var(--muted)}
.slide .body{position:absolute;left:34px;top:100px;width:1212px;height:560px;display:flex;flex-direction:column}
.num{position:absolute;right:20px;bottom:10px;font-size:12px;color:var(--muted)}
.foot{position:absolute;left:34px;bottom:10px;font-size:11px;color:var(--muted)}
.notes{display:none}
.cover{background:var(--primary);color:#fff}
.cover h1{color:#fff;left:56px;top:262px;width:760px;font-size:48px}
.cover .msg{color:#e4e8f4;left:56px;top:400px;font-size:20px}
.cover .presenter{position:absolute;left:56px;top:448px;font-size:20px;color:#e4e8f4}
.cover .date{position:absolute;left:56px;top:482px;font-size:16px;color:#e4e8f4}
.cover .logo{position:absolute;left:50%%;top:34px;height:78px;transform:translateX(-50%%)}
.cover .rule{position:absolute;left:840px;top:200px;width:3px;height:260px;background:var(--accent)}
.bul ul,.side ul{list-style:none;margin:10px 0 0 6px}
.bul li,.side li{position:relative;padding-left:26px;margin:0 0 18px;font-size:22px;line-height:1.35}
.side li{font-size:18px;margin-bottom:14px}
.bul li:before,.side li:before{content:"";position:absolute;left:0;top:.5em;width:10px;height:10px;
 border-radius:50%%;background:var(--accent)}
.tbl{border-collapse:collapse;width:100%%;font-size:16px;margin-top:6px}
.tbl th{background:var(--primary);color:#fff;text-align:left;padding:10px 14px;font-weight:600}
.tbl td{padding:9px 14px;border-bottom:1px solid #dfe3ee;vertical-align:top;line-height:1.35}
.tbl tbody tr:nth-child(even) td{background:#f4f6fc}
.dia{flex:1;min-height:0;display:flex;align-items:center;justify-content:center;border:1px solid #e3e6ef;
 background:#fff}
.dia img{max-width:100%%;max-height:100%%;object-fit:contain}
.dia.ph{background:#eef0f4;color:var(--muted);font-size:18px;border-style:dashed}
.two{flex:1;min-height:0;display:flex;gap:10px}.two .dia{width:50%%}
.dt{flex:1;min-height:0;display:flex;gap:18px}.dt .dia{width:62%%;flex:none}.dt .side{flex:1}
.leg{display:flex;flex-wrap:wrap;gap:4px 16px;margin-top:6px;font-size:12px;color:var(--muted);align-items:center;
 min-height:20px}
.chip{display:inline-flex;align-items:center;gap:6px}.sw{display:inline-block;width:26px;height:13px;border-radius:2px}
.agenda{display:flex;gap:56px;margin:26px 10px 0 20px}.agenda .col{flex:1}
.ag-item{display:flex;align-items:center;margin-bottom:24px}
.ag-item .n{flex:none;width:38px;height:38px;border-radius:50%%;background:var(--accent);color:#fff;text-align:center;
 line-height:38px;font-size:17px;margin-right:16px}
.ag-item .t{flex:1;font-size:21px;color:var(--primary);font-weight:600}
.ag-item .pg{flex:none;min-width:56px;text-align:right;font-size:15px;color:var(--muted)}
#bar{position:fixed;left:0;right:0;bottom:0;background:#0e1020;color:#cfd3ea;font-size:13px;padding:8px 14px;
 display:flex;gap:18px;align-items:center;z-index:9}
#bar b{color:#fff}
#nt{display:none;position:fixed;left:0;right:0;bottom:34px;max-height:34vh;overflow:auto;background:#fff8d6;
 color:#222;padding:14px 22px;font-size:16px;line-height:1.5;border-top:2px solid #d6b656;z-index:8;
 white-space:pre-wrap}
#nt.show{display:block}
@page{size:1280px 720px;margin:0}
@media print{html,body{background:#fff;height:auto}#bar,#nt{display:none!important}
 #stage{position:static;transform:none!important;width:1280px;height:auto}
 .slide{position:relative;visibility:visible;width:1280px;height:720px;page-break-after:always;break-after:page}
 .slide:not(.on) *{visibility:visible!important}.slide *{visibility:visible!important}}
"""

JS = """
const slides=[...document.querySelectorAll('.slide')];let cur=0;
function fit(){const s=Math.min(innerWidth/1280,(innerHeight-34)/720);const st=document.getElementById('stage');
 st.style.transform='translate(-50%,-50%) scale('+s+')';st.style.top='calc(50% - 17px)';}
function show(i){cur=Math.max(0,Math.min(slides.length-1,i));slides.forEach((s,j)=>s.classList.toggle('on',j===cur));
 document.getElementById('pos').textContent=(cur+1)+' / '+slides.length;
 document.getElementById('nt').textContent=slides[cur].querySelector('.notes').textContent;
 history.replaceState(null,'','#'+(cur+1));}
addEventListener('keydown',e=>{
 if(['ArrowRight','PageDown',' '].includes(e.key)){show(cur+1);e.preventDefault();}
 else if(['ArrowLeft','PageUp'].includes(e.key)){show(cur-1);e.preventDefault();}
 else if(e.key==='Home')show(0);else if(e.key==='End')show(slides.length-1);
 else if(e.key.toLowerCase()==='n')document.getElementById('nt').classList.toggle('show');});
addEventListener('hashchange',()=>show((parseInt(location.hash.slice(1))||1)-1));
addEventListener('resize',fit);
window.onload=()=>{fit();show((parseInt(location.hash.slice(1))||1)-1);};
"""


def render(deck: Deck, images: dict[DiagramRef, SlideImage], design_dir: Path) -> str:
    """The deck as one self-contained HTML document (no external URL)."""
    theme = deck.theme
    css = CSS % {"primary": theme.primary, "accent": theme.accent, "text": theme.text, "muted": theme.muted,
                 "font": f"'{theme.font}'"}
    slides = [_cover(deck, s, design_dir) if s.kind == "cover" else _content(deck, s, images, design_dir)
              for s in deck.slides]
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(deck.title)}</title>'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><style>{css}</style></head><body>'
            f'<div id="stage">{"".join(slides)}</div><div id="nt"></div>'
            f'<div id="bar"><b id="pos"></b><span>← → navigate · N speaker notes · print = one slide per page</span>'
            f'<span style="margin-left:auto">Total {clock(deck.seconds)} of {clock(deck.minutes * 60)}</span></div>'
            f"<script>{JS}</script></body></html>\n")
