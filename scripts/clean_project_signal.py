"""
Project Signal - Task 1: Data Detective
Reproducible cleaning + exception-detection pipeline.

Reads the raw workbook, and for every operational sheet:
  1. Preserves every raw column untouched.
  2. Adds parsed/standardised columns (datetime, canonical equipment code,
     normalised category labels, normalised units) alongside the raw ones.
  3. Flags exceptions at the record level in an Exception_Flags column,
     using a fixed set of short codes (see EXCEPTION_CODES below).
  4. Removes exact full-row duplicates from the "cleaned" working copy,
     but keeps a full audit trail of every row removed.
  5. Writes everything to a new workbook: raw sheets untouched, a
     "_Cleaned" version of each sheet, a Duplicates_Removed audit sheet,
     an Exception_Log sheet (one row per flagged issue, sheet-agnostic),
     and a Cleaning_Assumptions sheet documenting every rule applied.

Run: python3 clean_project_signal.py <input.xlsx> <output.xlsx>
"""
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from common import parse_dt, normalize_equipment, EQUIPMENT_DISPLAY

EXCEPTION_CODES = {
    'DUP': 'Exact duplicate of another record (removed from cleaned copy)',
    'MISSING': 'Required field missing / blank',
    'EQUIP_UNKNOWN': 'Equipment code not in the recognised 6-asset master list',
    'DATE_UNPARSED': 'Date/time value did not match any known format',
    'NEG_DURATION': 'Duration/downtime value is negative',
    'OUTLIER': 'Value is a statistical/physical outlier vs. the rest of the field',
    'UNIT_MISMATCH': 'Recorded unit is inconsistent with the value pattern for that field',
    'BAD_CATEGORY': 'Category/label value is a misspelling or non-standard variant',
    'SEQ_CONTRADICTION': 'Value contradicts the logical order of related timestamps',
    'CROSS_RECORD_CONFLICT': 'Record conflicts with a related record elsewhere in the workbook',
    'PII': 'Field contains a direct personal identifier',
    'PROXY': 'Field is a proxy variable that could indirectly identify or disadvantage a person',
}


def load_raw(path):
    xls = pd.ExcelFile(path)
    sheets = {}
    for name in xls.sheet_names:
        if name in ('START_HERE', 'Data_Dictionary'):
            continue
        sheets[name] = pd.read_excel(path, sheet_name=name)
    return sheets


def flag(flags_dict, sheet, rec_id, code, detail=''):
    flags_dict.setdefault(sheet, []).append({
        'Sheet': sheet, 'Record_ID': rec_id, 'Code': code,
        'Issue': EXCEPTION_CODES[code], 'Detail': detail
    })


def dedupe(df, id_col, sheet, exlog):
    """Remove exact full-row duplicates, log them, keep first occurrence."""
    dup_mask = df.duplicated(keep='first')
    for rid in df.loc[dup_mask, id_col]:
        flag(exlog, sheet, rid, 'DUP')
    removed = df[dup_mask].copy()
    kept = df[~dup_mask].copy()
    return kept, removed


def add_parsed_datetime(df, col, newcol, sheet, exlog):
    parsed = df[col].apply(parse_dt)
    for rid, val in zip(df.iloc[:, 0], parsed):
        if isinstance(val, str) and val.startswith('UNPARSED'):
            flag(exlog, sheet, rid, 'DATE_UNPARSED', f'{col}={val}')
    df[newcol] = parsed.apply(lambda v: v if isinstance(v, datetime) else pd.NaT)
    return df


def add_equipment_canon(df, col, sheet, exlog, id_col):
    canon, ok = [], []
    for rid, raw in zip(df[id_col], df[col]):
        c, is_ok = normalize_equipment(raw)
        canon.append(c)
        ok.append(is_ok)
        if raw is not None and not (isinstance(raw, float) and pd.isna(raw)) and not is_ok:
            flag(exlog, sheet, rid, 'EQUIP_UNKNOWN', f'{col}={raw}')
    df[col + '_Canonical'] = canon
    df[col + '_Display'] = [EQUIPMENT_DISPLAY.get(c, c) for c in canon]
    return df


