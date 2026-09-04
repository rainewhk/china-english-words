import csv
import os
import re


def parse_line(line):
    line = line.strip()
    if not line:
        return None

    # Check if there is a period
    if "。" not in line:
        # No period -> definitely a hint/note/pronunciation
        return ("", line)

    # It contains a period. Check if it's a regular meaning or a general note.
    has_num_prefix = re.match(r"^[\(\（\s]*\d+[\)\）\s\.]|^[①-⑩]|^[A-Za-z]\s*\.", line)

    parts = line.split("。", 1)
    key = parts[0].strip()
    val = parts[1].strip()

    if has_num_prefix:
        # Starts with number -> definitely a meaning item
        return (key, val)

    # Doesn't start with a number. Let's check length of key.
    # If key is short (<= 15 characters), it's probably a direct translation key
    if len(key) <= 15:
        return (key, val)
    else:
        # Key is too long, probably a general note sentence (e.g. "国"本义是"国都"...)
        # Put the whole line in the second column as a note
        return ("", line)


def generate_html_table(explanation):
    lines = [line.strip() for line in explanation.split("\n") if line.strip()]

    table_rows = []
    for line in lines:
        parsed = parse_line(line)
        if not parsed:
            continue
        key, val = parsed

        if not key:
            # Check if it's a pronunciation (only alphabet letters + tone marks)
            is_pron = re.match(r"^[a-zA-Zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ\s]+$", val)
            if is_pron:
                val_html = f'<span class="anki-pron">{val}</span>'
            else:
                val_html = f'<span class="anki-note">{val}</span>'

            table_rows.append(
                f"      <tr>\n"
                f'        <td class="anki-key"></td>\n'
                f'        <td class="anki-val">{val_html}</td>\n'
                f"      </tr>"
            )
        else:
            # Regular key-value meaning pair
            table_rows.append(
                f"      <tr>\n"
                f'        <td class="anki-key">{key}</td>\n'
                f'        <td class="anki-val">{val}</td>\n'
                f"      </tr>"
            )

    rows_str = "\n".join(table_rows)
    return f'<table class="anki-table">\n  <tbody>\n{rows_str}\n  </tbody>\n</table>'


# CSS embedded once in the first card's field.
# Anki applies <style> blocks from any card to the whole session,
# so this is the cleanest way to share styles across all cards.
ANKI_CSS = """<style>
.anki-table {
  width: 100%;
  border-collapse: collapse;
  margin: 6px 0;
  font-size: 14px;
  line-height: 1.6;
}
.anki-table tr {
  border-bottom: 1px solid rgba(128, 128, 128, 0.12);
}
.anki-table tr:last-child {
  border-bottom: none;
}
.anki-key {
  font-weight: 600;
  color: #2563eb;
  padding: 8px 10px;
  width: 32%;
  vertical-align: top;
  text-align: left;
}
.anki-val {
  padding: 8px 10px;
  width: 68%;
  vertical-align: top;
  text-align: left;
  color: #374151;
}
.anki-pron {
  font-weight: 700;
  font-size: 15px;
  color: #7c3aed;
  background-color: rgba(124, 58, 237, 0.08);
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-block;
  font-family: Georgia, serif;
}
.anki-note {
  font-size: 13px;
  color: #059669;
  background-color: rgba(5, 150, 105, 0.08);
  padding: 5px 8px;
  border-radius: 6px;
  display: block;
  margin: 2px 0;
  border-left: 3px solid #10b981;
}
@media (prefers-color-scheme: dark) {
  .anki-key { color: #60a5fa; }
  .anki-val { color: #d1d5db; }
  .anki-pron { color: #a78bfa; background-color: rgba(167, 139, 250, 0.15); }
  .anki-note { color: #34d399; background-color: rgba(52, 211, 153, 0.15); }
}
</style>"""


def main():
    input_path = os.path.join("文言", "120文言实词.CSV")
    output_path = os.path.join("文言", "120文言实词_anki.csv")

    if not os.path.exists(input_path):
        print(f"Error: {input_path} does not exist.")
        return

    print(f"Reading {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    out_rows = []
    for idx, row in enumerate(rows):
        if not row:
            continue
        word = row[0]
        explanation = row[1] if len(row) > 1 else ""

        html_table = generate_html_table(explanation)

        # Embed CSS only in the very first card — Anki propagates it to the whole session
        if idx == 0:
            html_table = ANKI_CSS + "\n" + html_table

        out_rows.append([word, html_table])

    print(f"Writing {output_path}...")
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(out_rows)

    print("Conversion completed successfully!")
    print(f"Total processed words: {len(out_rows)}")


if __name__ == "__main__":
    main()
