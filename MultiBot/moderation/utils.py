import re
from datetime import timedelta
from typing import Optional

TIME_UNITS = {
    "s": "seconds", "ثانية": "seconds", "ثواني": "seconds", "ثانيه": "seconds",
    "m": "minutes", "دقيقة": "minutes", "دقايق": "minutes", "د": "minutes",
    "h": "hours", "ساعة": "hours", "ساعه": "hours", "ساعات": "hours", "س": "hours",
    "d": "days", "يوم": "days", "ايام": "days", "یوم": "days",
    "w": "weeks", "اسبوع": "weeks", "اسابيع": "weeks", "أسبوع": "weeks",
    "mo": "months", "شهر": "months", "شهور": "months",
    "y": "years", "سنة": "years", "سنه": "years", "سنين": "years", "عام": "years",
}

ARABIC_NUMS = {
    "واحد": 1, "اثنان": 2, "اثنين": 2, "ثلاثة": 3, "ثلاث": 3,
    "اربعة": 4, "أربعة": 4, "خمسة": 5, "خمس": 5,
    "ستة": 6, "سبعة": 7, "ثمانية": 8, "ثماني": 8,
    "تسعة": 9, "عشرة": 10,
    "١": 1, "٢": 2, "٣": 3, "٤": 4, "٥": 5, "٦": 6, "٧": 7, "٨": 8, "٩": 9, "٠": 0,
}

DUAL_MAP = {
    "ثانية": 2, "ساعة": 2, "ساعتين": 2, "دقيقة": 2, "دقيقتين": 2,
    "يوم": 2, "يومين": 2, "شهر": 2, "شهرين": 2, "سنة": 2, "سنتين": 2,
    "اسبوع": 2, "اسبوعين": 2,
}

def parse_duration(text: str) -> Optional[timedelta]:
    if not text:
        return None
    text = text.strip()
    total = timedelta()

    patterns = [
        (r"(\d+)\s*(s|ثانية|ثواني|ثانيه)\b", "seconds"),
        (r"(\d+)\s*(m|دقيقة|دقايق|د)\b", "minutes"),
        (r"(\d+)\s*(h|ساعة|ساعه|ساعات|س)\b", "hours"),
        (r"(\d+)\s*(d|يوم|ايام|یوم)\b", "days"),
        (r"(\d+)\s*(w|اسبوع|اسابيع|أسبوع)\b", "weeks"),
        (r"(\d+)\s*(mo|شهر|شهور)\b", "months"),
        (r"(\d+)\s*(y|سنة|سنه|سنين|عام)\b", "years"),
        (r"(\d+)\s*(ثواني|ثوان)\b", "seconds"),
    ]

    DAYS_PER = {"years": 365, "months": 30, "weeks": 7, "days": 1}
    TD_KWARGS = {"seconds", "minutes", "hours", "days", "weeks"}

    for pattern, unit in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if unit in TD_KWARGS:
                total += timedelta(**{unit: val})
            elif unit in DAYS_PER:
                total += timedelta(days=val * DAYS_PER[unit])
            text = text.replace(m.group(0), "").strip()

    if total.total_seconds() > 0:
        return total

    if text in DUAL_MAP:
        return timedelta(days=DUAL_MAP[text] * 30)

    words = text.split()
    i = 0
    while i < len(words):
        word = words[i]
        num = None

        if word.isdigit():
            num = int(word)
            i += 1
        elif word in ARABIC_NUMS:
            num = ARABIC_NUMS[word]
            i += 1
        elif i + 1 < len(words) and words[i] + words[i+1] in ARABIC_NUMS:
            num = ARABIC_NUMS[words[i] + words[i+1]]
            i += 2
        else:
            i += 1
            continue

        if i < len(words):
            unit_word = words[i]
            if unit_word in DUAL_MAP:
                num *= DUAL_MAP[unit_word]
                i += 1
            elif unit_word in TIME_UNITS:
                u = TIME_UNITS[unit_word]
                if u in TD_KWARGS:
                    total += timedelta(**{u: num})
                elif u in DAYS_PER:
                    total += timedelta(days=num * DAYS_PER[u])
                i += 1

    return total if total.total_seconds() > 0 else None

def format_duration(td: timedelta) -> str:
    total = int(td.total_seconds())
    parts = []
    for unit, label in [(86400 * 365, "y"), (86400 * 30, "mo"), (86400, "d"), (3600, "h"), (60, "m")]:
        if total >= unit:
            v = total // unit
            parts.append(f"{v}{label}")
            total %= unit
    if total > 0 or not parts:
        parts.append(f"{total}s")
    return " ".join(parts)
