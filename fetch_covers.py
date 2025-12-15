import pyodbc
import requests
import time

# ==========================================
# CONFIGURATION
# ==========================================
# TODO: Enter your Twitch/IGDB API Keys here
CLIENT_ID = 'dieqxc999ufpwf6s7cpta2qn894fwm'
CLIENT_SECRET = 'v21sdv1zm5bykira88pot7fl3n1fnc'

# Database Connection String
DB_CONFIG = {
    'driver': '{ODBC Driver 18 for SQL Server}',
    'server': 'localhost',
    'database': 'Gamerz__db',
    'uid': 'sa',
    'pwd': 'GamerZ_Password123',
    'TrustServerCertificate': 'yes'
}

# ==========================================
# IGDB API FUNCTIONS
# ==========================================

def get_access_token(client_id, client_secret):
    """Authenticates with Twitch to get an IGDB access token."""
    url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, params=params)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Failed to authenticate: {response.text}")

def search_game(game_name, client_id, access_token):
    """Searches IGDB for a game and returns the vertical cover URL."""
    url = 'https://api.igdb.com/v4/games'
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}'
    }
    
    # Search for the game and get the cover image ID
    body = f'search "{game_name}"; fields name, cover.url; limit 1;'
    
    response = requests.post(url, headers=headers, data=body)
    
    if response.status_code == 200:
        data = response.json()
        if data and 'cover' in data[0]:
            # IGDB returns a thumbnail URL (t_thumb). We want high quality (t_cover_big_2x).
            # Example: //images.igdb.com/igdb/image/upload/t_thumb/co1r7x.jpg
            thumb_url = data[0]['cover']['url']
            if thumb_url.startswith('//'):
                thumb_url = 'https:' + thumb_url
            
            # Replace size for high quality vertical cover
            hq_url = thumb_url.replace('t_thumb', 't_cover_big_2x')
            return hq_url
    return None

# ==========================================
# DATABASE FUNCTIONS
# ==========================================

def get_db_connection():
    conn_str = f"DRIVER={DB_CONFIG['driver']};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['uid']};PWD={DB_CONFIG['pwd']};TrustServerCertificate={DB_CONFIG['TrustServerCertificate']}"
    return pyodbc.connect(conn_str)

def main():
    if CLIENT_ID == 'YOUR_CLIENT_ID_HERE' or CLIENT_SECRET == 'YOUR_CLIENT_SECRET_HERE':
        print("ERROR: Please open this script and enter your IGDB Client ID and Secret.")
        return

    print("Authenticating with IGDB...")
    try:
        token = get_access_token(CLIENT_ID, CLIENT_SECRET)
        print("Authentication successful!")
    except Exception as e:
        print(e)
        return

    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch all games
    print("Fetching games from database...")
    cur.execute("SELECT id, title FROM dbo.games")
    games = cur.fetchall()

    print(f"Found {len(games)} games. Starting update process...")
    print("-" * 50)

    updated_count = 0
    
    for game in games:
        game_id = game.id
        title = game.title
        
        print(f"Processing: {title}...")
        
        # 1. Search IGDB
        new_image_url = search_game(title, CLIENT_ID, token)
        
        if new_image_url:
            # 2. Update Database
            print(f"  -> Found Cover: {new_image_url}")
            cur.execute("UPDATE dbo.games SET image = ? WHERE id = ?", (new_image_url, game_id))
            conn.commit()
            updated_count += 1
        else:
            print("  -> No cover found.")
            
        # Respect API Rate Limits (4 requests per second is safe)
        time.sleep(0.25)

    conn.close()
    print("-" * 50)
    print(f"Done! Updated {updated_count} games.")

if __name__ == "__main__":
    main()
