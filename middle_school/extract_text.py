import sys
import os
import re
import fitz

# Reconfigure standard output to use utf-8 to avoid encoding errors in the console
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def is_chinese_char_or_punct(char):
    """
    Checks if a character is a Chinese character or a full-width punctuation/symbol.
    """
    if not char:
        return False
    if "\u4e00" <= char <= "\u9fff":
        return True
    if "\u3000" <= char <= "\u303f":
        return True
    if "\uff00" <= char <= "\uffef":
        return True
    return False


def enhance_clean_line(line):
    """
    Applies aggressive textbook-specific cleaning:
    1. Removes phonetic transcriptions like /.../.
    2. Truncates Chinese translations, footnotes, and full-width punctuations.
    3. Truncates part-of-speech abbreviations at the end of word items.
    4. Strips trailing page references.
    5. Converts common unicode punctuation equivalents to ASCII.
    6. Filters down strictly to traditional printable ASCII (chars in [32, 126]).
    """
    # Map common unicode punctuation to ASCII equivalents
    unicode_map = {
        "’": "'",
        "‘": "'",
        "`": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "…": "...",
    }
    for u_char, a_char in unicode_map.items():
        line = line.replace(u_char, a_char)

    # 1. Remove phonetic transcription (enclosed in slashes /.../)
    line = re.sub(r"\s*/[^/]+/\s*", " ", line)

    # 2. Truncate Chinese translation or annotations
    first_chinese_idx = -1
    for idx, char in enumerate(line):
        if is_chinese_char_or_punct(char):
            first_chinese_idx = idx
            break

    if first_chinese_idx != -1:
        line = line[:first_chinese_idx].strip()

    # 3. Remove parts of speech at the end of the English part
    line = re.sub(r"\s+\b(n|adj|adv|v|prep|conj|pron|num|art|int)\b\.?\s*$", "", line)

    # 4. Strip trailing page numbers/digits
    line = re.sub(r"\s*\d+$", "", line)

    # 5. Filter only traditional printable ASCII [32, 126] and strip
    cleaned_chars = []
    for char in line:
        val = ord(char)
        if 32 <= val <= 126:
            cleaned_chars.append(char)

    line = "".join(cleaned_chars).strip()
    return line


def should_skip_line(line):
    """
    Skips page numbers, page headers/footers, and meaningless lines.
    """
    stripped = line.strip()
    if not stripped:
        return True

    # Skip if only digits (page numbers)
    if stripped.isdigit():
        return True

    # Collapse whitespace and check for unit, vocabulary, or section headers
    collapsed = re.sub(r"\s+", "", stripped).lower()

    if "unit" in collapsed:
        return True
    if "vocabulary" in collapsed:
        return True
    if "lookingforwards" in collapsed or "lookingforward" in collapsed:
        return True
    if "namesandplaces" in collapsed:
        return True
    if collapsed == "names" or collapsed == "places":
        return True

    # Skip lines that do not contain any alphanumeric characters
    if not any(c.isalnum() for c in stripped):
        return True

    return False


def clean_text_block(text):
    """
    Cleans a text block by joining internal lines while handling:
    1. Hyphens at line wraps (general lowercase heuristic).
    2. Space injection between English words, while omitting spaces for Chinese text flows.
    3. Removal of control characters like backspaces.
    """
    text = text.replace("\t", " ").replace("\x08", "")
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]

    cleaned_parts = []
    for i, line in enumerate(lines):
        if not line:
            continue
        if i == 0:
            cleaned_parts.append(line)
        else:
            prev_line = cleaned_parts[-1]

            # General Hyphen Heuristic:
            # If the previous line ends with a hyphen and the next line starts with a lowercase letter,
            # we assume it is a word-wrap split and remove the hyphen.
            match_prev = re.search(r"([a-zA-Z]+)-$", prev_line)
            match_next = re.search(r"^([a-zA-Z]+)", line)

            if match_prev and match_next:
                prev_word = match_prev.group(1)
                next_word = match_next.group(1)
                if next_word[0].islower():
                    # Word-wrap hyphen split: remove hyphen
                    cleaned_parts[-1] = prev_line[:-1] + line
                else:
                    # Genuine compound hyphen or capitalized proper hyphen: keep hyphen
                    cleaned_parts[-1] = prev_line[:-1] + "-" + line
            else:
                # Join lines
                last_char = prev_line[-1] if prev_line else ""
                first_char = line[0] if line else ""

                is_chinese_last = is_chinese_char_or_punct(last_char)
                is_chinese_first = is_chinese_char_or_punct(first_char)

                if is_chinese_last or is_chinese_first:
                    # Chinese flow: join without space
                    cleaned_parts[-1] = prev_line + line
                else:
                    # English flow: join with a space
                    cleaned_parts[-1] = prev_line + " " + line

    return " ".join(cleaned_parts)


