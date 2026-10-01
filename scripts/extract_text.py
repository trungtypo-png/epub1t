import os
import sys
import re
import uuid
import zipfile
import io
import pymupdf
from PIL import Image

# Support UTF-8 output across platforms
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# High-precision AVn / ABC / VNI single-pass replacement rules
_AVN_RULES = [
    # 3-char composite vowels (lowercase & uppercase)
    ('ûúâ', 'ườ'), ('ûúá', 'ướ'), ('ûúä', 'ưỡ'), ('ûúå', 'ượ'), ('ûúã', 'ưở'), ('ûú', 'ươ'),
    ('Ûúâ', 'Ườ'), ('Ûúá', 'Ướ'), ('Ûúä', 'Ưỡ'), ('Ûúå', 'Ượ'), ('Ûúã', 'Ưưở'), ('Ûú', 'Ươ'),
    ('ÛÚÂ', 'ƯỜ'), ('ÛÚÁ', 'ƯỚ'), ('ÛÚÄ', 'ƯỠ'), ('ÛÚÅ', 'ƯỢ'), ('ÛÚÃ', 'ƯỞ'), ('ÛÚ', 'ƯƠ'),
    ('ƯƠÂ', 'ƯỜ'), ('ƯƠÁ', 'ƯỚ'), ('ƯƠÄ', 'ƯỠ'), ('ƯƠÅ', 'ƯỢ'), ('ƯƠÃ', 'ƯỞ'),
    
    ('uöë', 'uố'), ('uöì', 'uồ'), ('uöí', 'uổ'), ('uöä', 'uỗ'), ('uöå', 'uộ'), ('uöî', 'uỗ'), ('uö', 'uô'),
    ('Uöë', 'Uố'), ('Uöì', 'Uồ'), ('Uöí', 'Uổ'), ('Uöä', 'Uỗ'), ('Uöå', 'Uộ'), ('Uöî', 'Uỗ'), ('Uö', 'Uô'),
    ('UÖË', 'UỐ'), ('UÖÌ', 'UỒ'), ('UÖÍ', 'UỔ'), ('UÖÄ', 'UỖ'), ('UÖÅ', 'UỘ'), ('UÖÎ', 'UỖ'), ('UÖ', 'UÔ'),

    ('iïë', 'iế'), ('iïì', 'iề'), ('iïí', 'iể'), ('iïä', 'iễ'), ('iïå', 'iệ'), ('iïî', 'iễ'), ('iï', 'iê'),
    ('Iïë', 'Iế'), ('Iïì', 'Iề'), ('Iïí', 'Iể'), ('Iïä', 'Iễ'), ('Iïå', 'Iệ'), ('Iïî', 'Iễ'), ('Iï', 'Iê'),
    ('IÏË', 'IẾ'), ('IÏÌ', 'IỀ'), ('IÏÍ', 'IỂ'), ('IÏÄ', 'IỄ'), ('IÏÅ', 'IỆ'), ('IÏÎ', 'IỄ'), ('IÏ', 'IÊ'),

    ('yïë', 'yế'), ('yïì', 'yề'), ('yïí', 'yể'), ('yïä', 'yễ'), ('yïå', 'yệ'), ('yïî', 'yễ'), ('yï', 'yê'),
    ('Yïë', 'Yế'), ('Yïì', 'Yề'), ('Yïí', 'Yể'), ('Yïä', 'Yễ'), ('Yïå', 'Yệ'), ('Yïî', 'Yễ'), ('Yï', 'Yê'),
    ('YÏË', 'YẾ'), ('YÏÌ', 'YỀ'), ('YÏÍ', 'YỂ'), ('YÏÄ', 'YỄ'), ('YÏÅ', 'YỆ'), ('YÏÎ', 'YỄ'), ('YÏ', 'YÊ'),

    # 2-char ă (ù / Ù / Ă)
    ('ùæ', 'ắ'), ('ùç', 'ằ'), ('ùè', 'ẳ'), ('ùã', 'ẳ'), ('ùä', 'ẵ'), ('ùé', 'ẵ'), ('ùå', 'ặ'),
    ('Ùæ', 'Ắ'), ('Ùç', 'Ằ'), ('Ùè', 'Ẳ'), ('Ùã', 'Ẳ'), ('Ùä', 'Ẵ'), ('Ùé', 'Ẵ'), ('Ùå', 'Ặ'),
    ('ÙÆ', 'Ắ'), ('ÙÇ', 'Ằ'), ('ÙÈ', 'Ẳ'), ('ÙÃ', 'Ẳ'), ('ÙÄ', 'Ẵ'), ('ÙÉ', 'Ẵ'), ('ÙÅ', 'Ặ'),
    ('ĂÆ', 'Ắ'), ('ĂÇ', 'Ằ'), ('ĂÈ', 'Ẳ'), ('ĂÃ', 'Ẳ'), ('ĂÄ', 'Ẵ'), ('ĂÅ', 'Ặ'),

    # 2-char â (ê / Ê / Â)
    ('êë', 'ấ'), ('êì', 'ầ'), ('êí', 'ẩ'), ('êä', 'ẫ'), ('êî', 'ẫ'), ('êå', 'ậ'),
    ('Êë', 'Ấ'), ('Êì', 'Ầ'), ('Êí', 'Ẩ'), ('Êä', 'Ẫ'), ('Êî', 'Ẫ'), ('Êå', 'Ậ'),
    ('ÊË', 'Ấ'), ('ÊÌ', 'Ầ'), ('ÊÍ', 'Ẩ'), ('ÊÄ', 'Ẫ'), ('ÊÎ', 'Ẫ'), ('ÊÅ', 'Ậ'),
    ('ÂË', 'Ấ'), ('ÂÌ', 'Ầ'), ('ÂÍ', 'Ẩ'), ('ÂÄ', 'Ẫ'), ('ÂÎ', 'Ẫ'), ('ÂÅ', 'Ậ'),

    # 2-char ê (ï / Ï / Ê)
    ('ïë', 'ế'), ('ïì', 'ề'), ('ïí', 'ể'), ('ïä', 'ễ'), ('ïî', 'ễ'), ('ïå', 'ệ'),
    ('Ïë', 'Ế'), ('Ïì', 'Ề'), ('Ïí', 'Ể'), ('Ïä', 'Ễ'), ('Ïî', 'Ễ'), ('Ïå', 'Ệ'),
    ('ÏË', 'Ế'), ('ÏÌ', 'Ề'), ('ÏÍ', 'Ể'), ('ÏÄ', 'Ễ'), ('ÏÎ', 'Ễ'), ('ÏÅ', 'Ệ'),

    # 2-char ô (ö / Ö / Ô)
    ('öë', 'ố'), ('öì', 'ồ'), ('öí', 'ổ'), ('öä', 'ỗ'), ('öî', 'ỗ'), ('öå', 'ộ'),
    ('Öë', 'Ố'), ('Öì', 'Ồ'), ('Öí', 'Ổ'), ('Öä', 'Ỗ'), ('Öî', 'Ỗ'), ('Öå', 'Ộ'),
    ('ÖË', 'Ố'), ('ÖÌ', 'Ồ'), ('ÖÍ', 'Ổ'), ('ÖÄ', 'Ỗ'), ('ÖÎ', 'Ỗ'), ('ÖÅ', 'Ộ'),
    ('ÔË', 'Ố'), ('ÔÌ', 'Ồ'), ('ÔÍ', 'Ổ'), ('ÔÄ', 'Ỗ'), ('ÔÎ', 'Ỗ'), ('ÔÅ', 'Ộ'),

    # 2-char ơ (ú / Ú / Ơ)
    ('úá', 'ớ'), ('úâ', 'ờ'), ('úã', 'ở'), ('úä', 'ỡ'), ('úå', 'ợ'),
    ('Úá', 'Ớ'), ('Úâ', 'Ờ'), ('Úã', 'Ở'), ('Úä', 'Ỡ'), ('Úå', 'Ợ'),
    ('ÚÁ', 'Ớ'), ('ÚÂ', 'Ờ'), ('ÚÃ', 'Ở'), ('ÚÄ', 'Ỡ'), ('ÚÅ', 'Ợ'),
    ('ƠÁ', 'Ớ'), ('ƠÂ', 'Ờ'), ('ƠÃ', 'Ở'), ('ƠÄ', 'Ỡ'), ('ƠÅ', 'Ợ'),

    # 2-char ư (û / Û / Ư)
    ('ûá', 'ứ'), ('ûâ', 'ừ'), ('ûã', 'ử'), ('ûä', 'ữ'), ('ûå', 'ự'),
    ('Ûá', 'Ứ'), ('Ûâ', 'Ừ'), ('Ûã', 'Ử'), ('Ûä', 'Ữ'), ('Ûå', 'Ự'),
    ('ÛÁ', 'Ứ'), ('ÛÂ', 'Ừ'), ('ÛÃ', 'Ử'), ('ÛÄ', 'Ữ'), ('ÛÅ', 'Ự'),
    ('ƯÁ', 'Ứ'), ('ƯÂ', 'Ừ'), ('ƯÃ', 'Ử'), ('ƯÄ', 'Ữ'), ('ƯÅ', 'Ự'),

    # 2-char simple vowels + diacritics
    ('aá', 'á'), ('aâ', 'à'), ('aã', 'ả'), ('aä', 'ã'), ('aå', 'ạ'),
    ('Aá', 'Á'), ('Aâ', 'À'), ('Aã', 'Ả'), ('Aä', 'Ã'), ('Aå', 'Ạ'),
    ('AÁ', 'Á'), ('AÂ', 'À'), ('AÃ', 'Ả'), ('AÄ', 'Ã'), ('AÅ', 'Ạ'),
    
    ('eá', 'é'), ('eâ', 'è'), ('eã', 'ẻ'), ('eä', 'ẽ'), ('eå', 'ẹ'),
    ('Eá', 'É'), ('Eâ', 'È'), ('Eã', 'Ẻ'), ('Eä', 'Ẽ'), ('Eå', 'Ẹ'),
    ('EÁ', 'É'), ('EÂ', 'È'), ('EÃ', 'Ẻ'), ('EÄ', 'Ẽ'), ('EÅ', 'Ẹ'),

    ('oá', 'ó'), ('oâ', 'ò'), ('oã', 'ỏ'), ('oä', 'õ'), ('oå', 'ọ'),
    ('Oá', 'Ó'), ('Oâ', 'Ò'), ('Oã', 'Ỏ'), ('Oä', 'Õ'), ('Oå', 'Ọ'),
    ('OÁ', 'Ó'), ('OÂ', 'Ò'), ('OÃ', 'Ỏ'), ('OÄ', 'Õ'), ('OÅ', 'Ọ'),

    ('uá', 'ú'), ('uâ', 'ù'), ('uã', 'ủ'), ('uä', 'ũ'), ('uå', 'ụ'),
    ('Uá', 'Ú'), ('Uâ', 'Ù'), ('Uã', 'Ủ'), ('Uä', 'Ũ'), ('Uå', 'Ụ'),
    ('UÁ', 'Ú'), ('UÂ', 'Ù'), ('UÃ', 'Ủ'), ('UÄ', 'Ũ'), ('UÅ', 'Ụ'),

    ('yá', 'ý'), ('yâ', 'ỳ'), ('yã', 'ỷ'), ('yä', 'ỹ'), ('yå', 'ỵ'),
    ('Yá', 'Ý'), ('Yâ', 'Ỳ'), ('Yã', 'Ỷ'), ('Yä', 'Ỹ'), ('Yå', 'Ỵ'),
    ('YÁ', 'Ý'), ('YÂ', 'Ỳ'), ('YÃ', 'Ỷ'), ('YÄ', 'Ỹ'), ('YÅ', 'Ỵ'),

    # Contextual 'i hỏi' & special diacritics
    ('chó', 'chỉ'), ('Chó', 'Chỉ'), ('CHÓ', 'CHỈ'),
    ('kó', 'kỉ'), ('Kó', 'Kỉ'), ('KÓ', 'KỈ'),
    ('tó', 'tỉ'), ('Tó', 'Tỉ'), ('TÓ', 'TỈ'),
    ('nhó', 'nhỉ'), ('Nhó', 'Nhỉ'), ('NHÓ', 'NHỈ'),
    ('bó', 'bỉ'), ('Bó', 'Bỉ'), ('BÓ', 'BỈ'),
    ('mó', 'mỉ'), ('Mó', 'Mỉ'), ('MÓ', 'MỈ'),
    ('àó', 'đỉ'), ('Àó', 'Đỉ'), ('ÀÓ', 'ĐỈ'),
    ('đó', 'đỉ'), ('Đó', 'Đỉ'), ('ĐÓ', 'ĐỈ'),
    ('hó', 'hỉ'), ('Hó', 'Hỉ'), ('HÓ', 'HỈ'),
    ('só', 'sỉ'), ('Só', 'Sỉ'), ('SÓ', 'SỈ'),
    ('dó', 'dỉ'), ('Dó', 'Dỉ'), ('DÓ', 'DỈ'),

    # Specific word fixes
    ('nghôa', 'nghĩa'), ('Nghôa', 'Nghĩa'), ('NGHÔA', 'NGHĨA'),
    ('nghô', 'nghĩ'), ('Nghô', 'Nghĩ'), ('NGHÔ', 'NGHĨ'),

    # Single-character replacements
    ('ù', 'ă'), ('Ù', 'Ă'),
    ('ê', 'â'), ('Ê', 'Â'),
    ('ï', 'ê'), ('Ï', 'Ê'),
    ('ö', 'ô'), ('Ö', 'Ô'),
    ('ú', 'ơ'), ('Ú', 'Ơ'),
    ('û', 'ư'), ('Û', 'Ư'),
    ('ñ', 'í'), ('Ñ', 'Í'),
    ('ò', 'ì'), ('Ò', 'Ì'),
    ('õ', 'ị'), ('Õ', 'Ị'),
    ('à', 'đ'), ('À', 'Đ'),
]

