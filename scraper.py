import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os
from datetime import datetime
import zoneinfo

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest"
}

def extract_all_jakbar_venues():
    venues = []
    page = 1
    while True:
        url = (
            f"https://ayo.co.id/venues?tipe=venue"
            f"&lokasi=Kota%20Jakarta%20Barat%2C%20Daerah%20Khusus%20Ibukota%20Jakarta%2C%20Indonesia"
            f"&cabor=12&page={page}"
        )
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code != 200:
                break
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.find_all("a", href=re.compile(r"/v/"))
            if not cards:
                break
            new_found = 0
            for card in cards:
                href = card.get("href", "")
                slug = href.split("/v/")[-1].split("?")[0].strip("/")
                if slug and slug not in [v["slug"] for v in venues]:
                    venues.append({"slug": slug})
                    new_found += 1
            if new_found == 0:
                break
            page += 1
            time.sleep(0.3)
        except Exception:
            break
    return venues

def get_venue_details(slug):
    url = f"https://ayo.co.id/v/{slug}"
    venue_id = None
    venue_name = slug.replace("-", " ").title()
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            h1 = soup.find("h1")
            if h1 and h1.get_text(strip=True):
                venue_name = h1.get_text(strip=True)
            elif soup.title and soup.title.string:
                venue_name = soup.title.string.split("|")[0].split("-")[0].strip()

            venue_name = re.sub(r"^Venue\s+", "", venue_name, flags=re.IGNORECASE).strip()

            vid_match = re.search(r"venue_id[\"']?\s*[:=]\s*[\"']?(\d+)", res.text)
            if vid_match:
                venue_id = int(vid_match.group(1))
            else:
                v_match = re.search(r"/venue/(\d+)", res.text) or re.search(r"/venues-ajax/(\d+)", res.text)
                if v_match:
                    venue_id = int(v_match.group(1))
    except Exception:
        pass
        
    if not venue_id and slug == "hobi-padel-meruya":
        venue_id = 2110
        venue_name = "Hobi Padel Meruya"

    return venue_id, venue_name

def get_field_ids(venue_id):
    url = f"https://ayo.co.id/venues-ajax/{venue_id}/get-field-list?venue_id={venue_id}"
    fields = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            items = data if isinstance(data, list) else data.get("data", [])
            for item in items:
                fid = item.get("id") or item.get("field_id")
                fname = item.get("name", f"Court {fid}")
                if fid:
                    fields.append({"field_id": fid, "field_name": fname})
    except Exception:
        pass
    return fields

def scrape_slots(venue_id, venue_name, field_id, field_name, target_date):
    url = f"https://ayo.co.id/venue/{venue_id}/field/{field_id}/slots?date={target_date}"
    records = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            slots_data = res.json()
            if isinstance(slots_data, list):
                for slot in slots_data:
                    records.append({
                        "slot_key": f"{venue_id}_{field_id}_{slot.get('start_time')[:5]}",
                        "venue_id": venue_id,
                        "venue_name": venue_name,
                        "field_id": field_id,
                        "field_name": field_name,
                        "date": target_date,
                        "time_slot": f"{slot.get('start_time')[:5]} - {slot.get('end_time')[:5]}",
                        "price": slot.get("price", 0),
                        "status": "Available" if slot.get("is_available") == 1 else "Booked"
                    })
    except Exception:
        pass
    return records

if __name__ == "__main__":
    tz_wib = zoneinfo.ZoneInfo("Asia/Jakarta")
    now_wib = datetime.now(tz_wib)
    
    target_date = now_wib.strftime("%Y-%m-%d")
    print(f"[{now_wib.strftime('%H:%M:%S')} WIB] Menjalankan sinkronisasi slot untuk tanggal: {target_date}")
    
    venues_list = extract_all_jakbar_venues()
    current_slots = []
    
    for v in venues_list:
        v_id, v_name = get_venue_details(v["slug"])
        if not v_id:
            continue
        fields = get_field_ids(v_id)
        for f in fields:
            slots = scrape_slots(v_id, v_name, f["field_id"], f["field_name"], target_date)
            current_slots.extend(slots)
            time.sleep(0.08)

    df_current = pd.DataFrame(current_slots)
    raw_file = f"raw_slots_{target_date}.csv"
    
    if os.path.exists(raw_file):
        df_master = pd.read_csv(raw_file)
        combined = pd.concat([df_master, df_current], ignore_index=True)
        # Menghapus duplikat slot_key dan mempertahankan tarikan data paling baru (keep="last")
        df_final_slots = combined.drop_duplicates(subset=["slot_key"], keep="last")
    else:
        df_final_slots = df_current

    df_final_slots.to_csv(raw_file, index=False)

    if not df_final_slots.empty:
        df_final_slots["price"] = pd.to_numeric(df_final_slots["price"], errors="coerce").fillna(0)
        venue_records = []
        
        for idx, ((venue_id, venue_name), group) in enumerate(df_final_slots.groupby(["venue_id", "venue_name"]), start=1):
            total_slots = len(group)
            avail = (group["status"] == "Available").sum()
            booked = (group["status"] == "Booked").sum()
            occ = (booked / total_slots * 100) if total_slots > 0 else 0.0
            rev = group[group["status"] == "Booked"]["price"].sum()
            
            p_min, p_max = group["price"].min(), group["price"].max()
            p_range = f"Rp{p_min:,.0f}".replace(",", ".") if p_min == p_max else f"Rp{p_min:,.0f} - Rp{p_max:,.0f}".replace(",", ".")

            venue_records.append({
                "No": idx,
                "Venue": venue_name,
                "Slots": total_slots,
                "Available": avail,
                "Occupancy %": f"{occ:.1f}%",
                "Revenue": f"Rp{rev:,.0f}".replace(",", "."),
                "Range Harga": p_range
            })
            
        df_venues = pd.DataFrame(venue_records)
        final_filename = f"laporan_padel_{target_date}_final.csv"
        df_venues.to_csv(final_filename, index=False)
        print(f"Berhasil memperbarui: {final_filename}")