def sort_page_blocks(blocks, page_width):
    """
    Sorts PDF blocks in logical reading order:
    1. Full-width banners and titles first.
    2. Left column blocks (top-to-bottom).
    3. Right column blocks (top-to-bottom).
    """
    full_width_blocks = []
    other_blocks = []

    for b in blocks:
        x0, y0, x1, y1, text, block_no, block_type = b
        width = x1 - x0
        # If block spans across the middle of the page and is sufficiently wide, treat as full-width
        if (
            x0 < page_width * 0.38
            and x1 > page_width * 0.62
            and width > page_width * 0.4
        ):
            full_width_blocks.append(b)
        else:
            other_blocks.append(b)

    # Sort full-width blocks by their vertical positions
    full_width_blocks.sort(key=lambda x: x[1])

    # Partition other blocks using the horizontal bands created by full-width blocks
    bands = []
    current_y = 0.0
    for fwb in full_width_blocks:
        fy0, fy1 = fwb[1], fwb[3]
        band_blocks = [b for b in other_blocks if b[1] < fy0 and b[1] >= current_y]
        if band_blocks:
            bands.append((current_y, fy0, "columns", band_blocks))
        bands.append((fy0, fy1, "full-width", [fwb]))
        current_y = fy1

    band_blocks = [b for b in other_blocks if b[1] >= current_y]
    if band_blocks:
        bands.append((current_y, float("inf"), "columns", band_blocks))

    sorted_blocks = []
    for band in bands:
        b_start, b_end, b_type, b_list = band
        if b_type == "full-width":
            sorted_blocks.extend(b_list)
        else:
            mid_x = page_width / 2
            left_col = []
            right_col = []

            for b in b_list:
                bx0, by0, bx1, by1 = b[0], b[1], b[2], b[3]
                center_x = (bx0 + bx1) / 2
                if center_x < mid_x:
                    left_col.append(b)
                else:
                    right_col.append(b)

            left_col.sort(key=lambda x: x[1])
            right_col.sort(key=lambda x: x[1])

            sorted_blocks.extend(left_col)
            sorted_blocks.extend(right_col)

    return sorted_blocks