_AVN_DICT = dict(_AVN_RULES)
_AVN_REGEX = re.compile('|'.join(re.escape(k) for k in sorted(_AVN_DICT.keys(), key=len, reverse=True)))

_AVN_MARKERS = [
    'àaä', 'nhûäng', 'àûúåc', 'khöng', 'ngûúâi', 'thïë', 'rêët', 'bùæt',
    'viïåc', 'àiïìu', 'cöng', 'vúái', 'cuãa', 'phaãi', 'rùçng', 'àïën',
    'thaânh', 'thúâi', 'chuáng', 'phêìn', 'àêìu', 'maáy', 'caác'
]


def decode_avn(text):
    """Decodes AVn / legacy Vietnamese font tokens into clean Unicode UTF-8."""
    return _AVN_REGEX.sub(lambda m: _AVN_DICT[m.group(0)], text)


def clean_vietnamese_text(text):
    """
    Complete Vietnamese text sanitization pipeline:
    1. Decodes legacy AVn / ABC / VNI diacritics into standard UTF-8.
    2. Strips dangling/floating accent marks (diacritic ghosting).
    3. Contextually fixes edge-case words (vĩnh, vẫn, diễn, mỗi, chẳng, ngỗ ngược, tiến sĩ, v.v.).
    """
    decoded = decode_avn(text)
    
    # Strip dangling/floating accents (acute, grave, circumflex, tilde ghosting)
    decoded = re.sub(r'([a-zA-Z\u00C0-\u1EF9])[\u00B4\u0060\^~´`]', r'\1', decoded)
    
    # Contextual post-cleanups
    fixes = [
        (r'\bnghô\b', 'nghĩ'), (r'\bNghô\b', 'Nghĩ'), (r'\bNGHÔ\b', 'NGHĨ'),
        (r'\bvônh\b', 'vĩnh'), (r'\bVônh\b', 'Vĩnh'),
        (r'\bvâîn\b', 'vẫn'), (r'\bVâîn\b', 'Vẫn'),
        (r'\bvân\b(?=\s+(?:tiếp tục|còn|là|như|cứ|giữ))', 'vẫn'),
        (r'\bdiên\b(?=\s+(?:ra|đạt|tiến|giả|viên))', 'diễn'),
        (r'\bmôi\b(?=\s+(?:lần|ngày|người|khi|năm|tháng))', 'mỗi'),
        (r'\bchăèng\b', 'chẳng'),
        (r'\bngôî\b', 'ngỗ'),
        (r'\bhấp dâîn\b', 'hấp dẫn'),
        (r'\bchỉ dâîn\b', 'chỉ dẫn'),
        (r'\btàn nhâîn\b', 'tàn nhẫn'),
        (r'\bhọa sô\b', 'họa sĩ'), (r'\bHọa sô\b', 'Họa sĩ'),
        (r'\btiến sô\b', 'tiến sĩ'), (r'\bTiến sô\b', 'Tiến sĩ'),
        (r'\bnghệ sô\b', 'nghệ sĩ'), (r'\bNghệ sô\b', 'Nghệ sĩ'),
        (r'\blônh\b(?=\s+(?:vực|đạo))', 'lĩnh'),
        (r'\bthủ lônh\b', 'thủ lĩnh'),
        (r'\bđiềm tônh\b', 'điềm tĩnh'),
        (r'\bđónh\b', 'đỉnh'),
        (r'\bĐÓNH\b', 'ĐỈNH'),
    ]
    for pattern, repl in fixes:
        decoded = re.sub(pattern, repl, decoded, flags=re.IGNORECASE)
        
    return decoded