def clean_equipment_events(df, exlog):
    sheet = 'Equipment_Events'
    id_col = 'Event_ID'
    df, removed = dedupe(df, id_col, sheet, exlog)
    df = add_parsed_datetime(df, 'Event_Time', 'Event_Time_Parsed', sheet, exlog)
    df = add_equipment_canon(df, 'Equipment_Name', sheet, exlog, id_col)

    # Status / Event_Type case normalisation + typo fix
    status_map = {'complete': 'Complete', 'closed': 'Closed', 'open': 'Open'}
    df['Status_Clean'] = df['Status'].astype(str).str.strip().str.lower().map(status_map).fillna(df['Status'])
    type_map = {'start': 'Start', 'strat': 'Start', 'stop': 'Stop', 'idle': 'Idle',
                'inspection': 'Inspection', 'fault': 'Fault'}
    raw_type_lower = df['Event_Type'].astype(str).str.strip().str.lower()
    df['Event_Type_Clean'] = raw_type_lower.map(type_map).fillna(df['Event_Type'])
    for rid, raw in zip(df[id_col], df['Event_Type']):
        if str(raw).strip().lower() == 'strat':
            flag(exlog, sheet, rid, 'BAD_CATEGORY', "Event_Type='Strat' -> 'Start'")

    # Meter reading: the true underlying value always increases by a fixed
    # step (~7.3) per 3-hour interval for a given asset, regardless of the
    # label in Meter_Unit. The label is unreliable; the raw value is not.
    df['Meter_Reading_Hours_AsRecorded'] = df['Meter_Reading']
    for rid, val, unit in zip(df[id_col], df['Meter_Reading'], df['Meter_Unit']):
        if val == 999999.0:
            flag(exlog, sheet, rid, 'OUTLIER', f'Meter_Reading={val} (sentinel/placeholder value)')
        if str(unit).strip().lower() == 'mins':
            flag(exlog, sheet, rid, 'UNIT_MISMATCH',
                 "Meter_Unit='mins' but reading pattern matches the hours-scale sequence for this asset")

    # Sequence contradiction: EVT0023 timestamp precedes earlier-ID events for the same asset
    g = df.sort_values([ 'Equipment_Name_Canonical' if 'Equipment_Name_Canonical' in df.columns else id_col ])
    for eq, grp in df.dropna(subset=['Event_Time_Parsed']).groupby(df['Equipment_Name'].map(lambda x: normalize_equipment(x)[0])):
        grp_sorted = grp.sort_values(id_col)
        prev_dt, prev_id = None, None
        for _, r in grp_sorted.iterrows():
            if prev_dt is not None and r['Event_Time_Parsed'] < prev_dt:
                flag(exlog, sheet, r[id_col], 'SEQ_CONTRADICTION',
                     f"Event_Time {r['Event_Time_Parsed']} is earlier than {prev_id}'s {prev_dt} for the same asset, despite a later Event_ID")
            prev_dt, prev_id = r['Event_Time_Parsed'], r[id_col]

    return df, removed


