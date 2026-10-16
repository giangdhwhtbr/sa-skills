// Render a sa-deck deck.json as an editable PowerPoint: node pptx.js <deck.json> <out.pptx>.
// Uses the same layout grid as the HTML deck (1280x720 px == 13.333x7.5 in). Exit 1 with the error on failure.
const fs = require('fs');
const PptxGenJS = require('pptxgenjs');

const [input, output] = process.argv.slice(2);
if (!input || !output) {
  console.error('usage: node pptx.js <deck.json> <out.pptx>');
  process.exit(1);
}
const deck = JSON.parse(fs.readFileSync(input, 'utf8'));
const T = deck.theme;
const W = 13.333, H = 7.5, X0 = 0.45, CW = W - 2 * X0;
const BODY = { x: X0, y: 1.3, w: CW, h: 5.6 };
const LIGHT = 'F4F6FC', LINE = 'DFE3EE', PLACEHOLDER_FILL = 'EEF0F4';
const PLACEHOLDER = 'Diagram not exported: run /sa-diagrams --png';

const pres = new PptxGenJS();
pres.layout = 'LAYOUT_WIDE';
pres.title = deck.meta.title;
if (deck.meta.presenter) pres.author = deck.meta.presenter;
pres.theme = { headFontFace: T.font, bodyFontFace: T.font };
pres.defineSlideMaster({
  title: 'CONTENT',
  background: { color: 'FFFFFF' },
  slideNumber: { x: W - 0.9, y: H - 0.4, w: 0.5, h: 0.3, fontFace: T.font, fontSize: 10, color: T.muted, align: 'right' },
});

const runs = (list, base = {}) => list.map(([text, bold]) => ({ text, options: { ...base, bold: !!bold || !!base.bold } }));

function fit(img, box) {
  // largest w x h with the image's aspect ratio inside the box, centred
  const ratio = img.w && img.h ? img.w / img.h : box.w / box.h;
  let w = box.w, h = w / ratio;
  if (h > box.h) { h = box.h; w = h * ratio; }
  return { x: box.x + (box.w - w) / 2, y: box.y + (box.h - h) / 2, w, h };
}

function picture(slide, img, box) {
  if (!img.path) {
    slide.addShape(pres.shapes.RECTANGLE, { ...box, fill: { color: PLACEHOLDER_FILL }, line: { color: 'C5CAD6', dashType: 'dash', width: 1 } });
    slide.addText(PLACEHOLDER, { ...box, fontFace: T.font, fontSize: 16, color: T.muted, align: 'center', valign: 'middle' });
    return;
  }
  slide.addImage({ path: img.path, ...fit(img, box) });
}

const CHIP_ROW = 0.26;
const chipWidth = (chip) => 0.45 + chip.label.length * 0.075;

function chipRows(list) {
  // number of rows the chips need when they wrap across the body width
  let rows = list.length ? 1 : 0, x = 0;
  for (const chip of list) {
    const w = chipWidth(chip) + 0.25;
    if (x + w > BODY.w && x > 0) { rows += 1; x = 0; }
    x += w;
  }
  return rows;
}

function chips(slide, list) {
  const rows = chipRows(list);
  let x = BODY.x, y = BODY.y + BODY.h - rows * CHIP_ROW + 0.02;
  for (const chip of list) {
    const width = chipWidth(chip);
    if (x + width + 0.25 > BODY.x + BODY.w && x > BODY.x) { x = BODY.x; y += CHIP_ROW; }
    if (chip.kind === 'edge') {
      slide.addShape(pres.shapes.LINE, { x, y: y + 0.1, w: 0.35, h: 0, line: { color: chip.stroke, width: 2, dashType: chip.dashed ? 'dash' : 'solid', endArrowType: 'triangle' } });
    } else {
      slide.addShape(pres.shapes.RECTANGLE, { x, y: y + 0.02, w: 0.32, h: 0.16, fill: chip.fill ? { color: chip.fill } : { type: 'none' }, line: { color: chip.stroke, width: 1, dashType: chip.dashed ? 'dash' : 'solid' } });
    }
    slide.addText(chip.label, { x: x + 0.4, y: y - 0.04, w: width - 0.4, h: 0.28, fontFace: T.font, fontSize: 10, color: T.muted, margin: 0, valign: 'middle' });
    x += width + 0.25;
  }
}

function bullets(slide, items, box, size) {
  const paragraphs = [];
  items.forEach((item) => {
    item.forEach(([text, bold], k) => {
      paragraphs.push({ text, options: { bold: !!bold, bullet: { code: '25CF', indent: 16 }, breakLine: k === item.length - 1, paraSpaceAfter: 10 } });
    });
  });
  slide.addText(paragraphs, { ...box, fontFace: T.font, fontSize: size, color: T.text, valign: 'top', margin: 0.05 });
}