def is_avn_encoded(text):
    """
    Detects whether a given text chunk exhibits hallmark signatures of AVn encoding.
    Checks both lowercase token patterns and uppercase title patterns.
    """
    matches = sum(1 for m in _AVN_MARKERS if m in text)
    if matches >= 2:
        return True
    upper_signatures = ['ÀAÄ', 'VAÂ', 'TÖÍNG', 'BIÏN', 'NGUYÏÎN', 'XUÊËT', 'BAÃN', 'ÀÛÚÂNG', 'MÖÅT', 'ÛÚÃ', 'ÛÚÁ', 'ÛÚÂ', 'ÙÆ', 'ÙÇ', 'ÙÅ']
    if any(s in text for s in upper_signatures):
        return True
    if re.search(r'[ÛÚÖÏÊÙ][ÁÂÃÄÅÆÇËÌÍÑÒÕ]', text):
        return True
    return False


def is_header_footer_or_watermark(line, page_num):
    """
    Identifies repeated headers, footers, standalone page numbers, and site watermarks.
    Protects real content (e.g. model numbers like '8080') by verifying page distance.
    """
    s = line.strip()
    if not s:
        return False
        
    # Check watermark / promotional links
    if re.search(r'(chiasemoi\.com|thuviensach|tve-4u|quangduc|chia\s+sẻ\s+ebook|download|facebook\.com|zalo\.me|e-thuvien)', s, re.IGNORECASE):
        return True
        
    # Check standalone page number: must match within +/- 5 pages of current page
    m_num = re.match(r'^[\-\[\(]?\s*(\d{1,4})\s*[\-\]\)]?$', s)
    if m_num:
        val = int(m_num.group(1))
        if abs(val - page_num) <= 5:
            return True
            
    # Running header pattern 1: "<num> • <book title>" or "<num> - <book title>"
    m = re.match(r'^(\d{1,4})[\s\.\-—–•·/]+(.{2,50})$', s)
    if m:
        num = int(m.group(1))
        if abs(num - page_num) <= 5:
            return True
            
    # Running header pattern 2: "<book title> • <num>" or "<book title> - <num>"
    m2 = re.match(r'^(.{2,50})[\s\.\-—–•·/]+(\d{1,4})$', s)
    if m2:
        num = int(m2.group(2))
        if abs(num - page_num) <= 5:
            return True

    return False