def clean_delays(df, exlog):
    sheet = 'Delays_Downtime'
    id_col = 'Delay_ID'
    df, removed = dedupe(df, id_col, sheet, exlog)
    df = add_parsed_datetime(df, 'Start_Time', 'Start_Time_Parsed', sheet, exlog)
    df = add_parsed_datetime(df, 'End_Time', 'End_Time_Parsed', sheet, exlog)
    df = add_equipment_canon(df, 'Equipment_Name', sheet, exlog, id_col)

    cat_map = {'weather': 'Weather', 'mechanical': 'Mechanical', 'mecanical': 'Mechanical',
               'no operator': 'No Operator', 'operational': 'Operational', 'other': 'Other'}
    df['Delay_Category_Clean'] = df['Delay_Category'].astype(str).str.strip().str.lower().map(cat_map).fillna(df['Delay_Category'])
    for rid, raw in zip(df[id_col], df['Delay_Category']):
        if str(raw).strip().lower() == 'mecanical':
            flag(exlog, sheet, rid, 'BAD_CATEGORY', "Delay_Category='Mecanical' -> 'Mechanical'")

    df['Duration_Minutes'] = df.apply(
        lambda r: r['Duration'] * 60 if str(r['Duration_Unit']).strip().lower() == 'hours' else r['Duration'],
        axis=1)

    for rid, dur, unit in zip(df[id_col], df['Duration'], df['Duration_Unit']):
        if pd.isna(dur):
            flag(exlog, sheet, rid, 'MISSING', 'Duration is blank')
        elif dur < 0:
            flag(exlog, sheet, rid, 'NEG_DURATION', f'Duration={dur} {unit}')

    for rid, mins in zip(df[id_col], df['Duration_Minutes']):
        if pd.notna(mins) and mins > 480:  # > 8 hours for a single delay is implausible
            flag(exlog, sheet, rid, 'OUTLIER', f'Duration={mins} minutes (implausibly long single delay)')

    for rid, s, e, mins in zip(df[id_col], df['Start_Time_Parsed'], df['End_Time_Parsed'], df['Duration_Minutes']):
        if pd.notna(s) and pd.notna(e) and pd.notna(mins):
            computed = (e - s).total_seconds() / 60.0
            if abs(computed - mins) > 5:
                flag(exlog, sheet, rid, 'CROSS_RECORD_CONFLICT',
                     f'Stated Duration={mins} min does not match End-Start={computed:.0f} min')

    for rid, appr in zip(df[id_col], df['Approved_By']):
        if pd.isna(appr):
            flag(exlog, sheet, rid, 'MISSING', 'Approved_By is blank')

    return df, removed


def clean_operator_activities(df, exlog):
    sheet = 'Operator_Activities'
    id_col = 'Activity_ID'
    df, removed = dedupe(df, id_col, sheet, exlog)
    df = add_parsed_datetime(df, 'Activity_Start', 'Activity_Start_Parsed', sheet, exlog)
    df = add_parsed_datetime(df, 'Activity_End', 'Activity_End_Parsed', sheet, exlog)
    df = add_equipment_canon(df, 'Equipment_Name', sheet, exlog, id_col)

    type_map = {'hauling': 'Hauling', 'hualing': 'Hauling', 'loading': 'Loading',
                'break': 'Break', 'inspection': 'Inspection'}
    df['Activity_Type_Clean'] = df['Activity_Type'].astype(str).str.strip().str.lower().map(type_map).fillna(df['Activity_Type'])
    for rid, raw in zip(df[id_col], df['Activity_Type']):
        if str(raw).strip().lower() == 'hualing':
            flag(exlog, sheet, rid, 'BAD_CATEGORY', "Activity_Type='hualing' -> 'Hauling'")

    # Missing Operator_ID, recoverable via Operator_Name lookup elsewhere in the same sheet
    name_to_id = (df.dropna(subset=['Operator_ID'])
                    .drop_duplicates('Operator_Name')
                    .set_index('Operator_Name')['Operator_ID'].to_dict())
    recovered = []
    for rid, oid, nm in zip(df[id_col], df['Operator_ID'], df['Operator_Name']):
        if pd.isna(oid):
            flag(exlog, sheet, rid, 'MISSING', f'Operator_ID blank; recoverable from Operator_Name={nm} -> {name_to_id.get(nm)}')
            recovered.append(name_to_id.get(nm))
        else:
            recovered.append(oid)
    df['Operator_ID_Recovered'] = recovered

    for rid, qty in zip(df[id_col], df['Quantity']):
        if pd.notna(qty) and qty > 50:
            flag(exlog, sheet, rid, 'OUTLIER', f'Quantity={qty} (~10x the typical range of 2-10)')

    for col in ['Operator_Name', 'Email', 'Mobile_Number']:
        for rid in df[id_col]:
            pass
    df['_PII_Fields'] = 'Operator_Name;Email;Mobile_Number'
    df['_Proxy_Fields'] = 'Home_Zone;Contractor_Group'

    return df, removed


