from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

# Parse high_school.txt (each line is a word)
words1 = []
with open('high_school.txt', 'r', encoding='utf-8') as f:
    for line in f:
        word = line.strip()
        if word:
            words1.append(word)

# Parse high_school_new.txt (each line is a phrase)
words2 = []
with open('high_school_new.txt', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            words2.append(line)

# Combine all words
all_words = words1 + words2

print(f"Words from high_school.txt: {len(words1)}")
print(f"Words from high_school_new.txt: {len(words2)}")
print(f"Total words: {len(all_words)}")

# A4 dimensions
width, height = A4

# Margins
margin_left = 15 * mm
margin_right = 15 * mm
margin_top = 15 * mm
margin_bottom = 15 * mm

# Calculate usable area
usable_width = width - margin_left - margin_right
usable_height = height - margin_top - margin_bottom

# Font settings
font_name = 'Helvetica'
font_size = 10
line_height = font_size * 1.4

# Create PDF
c = canvas.Canvas('high_school.pdf', pagesize=A4)
c.setFont(font_name, font_size)

# Space between words: 2 spaces
space_count = 2
space_width = c.stringWidth(' ', font_name, font_size)
join_width = space_count * space_width  # Width of the joiner between words

# Calculate lines per page
lines_per_page = int(usable_height / line_height)
print(f"Lines per page: {lines_per_page}")

def wrap_words_to_lines(words, available_width, font_name, font_size):
    """Wrap words into lines so no word is cut"""
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        word_width = c.stringWidth(word, font_name, font_size)
        
        if not current_line:
            current_line.append(word)
            current_width = word_width
        else:
            # Width = current + join_width (space between) + word
            total_width = current_width + join_width + word_width
            
            if total_width > available_width:
                lines.append(current_line[:])
                current_line = [word]
                current_width = word_width
            else:
                current_line.append(word)
                current_width = total_width
    
    if current_line:
        lines.append(current_line)
    
    return lines

lines = wrap_words_to_lines(all_words, usable_width, font_name, font_size)
print(f"Total lines: {len(lines)}")

# Calculate total pages
total_pages = (len(lines) + lines_per_page - 1) // lines_per_page
print(f"Total pages: {total_pages}")

# Draw each page
for page_num in range(total_pages):
    if page_num > 0:
        c.showPage()
        c.setFont(font_name, font_size)
    
    start_line = page_num * lines_per_page
    end_line = min(start_line + lines_per_page, len(lines))
    
    y = height - margin_top - font_size
    
    for line_idx in range(start_line, end_line):
        line_words = lines[line_idx]
        line_text = (' ' * space_count).join(line_words)
        c.drawString(margin_left, y, line_text)
        y -= line_height

# Save PDF
c.save()
print(f"PDF generated: high_school.pdf ({total_pages} pages)")