CHAPTER_PATTERNS = [
    re.compile(r'^(?:Chương|CHƯƠNG)\s+(?:[0-9IVXLCDM]+|một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười|nhất|nhì|tam|tứ)\b(?:[\s:\.\-—–].*)?$', re.IGNORECASE),
    re.compile(r'^(?:Phần|PHẦN)\s+(?:[0-9IVXLCDM]+|một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười|nhất|nhì|tam|tứ)\b(?:[\s:\.\-—–].*)?$', re.IGNORECASE),
    re.compile(r'^(?:Hồi|HỒI)\s+(?:[0-9IVXLCDM]+)(?:[\s:\.\-—–].*)?$', re.IGNORECASE),
    re.compile(r'^(?:Mục lục|MỤC LỤC|Table of Contents|LỜI NÓI ĐẦU|Lời nói đầu|LỜI MỞ ĐẦU|Lời mở đầu|LỜI TỰA|Lời tựa|LỜI BẠT|Lời bạt|VĨ THANH|Vĩ thanh|KẾT LUẬN|Kết luận|PHỤ LỤC|Phụ lục|TÀI LIỆU THAM KHẢO|Tài liệu tham khảo)$', re.IGNORECASE),
]


def is_chapter_heading(line):
    """Detects whether a line represents a major chapter or section title."""
    s = line.strip()
    if len(s) < 3 or len(s) > 90:
        return False
    # Avoid lines ending with normal sentence punctuation
    if s.endswith(('.', ',', ';', ':', '!', '?')):
        return False
    # Avoid bullet points and list indicators
    if s.startswith(('•', '·', '-', '*', '–', '—', '+')):
        return False
        
    for p in CHAPTER_PATTERNS:
        if p.match(s):
            return True
            
    # Check if ALL UPPERCASE letters (allowing spaces and standard punctuation)
    letters = re.findall(r'[a-zA-Z\u00C0-\u1EF9]', s)
    if len(letters) >= 6 and all(c.isupper() for c in letters):
        # Exclude running header phrases
        if not re.search(r'\b(?:trang|page)\b', s, re.IGNORECASE):
            return True

    return False