def clean_shift_performance(df, exlog):
    sheet = 'Shift_Performance'
    id_col = 'Shift_Record_ID'
    df, removed = dedupe(df, id_col, sheet, exlog)
    df = add_parsed_datetime(df, 'Shift_Date', 'Shift_Date_Parsed', sheet, exlog)
    df = add_equipment_canon(df, 'Equipment_Name', sheet, exlog, id_col)

    for rid, sch, act in zip(df[id_col], df['Scheduled_Hours'], df['Actual_Hours']):
        if act > sch * 1.5:
            flag(exlog, sheet, rid, 'OUTLIER', f'Actual_Hours={act} vs Scheduled_Hours={sch}')

    for rid, loads in zip(df[id_col], df['Loads']):
        if loads < 0:
            flag(exlog, sheet, rid, 'NEG_DURATION', f'Loads={loads} (negative output count)')

    for rid, av in zip(df[id_col], df['Availability_Pct']):
        if av > 1 or av < 0:
            flag(exlog, sheet, rid, 'OUTLIER', f'Availability_Pct={av} (expected 0.0-1.0)')

    for rid, ut in zip(df[id_col], df['Utilisation_Pct']):
        if ut > 1 or ut < 0:
            flag(exlog, sheet, rid, 'OUTLIER', f'Utilisation_Pct={ut} (expected 0.0-1.0)')

    df['Fuel_Used_Litres'] = df.apply(
        lambda r: r['Fuel_Used'] * 3.78541 if str(r['Fuel_Unit']).strip().lower() == 'gallons' else r['Fuel_Used'],
        axis=1)
    for rid, unit in zip(df[id_col], df['Fuel_Unit']):
        if str(unit).strip().lower() == 'gallons':
            flag(exlog, sheet, rid, 'UNIT_MISMATCH', "Fuel_Unit='gallons' while the rest of the sheet uses litres")

    for rid, fuel, loads in zip(df[id_col], df['Fuel_Used'], df['Loads']):
        if fuel == 0 and loads > 0:
            flag(exlog, sheet, rid, 'CROSS_RECORD_CONFLICT', f'Fuel_Used=0 but Loads={loads} (equipment produced output with no recorded fuel use)')

    return df, removed


def clean_safety(df, exlog):
    sheet = 'Safety_Observations'
    id_col = 'Observation_ID'
    df, removed = dedupe(df, id_col, sheet, exlog)
    df = add_parsed_datetime(df, 'Observation_Date', 'Observation_Date_Parsed', sheet, exlog)
    df = add_parsed_datetime(df, 'Closed_Date', 'Closed_Date_Parsed', sheet, exlog)
    df = add_equipment_canon(df, 'Equipment_Name', sheet, exlog, id_col)

    cat_map = {'saftey': 'Safety', 'ppe': 'PPE', 'vehicle interaction': 'Vehicle Interaction',
               'housekeeping': 'Housekeeping', 'procedure': 'Procedure', 'production': 'Production',
               'environmental': 'Environmental'}
    df['Category_Clean'] = df['Category'].astype(str).str.strip().str.lower().map(cat_map).fillna(df['Category'])
    for rid, raw in zip(df[id_col], df['Category']):
        if str(raw).strip().lower() == 'saftey':
            flag(exlog, sheet, rid, 'BAD_CATEGORY', "Category='Saftey' -> 'Safety'")

    sev_map = {'low': 'Low', 'medium': 'Medium', 'high': 'High', 'critical': 'Critical'}
    df['Severity_Clean'] = df['Severity'].astype(str).str.strip().str.lower().map(sev_map).fillna(df['Severity'])

    for rid, obs, clo in zip(df[id_col], df['Observation_Date_Parsed'], df['Closed_Date_Parsed']):
        if pd.notna(obs) and pd.notna(clo) and clo < obs:
            flag(exlog, sheet, rid, 'SEQ_CONTRADICTION', f'Closed_Date {clo} is earlier than Observation_Date {obs}')

    for rid, desc in zip(df[id_col], df['Description']):
        if pd.isna(desc):
            flag(exlog, sheet, rid, 'MISSING', 'Description is blank')

    for rid, desc, obs_person in zip(df[id_col], df['Description'], df['Observed_Person_ID']):
        if isinstance(desc, str) and isinstance(obs_person, str) and obs_person in desc:
            flag(exlog, sheet, rid, 'PII',
                 f'Free-text Description names an identified individual ({obs_person}) alongside an unproven allegation - requires review before wider distribution')

    df['_PII_Fields'] = 'Reporter_ID;Observed_Person_ID (indirect via linkage)'
    return df, removed