function table(slide, block) {
  const head = block.header.map((cell) => ({ text: runs(cell, { bold: true, color: 'FFFFFF' }), options: { fill: { color: T.primary } } }));
  const body = block.rows.map((row, r) => row.map((cell) => ({ text: runs(cell), options: { fill: { color: r % 2 ? LIGHT : 'FFFFFF' } } })));
  const cols = block.header.length;
  const weights = block.widths && block.widths.length === cols ? block.widths : Array(cols).fill(1);
  const sum = weights.reduce((a, b) => a + b, 0);
  slide.addTable([head, ...body], {
    x: BODY.x, y: BODY.y, w: BODY.w, colW: weights.map((w) => (w / sum) * BODY.w),
    fontFace: T.font, fontSize: 13, color: T.text, valign: 'top', margin: 0.08,
    border: { type: 'solid', pt: 0.5, color: LINE }, autoPage: false,
  });
}

function agenda(slide, items) {
  const half = Math.ceil(items.length / 2), colW = (CW - 0.6) / 2;
  items.forEach((item, k) => {
    const col = k < half ? 0 : 1, row = k < half ? k : k - half;
    const x = X0 + 0.2 + col * (colW + 0.6), y = BODY.y + 0.3 + row * 0.8;
    slide.addShape(pres.shapes.OVAL, { x, y: y + 0.08, w: 0.42, h: 0.42, fill: { color: T.accent }, line: { color: T.accent } });
    slide.addText(String(item.n), { x, y: y + 0.08, w: 0.42, h: 0.42, fontFace: T.font, fontSize: 15, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0 });
    slide.addText(item.title, { x: x + 0.6, y, w: colW - 1.5, h: 0.58, fontFace: T.font, fontSize: 19, bold: true, color: T.primary, valign: 'middle', margin: 0 });
    slide.addText(item.pages, { x: x + colW - 0.9, y, w: 0.8, h: 0.58, fontFace: T.font, fontSize: 13, color: T.muted, align: 'right', valign: 'middle', margin: 0 });
  });
}

function block(slide, b) {
  if (!b) return;
  const legend = b.chips ? chipRows(b.chips) * CHIP_ROW : 0;
  const pictureBox = { x: BODY.x, y: BODY.y, w: BODY.w, h: BODY.h - legend - 0.05 };
  if (b.kind === 'bullets') bullets(slide, b.items, BODY, 20);
  else if (b.kind === 'table') table(slide, b);
  else if (b.kind === 'diagram') { picture(slide, b.images[0], pictureBox); chips(slide, b.chips); }
  else if (b.kind === 'diagrams') {
    const half = (BODY.w - 0.1) / 2;
    picture(slide, b.images[0], { ...pictureBox, w: half });
    picture(slide, b.images[1], { ...pictureBox, x: BODY.x + half + 0.1, w: half });
    chips(slide, b.chips);
  } else if (b.kind === 'diagram-text') {
    const wide = BODY.w * 0.62;
    picture(slide, b.images[0], { ...pictureBox, w: wide });
    bullets(slide, b.items, { x: BODY.x + wide + 0.2, y: BODY.y, w: BODY.w - wide - 0.2, h: pictureBox.h }, 16);
    chips(slide, b.chips);
  } else if (b.kind === 'agenda') agenda(slide, b.agenda);
  else if (b.kind === 'image') picture(slide, b.images[0], BODY);
}

for (const s of deck.slides) {
  if (s.kind === 'cover') {
    const slide = pres.addSlide();
    slide.background = { color: T.primary };
    if (T.logo) {
      const h = 0.81, w = T.logo.h ? (h * T.logo.w) / T.logo.h : h;
      slide.addImage({ path: T.logo.path, x: (W - w) / 2, y: 0.35, w, h });
    }
    slide.addShape(pres.shapes.LINE, { x: 8.75, y: 2.1, w: 0, h: 2.7, line: { color: T.accent, width: 3 } });
    slide.addText(s.title, { x: 0.58, y: 2.0, w: 7.9, h: 2.0, fontFace: T.font, fontSize: 40, bold: true, color: 'FFFFFF', valign: 'bottom', margin: 0, objectName: 'Title' });
    slide.addText(runs(s.message), { x: 0.58, y: 4.15, w: 7.9, h: 0.45, fontFace: T.font, fontSize: 18, color: 'E4E8F4', margin: 0, objectName: 'Message' });
    const lines = [deck.meta.presenter, deck.meta.date].filter((t) => t);
    if (lines.length) slide.addText(lines.join('\n'), { x: 0.58, y: 4.65, w: 7.9, h: 0.8, fontFace: T.font, fontSize: 16, color: 'E4E8F4', margin: 0, valign: 'top' });
    slide.addNotes(s.notes);
    continue;
  }
  const slide = pres.addSlide({ masterName: 'CONTENT' });
  slide.addText(s.title, { x: X0, y: 0.2, w: CW, h: 0.6, fontFace: T.font, fontSize: 28, bold: true, color: T.primary, valign: 'middle', margin: 0, objectName: 'Title' });
  slide.addText(runs(s.message), { x: X0, y: 0.8, w: CW, h: 0.35, fontFace: T.font, fontSize: 15, color: T.muted, valign: 'middle', margin: 0, objectName: 'Message' });
  block(slide, s.block);
  if (deck.meta.footer) slide.addText(deck.meta.footer, { x: X0, y: H - 0.4, w: 8, h: 0.3, fontFace: T.font, fontSize: 10, color: T.muted, margin: 0 });
  slide.addNotes(s.notes);
}

pres.writeFile({ fileName: output })
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error && error.message ? error.message : error);
    process.exit(1);
  });