def lines_to_paragraphs(lines):
    """
    Intelligently joins lines into natural reflowable paragraphs:
    - Merges soft line breaks within sentences.
    - Resolves end-of-line hyphenation ('kinh-' + 'doanh' -> 'kinh doanh', 'Micro-' + 'Soft' -> 'Microsoft').
    - Preserves bullet points and blockquotes.
    - Accurately identifies true paragraph boundaries.
    """
    paragraphs = []
    curr_para = []

    def flush_curr():
        if curr_para:
            text = ' '.join(curr_para).strip()
            text = re.sub(r'[ \t]+', ' ', text)
            if text:
                paragraphs.append(text)
            curr_para.clear()

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            flush_curr()
            continue

        is_bullet = bool(re.match(r'^[•·*–—-]\s+', line))
        
        # De-hyphenation handling
        if curr_para and curr_para[-1].endswith(('-', '—')):
            prev = curr_para.pop()
            m_hyphen = re.match(r'^(.*?)(\w+)[-—]$', prev)
            if m_hyphen:
                prefix = m_hyphen.group(1)
                part1 = m_hyphen.group(2)
                m_next = re.match(r'^(\w+)(.*)$', line)
                if m_next:
                    part2 = m_next.group(1)
                    rest = m_next.group(2)
                    joined_word = f"{part1}{part2}" if (len(part1) > 2 and len(part2) > 2 and part2.islower()) else f"{part1} {part2}"
                    combined = f"{prefix}{joined_word}{rest}".strip()
                    curr_para.append(combined)
                    continue

        if is_bullet:
            flush_curr()
            curr_para.append(line)
            continue

        if not curr_para:
            curr_para.append(line)
        else:
            prev_line = curr_para[-1]
            if prev_line.endswith(('.', '!', '?', '”', '"', '…', ':')):
                if len(prev_line) < 55:
                    flush_curr()
                    curr_para.append(line)
                else:
                    curr_para.append(line)
            else:
                curr_para.append(line)

    flush_curr()
    return paragraphs


def get_tessdata_path(custom_path=None):
    """Locates the tessdata directory for PyMuPDF OCR."""
    if custom_path and os.path.isdir(custom_path):
        return custom_path
    
    env_p = os.environ.get('TESSDATA_PREFIX')
    if env_p and os.path.isdir(env_p):
        return env_p
        
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tessdata'),
        r'D:\github\tessdata',
        r'C:\Program Files\Tesseract-OCR\tessdata',
        r'C:\tessdata',
        r'/usr/share/tesseract-ocr/4.00/tessdata',
        r'/usr/share/tessdata',
    ]
    for c in candidates:
        if os.path.isdir(c) and os.path.exists(os.path.join(c, 'vie.traineddata')):
            return c
    for c in candidates:
        if os.path.isdir(c):
            return c
    return None