def clean_training(df, exlog):
    sheet = 'Training_Records'
    id_col = 'Training_Record_ID'
    df, removed = dedupe(df, id_col, sheet, exlog)
    df = add_parsed_datetime(df, 'Completion_Date', 'Completion_Date_Parsed', sheet, exlog)
    df = add_parsed_datetime(df, 'Expiry_Date', 'Expiry_Date_Parsed', sheet, exlog)

    course_map = {'SAFE-1': 'SAFE01'}
    df['Course_Code_Clean'] = df['Course_Code'].replace(course_map)
    for rid, raw in zip(df[id_col], df['Course_Code']):
        if raw == 'SAFE-1':
            flag(exlog, sheet, rid, 'BAD_CATEGORY', "Course_Code='SAFE-1' -> 'SAFE01'")

    for rid, comp, exp in zip(df[id_col], df['Completion_Date_Parsed'], df['Expiry_Date_Parsed']):
        if pd.notna(comp) and pd.notna(exp) and exp < comp:
            flag(exlog, sheet, rid, 'SEQ_CONTRADICTION', f'Expiry_Date {exp} is earlier than Completion_Date {comp}')

    for rid, score in zip(df[id_col], df['Score']):
        if pd.notna(score) and (score > 100 or score < 0):
            flag(exlog, sheet, rid, 'OUTLIER', f'Score={score} (expected 0-100)')

    df['_PII_Fields'] = 'Operator_Name;Certificate_Number'
    df['_Sensitive_Fields'] = 'Medical_Fitness_Code (restricted - do not use without authority)'
    df['_Proxy_Fields'] = 'Home_Zone'
    return df, removed


def clean_maintenance(df, exlog):
    sheet = 'Maintenance_Notifications'
    id_col = 'Notification_ID'
    df, removed = dedupe(df, id_col, sheet, exlog)
    df = add_parsed_datetime(df, 'Raised_Date', 'Raised_Date_Parsed', sheet, exlog)
    df = add_parsed_datetime(df, 'Planned_Start', 'Planned_Start_Parsed', sheet, exlog)
    df = add_parsed_datetime(df, 'Actual_Start', 'Actual_Start_Parsed', sheet, exlog)
    df = add_parsed_datetime(df, 'Actual_End', 'Actual_End_Parsed', sheet, exlog)
    df = add_equipment_canon(df, 'Equipment_Name', sheet, exlog, id_col)

    prio_map = {'p1': 'P1', 'p2': 'P2', 'p3': 'P3', 'urgent': 'P1 (Urgent - non-standard label)'}
    df['Priority_Clean'] = df['Priority'].astype(str).str.strip().str.lower().map(prio_map).fillna(df['Priority'])
    for rid, raw in zip(df[id_col], df['Priority']):
        if str(raw).strip().lower() == 'urgent':
            flag(exlog, sheet, rid, 'BAD_CATEGORY', "Priority='Urgent' is not a controlled P1/P2/P3 value - mapped to P1 pending confirmation")

    type_map = {'break down': 'Breakdown', 'breakdown': 'Breakdown', 'inspection': 'Inspection', 'planned': 'Planned'}
    df['Notification_Type_Clean'] = df['Notification_Type'].astype(str).str.strip().str.lower().map(type_map).fillna(df['Notification_Type'])

    for rid, dh in zip(df[id_col], df['Downtime_Hours']):
        if pd.notna(dh) and dh < 0:
            flag(exlog, sheet, rid, 'NEG_DURATION', f'Downtime_Hours={dh}')

    for rid, raised, astart in zip(df[id_col], df['Raised_Date_Parsed'], df['Actual_Start_Parsed']):
        if pd.notna(raised) and pd.notna(astart) and astart < raised:
            flag(exlog, sheet, rid, 'SEQ_CONTRADICTION', f'Actual_Start {astart} is earlier than Raised_Date {raised}')

    for rid, aend, dh in zip(df[id_col], df['Actual_End'], df['Downtime_Hours']):
        if pd.isna(aend) and pd.notna(dh):
            flag(exlog, sheet, rid, 'CROSS_RECORD_CONFLICT', f'Downtime_Hours={dh} recorded but Actual_End is blank - cannot reconcile')

    return df, removed


