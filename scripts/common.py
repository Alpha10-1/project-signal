import pandas as pd
import re
from datetime import datetime

def parse_dt(s):
    """Parse one of four known messy formats into a real datetime.
    Returns None for blank/NaN, or a string 'UNPARSED:<raw>' if no pattern matches."""
    if pd.isna(s):
        return None
    s = str(s).strip()
    if s == '':
        return None
    # Pattern D: YYYY-MM-DD HH:MM:SS (ISO)
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$', s)
    if m:
        y, mo, d, h, mi, se = map(int, m.groups())
        try:
            return datetime(y, mo, d, h, mi, se)
        except ValueError:
            return 'UNPARSED:' + s
    # Pattern C: YYYY/MM/DD HH:MM
    m = re.match(r'^(\d{4})/(\d{2})/(\d{2}) (\d{2}):(\d{2})$', s)
    if m:
        y, mo, d, h, mi = map(int, m.groups())
        try:
            return datetime(y, mo, d, h, mi)
        except ValueError:
            return 'UNPARSED:' + s
    # Pattern B: MM/DD/YYYY hh:mm AM/PM
    m = re.match(r'^(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}) (AM|PM)$', s)
    if m:
        mo, d, y, h, mi, ap = m.groups()
        mo, d, y, h, mi = int(mo), int(d), int(y), int(h), int(mi)
        if ap == 'PM' and h != 12:
            h += 12
        if ap == 'AM' and h == 12:
            h = 0
        try:
            return datetime(y, mo, d, h, mi)
        except ValueError:
            return 'UNPARSED:' + s
    # Pattern A: DD/MM/YYYY HH:MM (24hr, no AM/PM)
    m = re.match(r'^(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2})$', s)
    if m:
        d, mo, y, h, mi = map(int, m.groups())
        try:
            return datetime(y, mo, d, h, mi)
        except ValueError:
            return 'UNPARSED:' + s
    # Date-only patterns (used in Training_Records / Shift_Performance)
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', s)  # YYYY-MM-DD
    if m:
        y, mo, d = map(int, m.groups())
        try:
            return datetime(y, mo, d)
        except ValueError:
            return 'UNPARSED:' + s
    m = re.match(r'^(\d{4})/(\d{2})/(\d{2})$', s)  # YYYY/MM/DD
    if m:
        y, mo, d = map(int, m.groups())
        try:
            return datetime(y, mo, d)
        except ValueError:
            return 'UNPARSED:' + s
    m = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', s)  # ambiguous DD/MM/YYYY or MM/DD/YYYY
    if m:
        a, b, y = map(int, m.groups())
        # Disambiguate using >12 rule; if both <=12, assume DD/MM/YYYY (matches
        # the convention used elsewhere in this workbook's date-only fields).
        y = int(y)
        if a > 12 and b <= 12:
            mo, d = b, a  # a is day
            try:
                return datetime(y, mo, d)
            except ValueError:
                return 'UNPARSED:' + s
        elif b > 12 and a <= 12:
            mo, d = a, b
            try:
                return datetime(y, mo, d)
            except ValueError:
                return 'UNPARSED:' + s
        else:
            # ambiguous both <=12: default DD/MM/YYYY, flag separately by caller
            try:
                return datetime(y, b, a)
            except ValueError:
                return 'UNPARSED:' + s
    return 'UNPARSED:' + s


# Canonical equipment master list, derived from the fixed 6-asset rotation
# observed across every operational sheet (3 trucks, 2 excavators, 1 drill).
EQUIPMENT_CANON = {
    'TRK001': 'TRK001', 'TRK-001': 'TRK001', 'TRK 001': 'TRK001',
    'TRUCK01': 'TRK001', 'TRUCK1': 'TRK001', 'TRUCK 1': 'TRK001', 'TRUCK ONE': 'TRK001',
    'TRK002': 'TRK002', 'TRK-002': 'TRK002', 'TRK 002': 'TRK002',
    'TRUCK02': 'TRK002', 'TRUCK2': 'TRK002', 'TRUCK 2': 'TRK002',
    'TRK003': 'TRK003', 'TRK-003': 'TRK003', 'TRK 003': 'TRK003',
    'TRUCK03': 'TRK003', 'TRUCK3': 'TRK003', 'TRUCK 3': 'TRK003',
    'EXC001': 'EXC001', 'EXC-01': 'EXC001', 'EXC 001': 'EXC001', 'EX 001': 'EXC001',
    'EXCAVATOR1': 'EXC001', 'EXCAVATOR 1': 'EXC001',
    'EXC002': 'EXC002', 'EXC-02': 'EXC002', 'EXC 002': 'EXC002', 'EX 002': 'EXC002',
    'EXCAVATOR2': 'EXC002', 'EXCAVATOR 2': 'EXC002',
    'DRL001': 'DRL001', 'DRILL-1': 'DRL001', 'DRILL 1': 'DRL001', 'DRILL01': 'DRL001',
    'DRILL 01': 'DRL001',
}

EQUIPMENT_DISPLAY = {
    'TRK001': 'Truck 1', 'TRK002': 'Truck 2', 'TRK003': 'Truck 3',
    'EXC001': 'Excavator 1', 'EXC002': 'Excavator 2', 'DRL001': 'Drill 1',
}


def normalize_equipment(raw):
    """Map a messy equipment name to its canonical asset code.
    Returns (canonical_code_or_None, is_recognized_bool)."""
    if pd.isna(raw):
        return None, False
    key = str(raw).strip().upper()
    if key in EQUIPMENT_CANON:
        return EQUIPMENT_CANON[key], True
    return str(raw).strip(), False  # unrecognized / out-of-master-list code