def extract_pdf_pages_text(pdf_path, ocr_lang='vie', tessdata_path=None, progress_callback=None):
    """
    Extracts high-accuracy text from each PDF page:
    1. Direct selectable text layer (if >= 30 chars).
    2. Intelligent AVn font decoding ONLY if AVn diacritics are detected (preserves standard Unicode).
    3. Automatic fallback to PyMuPDF OCR only for scanned documents (skips graphic/logo plates in digital PDFs).
    """
    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    tess_dir = get_tessdata_path(tessdata_path)
    
    text_page_count = sum(1 for p in doc if len(p.get_text().strip()) >= 30)
    is_digital_pdf = (text_page_count / total_pages) >= 0.80
    
    pages_text = []

    for idx, page in enumerate(doc):
        if progress_callback:
            try:
                progress_callback(idx + 1, total_pages)
            except Exception:
                pass

        # Page 0 is the cover, omit from text extraction to avoid OCR noise
        if idx == 0:
            pages_text.append("")
            continue

        raw_text = page.get_text()
        clean_text = ""

        if len(raw_text.strip()) >= 30:
            if is_avn_encoded(raw_text):
                clean_text = clean_vietnamese_text(raw_text)
            else:
                # Standard Unicode: clean dangling diacritics, keep standard vowels intact
                clean_text = re.sub(r'([a-zA-Z\u00C0-\u1EF9])[\u00B4\u0060\^~´`]', r'\1', raw_text)
        else:
            if not is_digital_pdf and tess_dir:
                try:
                    tp = page.get_textpage_ocr(language=ocr_lang, tessdata=tess_dir, dpi=150)
                    ocr_text = tp.extractText()
                    if len(ocr_text.strip()) >= 30:
                        clean_text = clean_vietnamese_text(ocr_text) if is_avn_encoded(ocr_text) else ocr_text
                except Exception:
                    clean_text = ""
            else:
                clean_text = ""

        pages_text.append(clean_text)

    return pages_text


def export_pdf_to_txt(pdf_path, txt_path=None, ocr_lang='vie', tessdata_path=None, progress_callback=None):
    """
    Extracts text and saves to a clean, well-formatted UTF-8 text file with real chapters and reflowable paragraphs.
    """
    if txt_path is None:
        txt_path = os.path.splitext(pdf_path)[0] + '.txt'

    pages = extract_pdf_pages_text(pdf_path, ocr_lang=ocr_lang, tessdata_path=tessdata_path, progress_callback=progress_callback)
    
    with open(txt_path, 'w', encoding='utf-8') as f:
        for p_idx, page_content in enumerate(pages, 1):
            trimmed = page_content.strip()
            if trimmed:
                f.write(trimmed)
                f.write('\n\n')

    return True, txt_path