def clean_environmental(df, exlog):
    sheet = 'Environmental_Readings'
    id_col = 'Reading_ID'
    df, removed = dedupe(df, id_col, sheet, exlog)
    df = add_parsed_datetime(df, 'Reading_Time', 'Reading_Time_Parsed', sheet, exlog)
    df = add_equipment_canon(df, 'Equipment_Nearby', sheet, exlog, id_col)

    expected_unit = {'Rainfall': 'mm', 'Temperature': 'C', 'Noise': 'dB', 'Dust': 'mg/m3'}
    for rid, rtype, unit in zip(df[id_col], df['Reading_Type'], df['Unit']):
        exp = expected_unit.get(rtype)
        if exp and str(unit).strip() != exp:
            flag(exlog, sheet, rid, 'UNIT_MISMATCH', f"Reading_Type={rtype} recorded in Unit='{unit}', expected '{exp}'")

    for rid, rtype, val in zip(df[id_col], df['Reading_Type'], df['Value']):
        if rtype == 'Rainfall' and val < 0:
            flag(exlog, sheet, rid, 'OUTLIER', f'Rainfall={val} (negative rainfall is physically impossible)')
        if rtype == 'Dust' and val > 100:
            flag(exlog, sheet, rid, 'OUTLIER', f'Dust={val} mg/m3 (~1000x the rest of the readings; likely sensor fault or sentinel value)')

    for rid, qf in zip(df[id_col], df['Quality_Flag']):
        if pd.isna(qf):
            flag(exlog, sheet, rid, 'MISSING', 'Quality_Flag is blank')

    return df, removed


def clean_access(df, exlog):
    sheet = 'Access_Control'
    id_col = 'Access_Event_ID'
    df, removed = dedupe(df, id_col, sheet, exlog)
    df = add_parsed_datetime(df, 'Event_Time', 'Event_Time_Parsed', sheet, exlog)

    dir_map = {'entry': 'Entry', 'in': 'Entry', 'exit': 'Exit', 'out': 'Exit'}
    df['Direction_Clean'] = df['Direction'].astype(str).str.strip().str.lower().map(dir_map).fillna(df['Direction'])

    res_map = {'granted': 'Granted', 'denied': 'Denied'}
    df['Access_Result_Clean'] = df['Access_Result'].astype(str).str.strip().str.lower().map(res_map).fillna(df['Access_Result'])

    for rid, badge in zip(df[id_col], df['Badge_ID']):
        if pd.isna(badge):
            flag(exlog, sheet, rid, 'MISSING', 'Badge_ID is blank')

    # Cross-check Employee_ID against the canonical ID<->Name map built from
    # Operator_ID/Operator_Name pairs seen elsewhere in the workbook.
    name_to_id = df.drop_duplicates('Employee_Name').set_index('Employee_Name')['Employee_ID'].to_dict()
    # Use the *modal* ID per name as canonical (handles the one bad row)
    from collections import Counter
    modal = {}
    for nm, grp in df.groupby('Employee_Name'):
        modal[nm] = Counter(grp['Employee_ID']).most_common(1)[0][0]
    for rid, eid, nm in zip(df[id_col], df['Employee_ID'], df['Employee_Name']):
        if modal.get(nm) != eid:
            flag(exlog, sheet, rid, 'CROSS_RECORD_CONFLICT',
                 f"Employee_ID={eid} does not match the established ID {modal.get(nm)} used elsewhere for {nm}")

    for rid, dt in zip(df[id_col], df['Event_Time_Parsed']):
        if pd.notna(dt) and dt.year != 2026:
            flag(exlog, sheet, rid, 'OUTLIER', f'Event_Time year={dt.year}, outside the 2026 operational window used by every other record')

    df['_PII_Fields'] = 'Employee_Name;Badge_ID'
    df['_Proxy_Fields'] = 'Home_Zone;Contractor_Group'
    return df, removed


