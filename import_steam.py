import requests
import time
import re
import pyodbc
import os
import random

# ---------- CONFIG ----------
SQL_CONFIG = {
    "DRIVER": "{ODBC Driver 18 for SQL Server}",
    "SERVER": "localhost",
    "DATABASE": "Gamerz__db",
    "UID": "sa",
    "PWD": "GamerZ_Password123",
}

def get_conn():
    conn_str = (
        f"DRIVER={SQL_CONFIG['DRIVER']};"
        f"SERVER={SQL_CONFIG['SERVER']};"
        f"DATABASE={SQL_CONFIG['DATABASE']};"
        f"UID={SQL_CONFIG['UID']};"
        f"PWD={SQL_CONFIG['PWD']};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

# ---------- HELPERS ----------
def clean_html(text):
    if not text:
        return ""
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_specs_block(block):
    clean_text = clean_html(block)
    specs = {"os": "N/A", "cpu": "N/A", "ram": "N/A", "gpu": "N/A", "storage": "N/A"}
    patterns = {
        "os": r"OS\s*:?\s*(.*?)(?:Processor|Memory|Graphics|Storage|DirectX|$)",
        "cpu": r"Processor\s*:?\s*(.*?)(?:Memory|Graphics|Storage|DirectX|OS|$)",
        "ram": r"Memory\s*:?\s*(.*?)(?:Graphics|Storage|DirectX|OS|Processor|$)",
        "gpu": r"Graphics\s*:?\s*(.*?)(?:Storage|DirectX|OS|Processor|Memory|$)",
        "storage": r"Storage\s*:?\s*(.*?)(?:DirectX|Sound Card|Additional Notes|$)"
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            specs[key] = match.group(1).strip()
    return specs

def safe(value, default=""):
    return value if value not in (None, "") else default

# ---------- CORE LOGIC ----------
def process_game(app_id, gd, section, conn, session):
    """
    Process a single game's data and insert/update it in the database.
    """
    cur = conn.cursor()
    
    # --- 1. Basic Fields ---
    title = clean_html(safe(gd.get("name"), f"Unknown Game {app_id}"))
    print(f"[+] Processing: {title}...")

    # --- 2. Trailer Logic (MP4 -> DASH/HLS Fallback) ---
    trailer = ""
    if gd.get("movies"):
        m = gd["movies"][0]
        mp4_list = m.get("mp4", {})
        vals = list(mp4_list.values())
        trailer = mp4_list.get("max") or mp4_list.get("480") or (vals[0] if vals else "")
        if not trailer:
            trailer = m.get("dash_h264") or m.get("hls_h264") or ""

    # --- 3. Upsert Game ---
    cur.execute("SELECT id FROM dbo.games WHERE title = ?", (title,))
    row = cur.fetchone()

    # Manual Price Overrides (for games like GTA V that don't return price)
    MANUAL_PRICES = {
        271590: 29.99
    }

    if gd.get("is_free"):
        price = 0.0
        original_price = 0.0
    elif app_id in MANUAL_PRICES:
        price = MANUAL_PRICES[app_id]
        original_price = MANUAL_PRICES[app_id] # Assume no discount for manual overrides unless specified
    else:
        price_overview = gd.get("price_overview", {})
        price = price_overview.get("final", 0) / 100 if price_overview else 0.0
        original_price = price_overview.get("initial", 0) / 100 if price_overview else 0.0

    # --- Image Selection Logic ---
    vertical_url = f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{app_id}/library_600x900_2x.jpg"
    header_url = safe(gd.get("header_image"), f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg")
    
    # Check if vertical image exists (HEAD request)
    try:
        # Use a short timeout for the check to avoid slowing down too much
        check = session.head(vertical_url, timeout=2)
        if check.status_code == 200:
            image = vertical_url
        else:
            image = header_url
    except:
        # If check fails (timeout/error), fallback to header which is safer
        image = header_url

    description = clean_html(safe(gd.get("short_description"), "No description available."))
    # Fetch ALL genres
    genre_list = [g["description"] for g in (gd.get("genres") or [{"description": "Unknown"}])]
    genre = ", ".join(genre_list)
    
    # Fetch release date
    release_info = gd.get("release_date", {})
    release_date = release_info.get("date", "Unknown")
    
    # Calculate rating from Steam reviews (convert percentage to 1-10 scale)
    rating = None
    metacritic_info = gd.get("metacritic", {})
    if metacritic_info and metacritic_info.get("score"):
        # Use Metacritic score if available (0-100, convert to 0-10)
        rating = round(metacritic_info["score"] / 10, 1)
    else:
        # Fallback: use Steam review percentage
        recommendations = gd.get("recommendations", {})
        if recommendations and recommendations.get("total"):
            # Steam doesn't give percentage directly, so we'll use a default rating
            # You can enhance this by fetching review data separately
            rating = 7.5  # Default for games with reviews
    
    if row:
        game_id = row[0]
        cur.execute("""
            UPDATE dbo.games 
            SET price=?, original_price=?, image=?, trailer=?, description=?, genre=?, section=?, release_date=?, rating=?, stock_quantity=?
            WHERE id=?
        """, (price, original_price, image, trailer, description, genre, section, release_date, rating, 100, game_id))
    else:
        cur.execute("""
            INSERT INTO dbo.games (title, price, original_price, image, trailer, description, genre, rating, section, release_date, stock_quantity)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, price, original_price, image, trailer, description, genre, rating, section, release_date, 100))
        row = cur.fetchone()
        if not row:
            print(f"   [X] Failed to insert {title}")
            return
        game_id = row[0]

    # --- 4. Refresh Related Data ---
    cur.execute("DELETE FROM dbo.game_specs WHERE game_id = ?", (game_id,))
    cur.execute("DELETE FROM dbo.game_dlcs WHERE game_id = ?", (game_id,))
    cur.execute("DELETE FROM dbo.game_editions WHERE game_id = ?", (game_id,))
    cur.execute("DELETE FROM dbo.game_screenshots WHERE game_id = ?", (game_id,))
    
    # Specs
    pc_reqs = gd.get("pc_requirements", {})
    if isinstance(pc_reqs, dict) and (pc_reqs.get("minimum") or pc_reqs.get("recommended")):
        min_specs = parse_specs_block(pc_reqs.get("minimum", ""))
        rec_specs = parse_specs_block(pc_reqs.get("recommended", ""))
        cur.execute("""
            INSERT INTO dbo.game_specs 
            (game_id, min_os, min_cpu, min_ram, min_gpu, min_storage,
             rec_os, rec_cpu, rec_ram, rec_gpu, rec_storage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_id,
            min_specs["os"], min_specs["cpu"], min_specs["ram"], min_specs["gpu"], min_specs["storage"],
            rec_specs["os"], rec_specs["cpu"], rec_specs["ram"], rec_specs["gpu"], rec_specs["storage"]
        ))

    # DLCs (Fetch using session)
    if isinstance(gd.get("dlc"), list):
        dlc_ids = gd["dlc"][:3]
        if dlc_ids:
            for dlc_id in dlc_ids:
                try:
                    dresp = session.get(f"https://store.steampowered.com/api/appdetails?appids={dlc_id}&l=english", timeout=5)
                    dj = dresp.json()
                    if dj.get(str(dlc_id), {}).get("success"):
                        d = dj[str(dlc_id)]["data"]
                        d_price_overview = d.get("price_overview", {})
                        d_price = d_price_overview.get("final", 0) / 100 if d_price_overview else 0.0
                        d_orig_price = d_price_overview.get("initial", 0) / 100 if d_price_overview else 0.0
                        
                        cur.execute("""
                            INSERT INTO dbo.game_dlcs (game_id, title, price, original_price, description, image)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            game_id,
                            clean_html(safe(d.get("name"))),
                            d_price,
                            d_orig_price,
                            clean_html(safe(d.get("short_description"))),
                            safe(d.get("header_image"))
                        ))
                except Exception:
                    pass

    # Editions
    if gd.get("package_groups"):
        for group in gd["package_groups"]:
            for sub in group.get("subs", [])[:3]:
                sub_price = safe(sub.get("price_in_cents_with_discount", 0) / 100)
                savings = sub.get("percent_savings", 0)
                if savings > 0:
                    sub_orig_price = sub_price / (1 - (savings / 100))
                else:
                    sub_orig_price = sub_price

                cur.execute("""
                    INSERT INTO dbo.game_editions (game_id, title, price, original_price, description, image)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    game_id,
                    clean_html(safe(sub.get("option_text"), "Edition")).split(' - $')[0],
                    sub_price,
                    round(sub_orig_price, 2),
                    "Edition",
                    safe(gd.get("header_image"), image) # Use landscape header, fallback to vertical
                ))

    # Screenshots
    if isinstance(gd.get("screenshots"), list):
        for ss in gd["screenshots"][:5]:
            url = ss.get("path_full")
            if url:
                cur.execute("INSERT INTO dbo.game_screenshots (game_id, image_url) VALUES (?, ?)", (game_id, url))

    conn.commit()

def import_batch(games_map):
    app_ids = list(games_map.keys())
    ids_str = ",".join(str(x) for x in app_ids)
    
    print(f"Fetching batch: {ids_str} ...")
    
    try:
        # 1. Open Session and DB Connection
        USER_AGENTS = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]

        with requests.Session() as session:
            session.headers.update({
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://store.steampowered.com/'
            })
            conn = get_conn()
            
            # 2. Process each game sequentially
            for app_id in app_ids:
                print(f"Fetching {app_id} ...")
                try:
                    # Added cc=us to force USD currency
                    resp = session.get(f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=english&cc=us", timeout=15)
                    
                    if resp.status_code == 429:
                        print(f"[!] Rate limited (429). Pausing for 10 seconds...")
                        time.sleep(10)
                        continue
                    
                    if resp.status_code == 403:
                        print(f"[!] Access Denied (403). You might be temporarily blocked. Pausing for 60 seconds...")
                        time.sleep(60)
                        continue

                    if resp.status_code != 200:
                        print(f"[X] HTTP Error {resp.status_code} for {app_id}")
                        time.sleep(3) # Wait a bit even on other errors
                        continue
                        
                    data = resp.json()
                    if not data or not data.get(str(app_id), {}).get("success"):
                        print(f"[X] Failed to fetch data for {app_id}")
                        time.sleep(3)
                        continue
                        
                    section = games_map.get(app_id, "trending")
                    process_game(app_id, data[str(app_id)]["data"], section, conn, session)
                    
                    # Log success
                    with open("import_progress.txt", "a") as f:
                        f.write(f"{app_id}\n")

                    # Increased delay to 3 seconds to be very safe
                    time.sleep(3) 
                    
                except Exception as e:
                    print(f"[X] Error processing {app_id}: {e}")
            
            conn.close()
            print("Import completed.")
            
    except Exception as e:
        print(f"[X] Batch Error: {e}")

# ---------- RUN ----------
if __name__ == "__main__":
    DEFAULTS = {
        1593500: 'trending', # God of War
        1245620: 'trending', # Elden Ring
        1091500: 'trending', # Cyberpunk 2077
        2050650: 'trending', # Resident Evil 4
        271590: 'trending',  # Grand Theft Auto V
        601150: 'trending',  # Devil May Cry 5
        2215430: 'trending', # Ghost of Tsushima
        1808500: 'trending', # ARC Raiders
        289070: 'trending',  # Civilization VI (Strategy)
        367520: 'trending',  # Hollow Knight (Indie)
        1174180: 'trending', # Red Dead Redemption 2
        2668510: 'trending', # Red Dead Redemption
        883710: 'trending',  # Resident Evil 2
        952060: 'trending',  # Resident Evil 3
        418370: 'trending',  # Resident Evil 7
        1196590: 'trending', # Resident Evil Village
        1030300: 'trending', # Hollow Knight: Silksong
        1238840: 'trending', # Battlefield 1
        1238820: 'trending', # Battlefield 3
        1238860: 'trending', # Battlefield 4
        1238810: 'trending', # Battlefield V
        1517290: 'trending', # Battlefield 2042
        1238880: 'trending', # Battlefield Hardline
        1222140: 'trending', # Detroit: Become Human
        1903340: 'trending', # Clair Obscur: Expedition 33
        2592160: 'trending', # Dispatch
        2807960: 'trending', # Battlefield 6
        1145360: 'trending', # Hades
        1145350: 'trending', # Hades II
        3240220: 'trending'  # Grand Theft Auto V Enhanced
    }
    
    def load_custom_ids(filename):
        custom_map = {}
        if not os.path.exists(filename):
            print(f"File {filename} not found.")
            return custom_map
            
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                # Regex to find the last sequence of dots followed by digits
                # Handles cases like "Game Name.......12345" and "Game Name.......12345s"
                match = re.search(r'\.{2,}\s*(\d+)', line)
                if match:
                    app_id = int(match.group(1))
                    custom_map[app_id] = 'trending' # Default section
        return custom_map

    start_time = time.time()
    
    # Load custom IDs from file
    custom_ids = load_custom_ids("Games IDS.txt")
    DEFAULTS.update(custom_ids)
    
    print(f"Loaded {len(custom_ids)} games from file. Total games to process: {len(DEFAULTS)}")
    
    # Filter out already processed games
    PROGRESS_FILE = "import_progress.txt"
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            processed_ids = set(int(line.strip()) for line in f if line.strip().isdigit())
        print(f"Found {len(processed_ids)} already imported games. Skipping them.")
    else:
        processed_ids = set()

    # Create a new map with only unprocessed games
    games_to_process = {k: v for k, v in DEFAULTS.items() if k not in processed_ids}
    
    if not games_to_process:
        print("All games already imported!")
    else:
        try:
            import_batch(games_to_process)
        except KeyboardInterrupt:
            print("\n[!] Import interrupted by user. Progress saved.")
            
    print(f"Total Time: {time.time() - start_time:.2f}s")