def export_pdf_to_reflowable_epub(pdf_path, epub_path=None, ocr_lang='vie', tessdata_path=None, progress_callback=None):
    """
    Converts PDF into a standard reflowable EPUB 3 book:
    - Real chapters & working Table of Contents (TOC).
    - Preserves and embeds all interior illustrations, portraits, and diagrams.
    - Running headers, footers, and site watermarks stripped.
    - Natural reflowable paragraph merging and de-hyphenation.
    - High-resolution authentic cover image on cover.xhtml.
    - Beautiful modern e-reader typography CSS.
    - Generates both EPUB 3 nav.xhtml and EPUB 2 toc.ncx for universal e-reader compatibility.
    """
    if epub_path is None:
        epub_path = os.path.splitext(pdf_path)[0] + '_text.epub'

    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    title = filename
    author = 'Unknown Author'
    if ' - ' in filename:
        parts = filename.split(' - ', 1)
        title = parts[0].strip()
        author = parts[1].strip()

    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    book_uuid = str(uuid.uuid4())

    text_page_count = sum(1 for p in doc if len(p.get_text().strip()) >= 30)
    is_digital_pdf = (text_page_count / total_pages) >= 0.80

    # Extract authentic cover image from page 0
    p0 = doc[0]
    cover_bytes = None
    imgs0 = p0.get_images()
    if imgs0:
        try:
            base_info = doc.extract_image(imgs0[0][0])
            cover_bytes = base_info['image']
        except Exception:
            pass
    if cover_bytes is None:
        pix = p0.get_pixmap(dpi=150)
        cover_bytes = pix.tobytes(output='jpg')

    manifest_items = [
        '        <item id="style" href="Styles/style.css" media-type="text/css"/>'
    ]
    spine_items = []
    toc_nav_points = []
    nav_ol_items = []
    all_images_to_write = []

    # Process all pages from index 1 to total_pages - 1
    pages_data = []
    for p_idx in range(1, total_pages):
        if progress_callback:
            try:
                progress_callback(p_idx + 1, total_pages)
            except Exception:
                pass

        page_num = p_idx + 1
        page = doc[p_idx]
        raw_text = page.get_text()

        # Extract embedded illustrations on this page
        p_imgs = []
        for img_idx, img_info in enumerate(page.get_images()):
            xref = img_info[0]
            w, h = img_info[2], img_info[3]
            if w < 80 or h < 80:
                continue
            try:
                base_img = doc.extract_image(xref)
                im_bytes = base_img['image']
                ext = base_img['ext']
                if len(im_bytes) < 1500:
                    continue
                img_rel = f"Images/img_p{page_num:03d}_{img_idx+1:02d}.{ext}"
                item_id = f"img_p{page_num:03d}_{img_idx+1:02d}"
                mime = f"image/{ext}" if ext != 'jpg' else 'image/jpeg'
                p_imgs.append(img_rel)
                manifest_items.append(f'        <item id="{item_id}" href="{img_rel}" media-type="{mime}"/>')
                all_images_to_write.append((f"OEBPS/{img_rel}", im_bytes))
            except Exception:
                pass

        # Text extraction & decoding
        cleaned_text = ""
        if len(raw_text.strip()) >= 30:
            if is_avn_encoded(raw_text):
                cleaned_text = clean_vietnamese_text(raw_text)
            else:
                # Standard Unicode: clean dangling diacritics without modifying valid vowels
                cleaned_text = re.sub(r'([a-zA-Z\u00C0-\u1EF9])[\u00B4\u0060\^~´`]', r'\1', raw_text)
        else:
            if not is_digital_pdf:
                tess_dir = get_tessdata_path(tessdata_path)
                if tess_dir:
                    try:
                        tp = page.get_textpage_ocr(language=ocr_lang, tessdata=tess_dir, dpi=150)
                        ocr_txt = tp.extractText()
                        if len(ocr_txt.strip()) >= 30:
                            cleaned_text = clean_vietnamese_text(ocr_txt) if is_avn_encoded(ocr_txt) else ocr_txt
                    except Exception:
                        pass

        lines = [l.strip() for l in cleaned_text.splitlines() if l.strip()]
        while lines and is_header_footer_or_watermark(lines[0], page_num):
            lines.pop(0)
        while lines and is_header_footer_or_watermark(lines[-1], page_num):
            lines.pop()

        pages_data.append({
            'page_num': page_num,
            'lines': lines,
            'images': p_imgs
        })

    # Group into chapters
    chapters = []
    current_chapter = {'title': 'Thông tin xuất bản', 'page_start': 2, 'items': []}

    for p_info in pages_data:
        p_num = p_info['page_num']
        p_lines = p_info['lines']
        p_imgs = p_info['images']

        if p_lines and is_chapter_heading(p_lines[0]):
            if current_chapter['items']:
                chapters.append(current_chapter)

            l0 = p_lines[0]
            l1 = p_lines[1] if len(p_lines) > 1 else ""
            l2 = p_lines[2] if len(p_lines) > 2 else ""

            heading_lines = [l0]
            consumed = 1
            if l1 and is_chapter_heading(l1) and len(f"{l0} {l1}") <= 90:
                heading_lines.append(l1)
                consumed = 2
                if l2 and is_chapter_heading(l2) and len(f"{l0} {l1} {l2}") <= 110:
                    heading_lines.append(l2)
                    consumed = 3

            heading_title = heading_lines[0]
            wrappers = {'THÔNG', 'CỦA', 'VÀ', 'CHO', 'KHỎI', 'TRONG', 'VÀO', 'VỚI', 'ĐƯỜNG', 'GIAI ĐOẠN', 'PHONG CÁCH', 'MÔ HÌNH', 'CUỘC CHIẾN', 'NHỮNG SAI', 'TẤN CÔNG', 'NGƯỜI KHÁC', 'MỘT CHÚT', 'NỀN VĂN', 'NHỮNG DÒNG', 'CÁC MỐC', 'THỜI GIAN'}
            for nxt in heading_lines[1:]:
                last_w = heading_title.split()[-1] if heading_title else ""
                if heading_title.endswith(('-', '—', ':', '–')) or nxt.startswith(('-', '—', ':', '–', '“', '"', '‘', "'")):
                    heading_title = f"{heading_title} {nxt}"
                elif last_w in wrappers or any(heading_title.endswith(w) for w in wrappers) or len(heading_title.split()) <= 2:
                    heading_title = f"{heading_title} {nxt}"
                else:
                    heading_title = f"{heading_title} - {nxt}"
            heading_title = re.sub(r'\s*-\s*-\s*', ' - ', heading_title)
            heading_title = re.sub(r'\s+', ' ', heading_title).strip()

            rem_lines = p_lines[consumed:]
            current_chapter = {
                'title': heading_title,
                'page_start': p_num,
                'items': []
            }
            for img_href in p_imgs:
                current_chapter['items'].append({'type': 'image', 'href': img_href})
            if rem_lines:
                paras = lines_to_paragraphs(rem_lines)
                for pr in paras:
                    current_chapter['items'].append({'type': 'paragraph', 'text': pr})
        else:
            for img_href in p_imgs:
                current_chapter['items'].append({'type': 'image', 'href': img_href})
            if p_lines:
                paras = lines_to_paragraphs(p_lines)
                for pr in paras:
                    current_chapter['items'].append({'type': 'paragraph', 'text': pr})

    if current_chapter['items']:
        chapters.append(current_chapter)

    chapters = [ch for ch in chapters if ch['items']]

    css_content = '''@charset "utf-8";
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Georgia", "Times New Roman", serif;
    font-size: 1.05em;
    line-height: 1.65;
    margin: 4% 5%;
    color: #1a1a1a;
    background-color: #fafafa;
}
.chapter {
    margin-bottom: 3em;
}
h1.chapter-title {
    font-size: 1.5em;
    font-weight: 700;
    line-height: 1.3;
    text-align: center;
    margin-top: 1.2em;
    margin-bottom: 1.5em;
    color: #111;
    border-bottom: 1px solid #e0e0e0;
    padding-bottom: 0.5em;
}
p {
    margin: 0 0 0.85em 0;
    text-indent: 1.25em;
    text-align: justify;
    text-justify: inter-word;
}
p.bullet {
    text-indent: 0;
    padding-left: 1.5em;
}
.figure {
    text-align: center;
    margin: 1.8em auto;
}
.chapter-img {
    max-width: 95%;
    height: auto;
    display: inline-block;
    border-radius: 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.12);
}
nav#toc ol {
    list-style-type: decimal;
    padding-left: 1.5em;
    line-height: 1.8;
}
nav#toc a {
    text-decoration: none;
    color: #0b57d0;
}
'''

    with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        
        container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
        zf.writestr('META-INF/container.xml', container_xml)
        zf.writestr('OEBPS/Styles/style.css', css_content)

        if cover_bytes:
            zf.writestr('OEBPS/Images/cover.jpg', cover_bytes)
            manifest_items.append('        <item id="cover_img" href="Images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>')
            cover_xhtml = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="vi">