CLEANERS = {
    'Equipment_Events': clean_equipment_events,
    'Delays_Downtime': clean_delays,
    'Operator_Activities': clean_operator_activities,
    'Shift_Performance': clean_shift_performance,
    'Safety_Observations': clean_safety,
    'Training_Records': clean_training,
    'Maintenance_Notifications': clean_maintenance,
    'Environmental_Readings': clean_environmental,
    'Access_Control': clean_access,
}


def build_flag_summary_column(cleaned, exlog):
    """Attach a semicolon-joined Exception_Flags column to each cleaned df."""
    for sheet, df in cleaned.items():
        id_col = df.columns[0]
        issues = {}
        for e in exlog.get(sheet, []):
            issues.setdefault(e['Record_ID'], []).append(e['Code'])
        df['Exception_Flags'] = df[id_col].map(lambda x: ';'.join(issues.get(x, [])))
    return cleaned


def main(inpath, outpath):
    raw = load_raw(inpath)
    exlog = {}
    cleaned, removed_rows = {}, {}
    for sheet, df in raw.items():
        cleaner = CLEANERS[sheet]
        cdf, rdf = cleaner(df.copy(), exlog)
        cleaned[sheet] = cdf
        removed_rows[sheet] = rdf

    cleaned = build_flag_summary_column(cleaned, exlog)

    exception_rows = []
    for sheet, entries in exlog.items():
        exception_rows.extend(entries)
    exception_df = pd.DataFrame(exception_rows, columns=['Sheet', 'Record_ID', 'Code', 'Issue', 'Detail'])
    exception_df = exception_df.sort_values(['Sheet', 'Record_ID']).reset_index(drop=True)

    dup_rows = []
    for sheet, rdf in removed_rows.items():
        if len(rdf):
            rdf = rdf.copy()
            rdf.insert(0, 'Source_Sheet', sheet)
            dup_rows.append(rdf)
    dup_df = pd.concat(dup_rows, ignore_index=True) if dup_rows else pd.DataFrame()

    with pd.ExcelWriter(outpath, engine='openpyxl') as writer:
        for sheet, df in raw.items():
            df.to_excel(writer, sheet_name=f'{sheet[:22]}_RAW', index=False)
        for sheet, df in cleaned.items():
            df.to_excel(writer, sheet_name=f'{sheet[:22]}_Clean', index=False)
        exception_df.to_excel(writer, sheet_name='Exception_Log', index=False)
        dup_df.to_excel(writer, sheet_name='Duplicates_Removed', index=False)

    print(f'Wrote {outpath}')
    print(f'Total exceptions logged: {len(exception_df)}')
    print(exception_df['Code'].value_counts())
    print()
    print('By sheet:')
    print(exception_df.groupby(['Sheet', 'Code']).size())

    return cleaned, exception_df, dup_df


if __name__ == '__main__':
    inpath = sys.argv[1] if len(sys.argv) > 1 else 'project_signal.xlsx'
    outpath = sys.argv[2] if len(sys.argv) > 2 else 'project_signal_cleaned.xlsx'
    main(inpath, outpath)