def merge_blocks(sorted_blocks):
    """
    Intelligently merges consecutive blocks that are part of the same paragraph/list item.
    Protects independent elements (bullet items, numbered lists, headings) from being merged.
    """
    merged_texts = []
    current_block = None

    # Bullet/list patterns indicating the start of a new item (should not merge into the previous block)
    bullet_patterns = [
        r"^\s*\*\*+",  # e.g. ** boyhood
        r"^\s*\*+\s",  # e.g. * word
        r"^\s*UNIT\s+\d+",  # e.g. UNIT 1
        r"^\s*➊|➋|➌|➍|➎|➏|➐|➑|➒|➓",  # circle numbers
        r"^\s*\d+[\s\t\.]",  # e.g. 1. or 1\t
    ]

    for b in sorted_blocks:
        x0, y0, x1, y1, text, block_no, block_type = b
        text_clean = clean_text_block(text)
        if not text_clean:
            continue

        if current_block is None:
            current_block = {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "text": text_clean}
        else:
            prev_text = current_block["text"].strip()

            starts_with_bullet = False
            for pat in bullet_patterns:
                if re.match(pat, text_clean):
                    starts_with_bullet = True
                    break

            center_curr = (current_block["x0"] + current_block["x1"]) / 2
            center_new = (x0 + x1) / 2
            same_column = abs(center_curr - center_new) < 120

            y_dist = y0 - current_block["y1"]

            is_continuation = False
            if prev_text:
                last_char = prev_text[-1]
                first_char = text_clean[0]

                is_chinese_last = is_chinese_char_or_punct(last_char)
                is_chinese_first = is_chinese_char_or_punct(first_char)

                # Case 1: Line ended with hyphen
                if last_char == "-":
                    is_continuation = True

                # Case 2: Ended with a clause-splitting punctuation (comma, semicolon)
                elif last_char in (",", "，", ";", "；"):
                    is_continuation = True

                # Case 3: Ended with a letter (not sentence end punctuation) and next starts with lowercase
                elif last_char.isalpha() and first_char.islower():
                    ends_with_sentence_end = last_char in (".", "?", "!", '"', "”", "’")
                    if not ends_with_sentence_end:
                        is_continuation = True

                # Case 4: Ended with a Chinese character (not sentence end punctuation) and next starts with Chinese or lowercase
                elif is_chinese_last and last_char not in ("。", "！", "？", "”"):
                    if is_chinese_first or first_char.islower():
                        is_continuation = True

            should_merge = (
                same_column
                and y_dist < 40
                and is_continuation
                and not starts_with_bullet
            )

            if should_merge:
                # Merge current block with new block
                if prev_text.endswith("-"):
                    current_block["text"] = prev_text[:-1] + text_clean
                else:
                    is_chinese_last_char = is_chinese_char_or_punct(prev_text[-1])
                    is_chinese_first_char = is_chinese_char_or_punct(text_clean[0])
                    if is_chinese_last_char or is_chinese_first_char:
                        current_block["text"] = prev_text + text_clean
                    else:
                        current_block["text"] = prev_text + " " + text_clean
                current_block["y1"] = y1
                current_block["x0"] = min(current_block["x0"], x0)
                current_block["x1"] = max(current_block["x1"], x1)
            else:
                merged_texts.append(current_block["text"])
                current_block = {
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "text": text_clean,
                }

    if current_block:
        merged_texts.append(current_block["text"])

    return merged_texts


def extract_text(pdf_path, output_path):
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found in the current directory.")
        sys.exit(1)

    print(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    print(f"Total pages: {num_pages}")

    lines_written = 0
    with open(output_path, "w", encoding="utf-8") as out_f:
        for page_num in range(1, num_pages + 1):
            page = doc[page_num - 1]
            page_width = page.rect.width

            # Extract raw blocks from the page
            blocks = page.get_text("blocks")
            if not blocks:
                continue

            # Sort blocks to respect columns and logical reading order
            sorted_blocks = sort_page_blocks(blocks, page_width)

            # Intelligently merge lines and blocks into coherent paragraphs/sentences
            merged_lines = merge_blocks(sorted_blocks)

            # Write to output file using enhanced cleaning and skip rules
            for line in merged_lines:
                cleaned_line = enhance_clean_line(line)
                if not should_skip_line(cleaned_line):
                    out_f.write(cleaned_line + "\n")
                    lines_written += 1

            if page_num % 10 == 0 or page_num == num_pages:
                print(f"Processed page {page_num}/{num_pages}...")

    print(f"\nExtraction complete!")
    print(f"Output saved to: {output_path}")
    print(f"Total lines extracted: {lines_written}")


if __name__ == "__main__":
    pdf_file = "普通高中教科书·英语选择性必修 第四册.pdf"
    output_txt = "普通高中教科书·英语选择性必修 第四册.txt"

    extract_text(pdf_file, output_txt)
