import csv
from collections import OrderedDict, defaultdict
from pathlib import Path

INPUT = Path('BMG5205 Assignment 1 CSVversion.csv')
OUT_DIR = Path('analysis_output')
OUT_DIR.mkdir(exist_ok=True)

score_map = {'Full': 2, 'Partial': 1, 'No': 0}
color_map = {2: '#2e7d32', 1: '#f9a825', 0: '#c62828'}

items = OrderedDict()
ctx = {}
with INPUT.open(encoding='utf-8-sig', newline='') as fh:
    reader = csv.DictReader(fh)
    for row in reader:
        for key in ['Company Name', 'TCFD Recommendation', 'Recommended Disclosure', 'Description']:
            value = row[key].strip()
            if value:
                ctx[key] = value
            else:
                row[key] = ctx.get(key, '')

        identifier = row['Identifier'].strip()
        status = row['Full/Partial/No'].strip().title()

        if identifier not in items:
            items[identifier] = {
                'company': row['Company Name'].strip(),
                'recommendation': row['TCFD Recommendation'].strip(),
                'disclosure': row['Recommended Disclosure'].strip(),
                'status': status,
            }
        elif not items[identifier]['status'] and status:
            items[identifier]['status'] = status

agg = defaultdict(list)
for record in items.values():
    status = record['status']
    if status in score_map:
        key = (record['recommendation'], record['disclosure'])
        agg[key].append(score_map[status])

ordered = sorted(agg.items(), key=lambda kv: (kv[0][0], kv[0][1]))

rows = []
for (rec, disclosure), scores in ordered:
    avg = sum(scores) / len(scores)
    rounded = int(round(avg))
    label = {2: 'Full', 1: 'Partial', 0: 'No'}[rounded]
    rows.append({
        'recommendation': rec,
        'disclosure': disclosure,
        'count': len(scores),
        'avg_score': avg,
        'status': label,
        'status_score': rounded,
    })

# Write CSV summary
summary_csv = OUT_DIR / 'disclosure_scores.csv'
with summary_csv.open('w', encoding='utf-8', newline='') as fh:
    writer = csv.DictWriter(
        fh,
        fieldnames=['recommendation', 'disclosure', 'count', 'avg_score', 'status', 'status_score']
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

# Build simple SVG heatmap (one cell per disclosure)
cell_w = 520
cell_h = 34
left_label = 360
top = 70
width = left_label + cell_w + 40
height = top + len(rows) * cell_h + 60

svg_lines = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    '<style>',
    'text { font-family: Arial, sans-serif; fill: #222; }',
    '.title { font-size: 18px; font-weight: bold; }',
    '.label { font-size: 12px; }',
    '.celltext { font-size: 12px; font-weight: bold; fill: #fff; }',
    '</style>',
    '<text x="20" y="30" class="title">TCFD Recommended Disclosure Heatmap (Wilmar)</text>',
    '<text x="20" y="50" class="label">Scoring: Full=2, Partial=1, No=0 (higher is better)</text>',
]

for i, row in enumerate(rows):
    y = top + i * cell_h
    fill = color_map[row['status_score']]
    name = f"{row['recommendation']} / {row['disclosure']}"
    svg_lines.append(f'<text x="20" y="{y + 21}" class="label">{name}</text>')
    svg_lines.append(
        f'<rect x="{left_label}" y="{y}" width="{cell_w}" height="{cell_h - 2}" fill="{fill}" rx="4" ry="4"/>'
    )
    svg_lines.append(
        f'<text x="{left_label + 10}" y="{y + 21}" class="celltext">{row["status"]} (avg={row["avg_score"]:.2f}, n={row["count"]})</text>'
    )

legend_y = top + len(rows) * cell_h + 20
svg_lines.append(f'<text x="20" y="{legend_y}" class="label">Legend:</text>')
legend = [('Full', 2), ('Partial', 1), ('No', 0)]
for idx, (name, val) in enumerate(legend):
    x = 80 + idx * 170
    svg_lines.append(f'<rect x="{x}" y="{legend_y - 12}" width="24" height="16" fill="{color_map[val]}" rx="3"/>')
    svg_lines.append(f'<text x="{x + 32}" y="{legend_y}" class="label">{name}={val}</text>')

svg_lines.append('</svg>')

heatmap_svg = OUT_DIR / 'disclosure_heatmap.svg'
heatmap_svg.write_text('\n'.join(svg_lines), encoding='utf-8')

# Write markdown insights
md = OUT_DIR / 'analysis_summary.md'
best = max(rows, key=lambda r: r['avg_score'])
worst = min(rows, key=lambda r: r['avg_score'])
md.write_text(
    '\n'.join([
        '# Spreadsheet Analysis Summary',
        '',
        f'- Total unique identifiers scored: {sum(r["count"] for r in rows)}',
        f'- Best disclosure area: {best["recommendation"]} / {best["disclosure"]} (avg={best["avg_score"]:.2f})',
        f'- Lowest disclosure area: {worst["recommendation"]} / {worst["disclosure"]} (avg={worst["avg_score"]:.2f})',
        '',
        'Heatmap file: `analysis_output/disclosure_heatmap.svg`',
        'Detailed scores file: `analysis_output/disclosure_scores.csv`',
    ]),
    encoding='utf-8'
)

print(f'Wrote: {heatmap_svg}')
print(f'Wrote: {summary_csv}')
print(f'Wrote: {md}')
