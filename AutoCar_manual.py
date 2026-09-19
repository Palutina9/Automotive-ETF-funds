# -*- coding: utf-8 -*-
"""
Created on Wed Sep  9 09:24:08 2026

@author: p.mahmoudi
"""

import requests
import json
import jdatetime

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
DIGIT_MAP = {d: str(i) for i, d in enumerate(PERSIAN_DIGITS)}
DIGIT_MAP.update({d: str(i) for i, d in enumerate(ARABIC_DIGITS)})

def fa_to_float(s):
    s = s.strip()
    s = s.replace("%", "").strip()  # remove % first
    negative = s.startswith("(") and s.endswith(")")
    if negative:
        s = s[1:-1]
    s = s.replace("%", "").strip()
    s = "".join(DIGIT_MAP.get(ch, ch) for ch in s)
    s = s.replace("٫", ".")
    s = s.replace(",", "")
    return -float(s) if negative else float(s)

def safe_get(url, **kwargs):
    try:
        resp = requests.get(url, timeout=10, **kwargs)
        resp.raise_for_status()
        print(f"OK: {url}")
        return resp
    except requests.exceptions.RequestException as e:
        print(f"FAILED: {url} -> {e}")
        return None


def akharin_tarikh(n=7):
    emrooz = jdatetime.date.today()
    return [(emrooz - jdatetime.timedelta(days=i)).strftime("%Y/%m/%d") for i in range(n)]


def build_params(tarikh, today_str):
    if tarikh == today_str:
        return {}
    return {"toDate": tarikh}

def apietelaat(name, api_periodic, api_daily, navapi, params):
    response = safe_get(api_periodic, headers= headers, params= params)
    if response is None:
        print(f"Skipping {name} periodic — unreachable")
        return
    data = response.json()
    rows = data['rows'][:8]
    for row in rows:
        jadval.append({
            name + "_fundSimpleReturn": row['fundSimpleReturn']
            })

    roozaneh = safe_get(api_daily, params=params)
    if roozaneh is not None:
        data_daily = roozaneh.json()[0]
        jadval.append({
            name + "_fundDailyReturn": data_daily['fundDailyReturn'],
            })
    else:
        print(f"Skipping {name} daily — unreachable")
    
    navnum = safe_get(navapi, params=params)
    if navnum is not None:
        jadval.append({
            name + "_fundNAV": fa_to_float(navnum.json()['nav']),
            })
    else:
        print(f"Skipping {name} NAV — unreachable")

dates = akharin_tarikh(7)
print(dates)
today_str = akharin_tarikh(1)[0]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
}


api_periodic = "https://agahsectorfund.ir/api/v1/public/fundReturnPeriodic/2"
api_daily = "https://agahsectorfund.ir/api/v1/public/fundReturnDaily/2"
index_api = "https://fipiran.ir/services/chart/indexefficiencychart?insCodes=20213770409093165&showAll=true"


all_data = {}
index = safe_get(index_api)
radif = index.json()[0]['items'][:7]
print(radif)


for i, tarikh in enumerate(dates):
    jadval = []
    params = build_params(tarikh, today_str)
    # fixed section
    response = safe_get(api_periodic, params=params)
    if response is not None:
        data = response.json()
        rows = data['rows'][:8]
        roozaneh = safe_get(api_daily, params=params)
        if roozaneh is not None:
            data_daily = roozaneh.json()[i]
            for row in rows:
                jadval.append({
                    "key": row['key'],
                    "fromDate": row['fromDate'],
                    "toDate": row['toDate'],
                    "marketSimpleReturn": row['marketSimpleReturn']
                    })
            jadval.append({
                "marketDailyReturn": data_daily['marketDailyReturn']
                })
            jadval.append({
                "dailyReturnDate": data_daily['date']})
        else:
            print("Skipping market daily return — site unreachable")
    else:
        print("Skipping market data entirely — site unreachable")
    
    #AutoMotive inedx
    if i <len(radif):
        shakhes = radif[i]
        jadval.append({
            "indexDailyReturn": shakhes['dailyEfficiency']})
        jadval.append({
            "indexWeeklyReturn": shakhes['weeklyEfficiency']})
        jadval.append({
            "indexMonthlyReturn": shakhes['monthlyEfficiency']})
        jadval.append({
            "indexQuarterlyReturn": shakhes['quarterlyEfficiency']})
        jadval.append({
            "indexSixmonthsReturn": shakhes['sixMonthEfficiency']})
        jadval.append({
            "indexAnnualReturn": shakhes['annualEfficiency']})
        
    #AutoAgah
    name = "AutoAgah"
    navapi = "https://agahsectorfund.ir/api/v1/public/fundNavInfo/2"
    params = build_params(tarikh, today_str)
    apietelaat(name, api_periodic, api_daily, navapi, params)

    #AutoDariush
    name = "AutoDariush"
    api_periodic = "https://sector.dariush.fund/api/v1/public/fundReturnPeriodic/2"
    api_daily = "https://sector.dariush.fund/api/v1/public/fundReturnDaily/2"
    navapi = "https://sector.dariush.fund/api/v1/public/fundNavInfo/2"
    params = build_params(tarikh, today_str)
    apietelaat(name, api_periodic, api_daily, navapi, params)

    #BehinRo
    name = "BehinRo"
    api_periodic = "https://vistasectorfund.ir/api/v1/public/fundReturnPeriodic/1"
    api_daily = "https://vistasectorfund.ir/api/v1/public/fundReturnDaily/1"
    navapi = "https://vistasectorfund.ir/api/v1/public/fundNavInfo/1"
    params = build_params(tarikh, today_str)
    apietelaat(name, api_periodic, api_daily, navapi, params)

    all_data[tarikh] = jadval


print(all_data)

with open("manual_data.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