<head>
    <title>Bìa sách</title>
    <style>body { margin: 0; padding: 0; text-align: center; background-color: #000; } img { max-width: 100%; height: auto; display: block; margin: 0 auto; }</style>
</head>
<body>
    <img src="../Images/cover.jpg" alt="Cover"/>
</body>
</html>'''
            zf.writestr('OEBPS/Text/cover.xhtml', cover_xhtml)
            manifest_items.append('        <item id="cover_page" href="Text/cover.xhtml" media-type="application/xhtml+xml"/>')
            spine_items.append('        <itemref idref="cover_page"/>')

        # Write all extracted interior illustrations into OEBPS/Images/
        for img_rel_path, im_bytes in all_images_to_write:
            zf.writestr(img_rel_path, im_bytes)

        # Write Chapters
        for chap_idx, chap in enumerate(chapters, 1):
            chap_filename = f'chapter_{chap_idx:03d}.xhtml'
            chap_title_esc = chap['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            body_html = [f'        <h1 class="chapter-title">{chap_title_esc}</h1>']
            for it in chap['items']:
                if it['type'] == 'image':
                    img_src = f"../{it['href']}"
                    body_html.append(f'        <div class="figure"><img src="{img_src}" alt="Minh họa" class="chapter-img"/></div>')
                elif it['type'] == 'paragraph':
                    safe_p = it['text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    if re.match(r'^[•·*–—-]\s+', it['text']):
                        body_html.append(f'        <p class="bullet">{safe_p}</p>')
                    else:
                        body_html.append(f'        <p>{safe_p}</p>')

            chap_xhtml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="vi">
<head>
    <title>{chap_title_esc}</title>
    <link rel="stylesheet" type="text/css" href="../Styles/style.css"/>
</head>
<body>
    <section class="chapter">
{chr(10).join(body_html)}
    </section>
</body>
</html>'''
            zf.writestr(f'OEBPS/Text/{chap_filename}', chap_xhtml)
            item_id = f'chap_{chap_idx:03d}'
            manifest_items.append(f'        <item id="{item_id}" href="Text/{chap_filename}" media-type="application/xhtml+xml"/>')
            spine_items.append(f'        <itemref idref="{item_id}"/>')

            toc_nav_points.append(f'''        <navPoint id="navPoint-{chap_idx}" playOrder="{chap_idx}">
            <navLabel><text>{chap_title_esc}</text></navLabel>
            <content src="Text/{chap_filename}"/>
        </navPoint>''')
            nav_ol_items.append(f'            <li><a href="{chap_filename}">{chap_title_esc}</a></li>')

        # nav.xhtml (EPUB 3)
        nav_xhtml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="vi">
<head>
    <title>Mục Lục</title>
    <link rel="stylesheet" type="text/css" href="../Styles/style.css"/>
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h1 class="chapter-title">Mục Lục</h1>
        <ol>
{chr(10).join(nav_ol_items)}
        </ol>
    </nav>
</body>
</html>'''
        zf.writestr('OEBPS/Text/nav.xhtml', nav_xhtml)
        manifest_items.append('        <item id="nav" href="Text/nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')

        content_opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package version="3.0" unique-identifier="BookId" xmlns="http://www.idpf.org/2007/opf">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="BookId">urn:uuid:{book_uuid}</dc:identifier>
        <dc:title>{title}</dc:title>
        <dc:creator>{author}</dc:creator>
        <dc:language>vi</dc:language>
        <meta name="cover" content="cover_img"/>
    </metadata>
    <manifest>
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
{chr(10).join(manifest_items)}
    </manifest>
    <spine toc="ncx">
{chr(10).join(spine_items)}
    </spine>
</package>'''
        zf.writestr('OEBPS/content.opf', content_opf)

        toc_ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="urn:uuid:{book_uuid}"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="{len(chapters)}"/>
        <meta name="dtb:maxPageNumber" content="{len(chapters)}"/>
    </head>
    <docTitle><text>{title}</text></docTitle>
    <navMap>
{chr(10).join(toc_nav_points)}
    </navMap>
</ncx>'''
        zf.writestr('OEBPS/toc.ncx', toc_ncx)

    return True, epub_path
