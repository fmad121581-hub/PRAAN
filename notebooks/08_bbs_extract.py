import pdfplumber
import pandas as pd
import re
import os

# Paths resolve from this file's own location, so the scripts run unchanged
# on any machine. _R is the project root; _R2 its parent.
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/') + '/'
_R2 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).replace('\\', '/') + '/'

URBAN_PDF  = _R2 + "Urban Area Report.pdf"
OUTPUT_DIR = _R + "data/processed/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

all_data = []
current_corp = None

with pdfplumber.open(URBAN_PDF) as pdf:
    for i in range(258, 268):
        page = pdf.pages[i]
        words = page.extract_words()
        lines = {}
        for w in words:
            y = round(w['top'], 0)
            if y not in lines:
                lines[y] = []
            lines[y].append(w['text'])

        for y in sorted(lines.keys()):
            line = ' '.join(lines[y])

            # Detect corporation — handles split lines
            if 'Dhaka South' in line:
                current_corp = 'DSCC'
                continue
            elif 'Dhaka North' in line:
                current_corp = 'DNCC'
                continue
            elif current_corp in ['DNCC', 'DSCC'] and any(x in line for x in [
                'Chattogram', 'Khulna', 'Rajshahi',
                'Sylhet', 'Barishal', 'Narayanganj',
                'Gazipur', 'Mymensingh', 'Cumilla'
            ]):
                current_corp = None
                continue

            if current_corp is None:
                continue

            m = re.match(
                r'Ward No\.\s*(\d+)(?:\s*\(\d+\))?\s+(\d.*)',
                line.strip()
            )
            if m:
                nums = m.group(2).split()
                if len(nums) >= 11:
                    try:
                        all_data.append({
                            'city_corp':  current_corp,
                            'ward_no':    int(m.group(1)),
                            'hh_total':   float(nums[0]),
                            'hh_general': float(nums[1]),
                            'pop_total':  float(nums[4]),
                            'hh_size':    float(nums[10]),
                        })
                    except (IndexError, ValueError):
                        pass

df = pd.DataFrame(all_data)
print(f"Total rows: {len(df)}")
if len(df) > 0:
    print(df.groupby('city_corp')['ward_no'].count())
    print(df.head(10).to_string())
    df.to_csv(OUTPUT_DIR + 'bbs_2022_ward_final.csv', index=False)
    print("\nSaved → bbs_2022_ward_final.csv")
    # ── Merge electricity coverage ────────────────────────────────
elec_data = []
current_corp = None

with pdfplumber.open(URBAN_PDF) as pdf:
    for i in range(404, 415):
        page = pdf.pages[i]
        words = page.extract_words()
        lines = {}
        for w in words:
            y = round(w['top'], 0)
            if y not in lines:
                lines[y] = []
            lines[y].append(w['text'])

        for y in sorted(lines.keys()):
            line = ' '.join(lines[y])

            if 'Dhaka South' in line:
                current_corp = 'DSCC'
                continue
            elif 'Dhaka North' in line:
                current_corp = 'DNCC'
                continue
            elif current_corp in ['DNCC', 'DSCC'] and any(x in line for x in [
                'Chattogram', 'Khulna', 'Rajshahi',
                'Sylhet', 'Barishal', 'Narayanganj',
                'Gazipur', 'Mymensingh', 'Cumilla'
            ]):
                current_corp = None
                continue

            if current_corp is None:
                continue

            m = re.match(
                r'Ward No\.\s*(\d+)(?:\s*\(\d+\))?\s+(\d.*)',
                line.strip()
            )
            if m:
                nums = m.group(2).split()
                try:
                    elec_data.append({
                        'city_corp':     current_corp,
                        'ward_no':       int(m.group(1)),
                        'elec_coverage': float(nums[-1]),
                    })
                except (IndexError, ValueError):
                    pass

df_elec = pd.DataFrame(elec_data)
print(f"\nElectricity: {len(df_elec)} wards")
print(df_elec.groupby('city_corp')['ward_no'].count())

# Merge and save final
df_final = df.merge(df_elec, on=['city_corp','ward_no'], how='left')
df_final['NAME_4'] = 'Ward No-' + df_final['ward_no'].astype(str).str.zfill(2)

print(f"\nFinal merged: {len(df_final)} wards")
print(df_final[['city_corp','ward_no','NAME_4',
                 'hh_total','pop_total','hh_size',
                 'elec_coverage']].head(10).to_string())

df_final.to_csv(OUTPUT_DIR + 'bbs_2022_ward_final.csv', index=False)
print("\nSaved → bbs_2022_ward_final.csv")
print("✓ BBS extraction complete.")
with open(_R + "notebooks/08_bbs_extract.py") as f:
    for i, line in enumerate(f, 1):
        if 50 <= i <= 100:
            print(f"{i:3}: {line}", end='')