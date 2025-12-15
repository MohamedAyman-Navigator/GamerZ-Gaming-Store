# app.py
import datetime

import random
import string
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai

import os
from werkzeug.utils import secure_filename
import pyodbc

app = Flask(__name__)
app.secret_key = 'gamerz_secret_key_2025'

# ---------- CONFIG ----------
GEMINI_API_KEY = "PASTE YOUR API HERE"
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- AI MODEL SETUP ----------
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    print(f"Error configuring AI: {e}")
    model = None

# ---------- DATABASE CONFIG ----------
DB_CONFIG = {
    "DRIVER": "{ODBC Driver 18 for SQL Server}",
    "SERVER": "localhost",
    "DATABASE": "Gamerz__db",
    "UID": "sa",
    "PWD": "GamerZ_Password123",
}

def get_db_connection():
    # Build and return a pyodbc connection to SQL Server
    conn_str = (
        f"DRIVER={DB_CONFIG['DRIVER']};"
        f"SERVER={DB_CONFIG['SERVER']};"
        f"DATABASE={DB_CONFIG['DATABASE']};"
        f"UID={DB_CONFIG['UID']};"
        f"PWD={DB_CONFIG['PWD']};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

# ---------- UTILS: convert cursor results to dicts ----------
def fetch_all_dicts(cursor):
    # Convert cursor.fetchall() tuples into list of dicts using cursor.description
    cols = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(cols, row)) for row in rows]

def fetch_one_dict(cursor):
    # Convert a single row into dict or return None
    row = cursor.fetchone()
    if not row:
        return None
    cols = [col[0] for col in cursor.description]
    return dict(zip(cols, row))

# ---------- FILE HELPERS ----------
def allowed_file(filename):
    # Check extension whitelist
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- GLOBAL GAME EXTRAS ----------


def get_all_game_specs():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT title, description, price, genre, rating FROM dbo.games')
    rows = fetch_all_dicts(cur)
    conn.close()

    spec_list = []
    for game in rows:
        info = f"Title: {game['title']} | Genre: {game.get('genre')} | Price: ${game.get('price')} | Rating: {game.get('rating')}"
        spec_list.append(info)
    return "\n".join(spec_list)

# ---------- ADMIN CHECK ----------
def is_admin():
    return session.get('user_id') == 1

# ---------- ROUTES ----------
@app.route('/')
def home():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Main Games (Base Games) - Fetch landscape image from game_editions (header)
        cur.execute("""
            SELECT g.*, 
            (SELECT TOP 1 image FROM dbo.game_editions e WHERE e.game_id = g.id) as landscape_image
            FROM dbo.games g 
            WHERE g.genre NOT IN ('DLC', 'Edition') 
            ORDER BY g.title ASC
        """)
        games = fetch_all_dicts(cur)
        
        # DLCs
        cur.execute("""
            SELECT g.*, 
            (SELECT TOP 1 image FROM dbo.game_editions e WHERE e.game_id = g.id) as landscape_image
            FROM dbo.games g 
            WHERE g.genre = 'DLC' 
            ORDER BY g.title ASC
        """)
        dlcs = fetch_all_dicts(cur)
        
        # Editions
        cur.execute("""
            SELECT g.*, 
            (SELECT TOP 1 image FROM dbo.game_editions e WHERE e.game_id = g.id) as landscape_image
            FROM dbo.games g 
            WHERE g.genre = 'Edition' 
            ORDER BY g.title ASC
        """)
        editions = fetch_all_dicts(cur)
        
        # Survival Horror Query
        horror_query = """
            SELECT g.*, 
            (SELECT TOP 1 image FROM dbo.game_editions e WHERE e.game_id = g.id) as landscape_image
            FROM dbo.games g 
            WHERE 
            (g.genre LIKE '%Horror%' OR g.genre LIKE '%Survival%' OR g.title IN ('Outlast', 'Amnesia', 'Dead Space', 'Silent Hill', 'Phasmophobia', 'The Forest', 'Resident Evil', 'Alien: Isolation', 'Evil Within', 'Five Nights at Freddy''s', 'Until Dawn', 'Soma', 'Dying Light', 'Left 4 Dead'))
            AND g.genre NOT IN ('DLC', 'Edition')
        """
        cur.execute(horror_query)
        survival_horror = fetch_all_dicts(cur)

        # Refresh user session photo if logged in
        if 'user_id' in session:
            cur.execute('SELECT profile_photo FROM dbo.users WHERE id = ?', (session['user_id'],))
            user_row = cur.fetchone()
            if user_row and user_row[0]:
                session['profile_photo'] = user_row[0]

        conn.close()

        featured_slides = [
            { 'id': 1, 'title': "Monster Hunter Wilds", 'subtitle': "Pre-Order Available: February 28, 2025", 'tagline': "The next generation of the hunt.", 'image': "/static/assets/featured/featured_mh.jpg", 'link': "/game/mh-wilds" },
            { 'id': 2, 'title': "GTA VI: Postponed!", 'subtitle': "Pre-order now for Nov 2026 delivery.", 'tagline': "The ultimate open-world delay is confirmed.", 'image': "/static/assets/featured/featured_gta.jpg", 'link': "/preorder-gta6" },
            { 'id': 3, 'title': "RTX 5090 Launch", 'subtitle': "The Blackwall Beast is Here.", 'tagline': "Experience 8K gaming and run local AI models on 32GB GDDR7 VRAM.", 'image': "/static/assets/featured/featured_rtx.jpg", 'link': "/hardware/5090" }
        ]

        return render_template('index.html', games=games, dlcs=dlcs, editions=editions, survival_horror=survival_horror, featured_slides=featured_slides)
    except Exception as e:
        return f"Database Error: {e}"

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        # File upload handling for profile photo
        if 'profile_photo' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['profile_photo']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            import time
            ext = file.filename.rsplit('.', 1)[1].lower()
            timestamp = int(time.time())
            filename = secure_filename(f"user_{session['user_id']}_{timestamp}.{ext}")
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            cur.execute('UPDATE dbo.users SET profile_photo = ? WHERE id = ?', (filename, session['user_id']))
            conn.commit()
            session['profile_photo'] = filename
            flash('Profile photo updated!')
        else:
            flash('Invalid file type. Allowed: png, jpg, jpeg, gif')

    cur.execute('SELECT * FROM dbo.users WHERE id = ?', (session['user_id'],))
    user = fetch_one_dict(cur)

    # Get user library (orders join games)
    cur.execute('''
        SELECT g.title, g.image, o.[key], o.purchase_date, u.email
        FROM dbo.orders o
        JOIN dbo.games g ON o.game_id = g.id
        JOIN dbo.users u ON o.user_id = u.id
        WHERE o.user_id = ?
        ORDER BY o.purchase_date DESC
    ''', (session['user_id'],))
    library = fetch_all_dicts(cur)

    conn.close()
    return render_template('profile.html', user=user, library=library)

@app.route('/game/<int:game_id>')
def game_details(game_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM dbo.games WHERE id = ?', (game_id,))
    game = fetch_one_dict(cur)

    if game is None:
        conn.close()
        return "Game not found", 404



    owned_game_ids = []
    if 'user_id' in session:
        cur.execute('SELECT game_id FROM dbo.orders WHERE user_id = ?', (session['user_id'],))
        rows = cur.fetchall()
        owned_game_ids = [r[0] for r in rows]

    # 3. Get Extra Details (Specs, Screenshots, DLCs, Editions)
    # Initialize empty extras structure
    extras = {'specs': {}, 'screenshots': [], 'dlcs': [], 'editions': []}

    # A. Fetch Specs
    cur.execute('SELECT * FROM dbo.game_specs WHERE game_id = ?', (game_id,))
    specs_row = fetch_one_dict(cur)
    if specs_row:
        extras['specs'] = {
            'min': {'os': specs_row['min_os'], 'cpu': specs_row['min_cpu'], 'ram': specs_row['min_ram'], 'gpu': specs_row['min_gpu'], 'storage': specs_row['min_storage']},
            'rec': {'os': specs_row['rec_os'], 'cpu': specs_row['rec_cpu'], 'ram': specs_row['rec_ram'], 'gpu': specs_row['rec_gpu'], 'storage': specs_row['rec_storage']}
        }

    # B. Fetch Screenshots
    cur.execute('SELECT image_url FROM dbo.game_screenshots WHERE game_id = ?', (game_id,))
    shot_rows = cur.fetchall()
    for row in shot_rows:
        extras['screenshots'].append(row[0])
        
    # C. Fetch DLCs
    cur.execute('SELECT title, price, original_price, image FROM dbo.game_dlcs WHERE game_id = ?', (game_id,))
    dlc_rows = cur.fetchall()
    for d_title, d_price, d_orig, d_img in dlc_rows:
        extras['dlcs'].append({
            'title': d_title,
            'price': d_price,
            'original_price': d_orig,
            'image': d_img
        })

    # D. Fetch Editions
    cur.execute('SELECT title, price, original_price, description, image FROM dbo.game_editions WHERE game_id = ?', (game_id,))
    edition_rows = cur.fetchall()
    for e_title, e_price, e_orig, e_desc, e_img in edition_rows:
        extras['editions'].append({
            'title': e_title,
            'price': e_price,
            'original_price': e_orig,
            'desc': e_desc,
            'image': e_img
        })

    # E. Fetch Recommended Games (Smart Logic)
    recommended_games = []
    if game.get('title') and game.get('genre'):
        # 1. Identify Series (First 2 words or whole title if short)
        title_parts = game['title'].split()
        if len(title_parts) > 1:
            series_title = " ".join(title_parts[:2]) # e.g., "Call of" from "Call of Duty"
        else:
            series_title = title_parts[0]
            
        # 2. Fetch Sequels/Prequels (Priority 1)
        cur.execute("""
            SELECT TOP 5 g.*, 
            (SELECT TOP 1 image FROM dbo.game_editions e WHERE e.game_id = g.id) as landscape_image
            FROM dbo.games g
            WHERE g.title LIKE ? AND g.id != ? AND g.genre NOT IN ('DLC', 'Edition')
        """, (f'%{series_title}%', game_id))
        sequels = fetch_all_dicts(cur)
        
        # 3. Fetch High Rated Genre Matches (Priority 2)
        main_genre = game['genre'].split(',')[0].strip()
        cur.execute("""
            SELECT TOP 10 g.*, 
            (SELECT TOP 1 image FROM dbo.game_editions e WHERE e.game_id = g.id) as landscape_image
            FROM dbo.games g
            WHERE g.genre LIKE ? AND g.id != ? AND g.genre NOT IN ('DLC', 'Edition')
            ORDER BY g.rating DESC
        """, (f'%{main_genre}%', game_id))
        high_rated = fetch_all_dicts(cur)
        
        # 4. Combine & Deduplicate
        seen_ids = {game_id}
        final_list = []
        
        # Add sequels first
        for g in sequels:
            if g['id'] not in seen_ids:
                final_list.append(g)
                seen_ids.add(g['id'])
                
        # Add high rated to fill up to 5
        for g in high_rated:
            if len(final_list) >= 5:
                break
            if g['id'] not in seen_ids:
                final_list.append(g)
                seen_ids.add(g['id'])
                
        recommended_games = final_list

    conn.close()
    return render_template('game_details.html', game=game, extras=extras, owned_game_ids=owned_game_ids, recommended_games=recommended_games)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM dbo.users WHERE username = ?', (username,))
        user = fetch_one_dict(cur)
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            flash('Invalid Codename or Password!')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/admin')
def admin_index():
    if not is_admin():
        flash("Access Denied: Admin Clearance Required.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM dbo.games')
    games = fetch_all_dicts(cur)
    
    # Fetch landscape images from game_editions for each game
    for game in games:
        cur.execute('SELECT TOP 1 image FROM dbo.game_editions WHERE game_id = ?', (game['id'],))
        edition_row = cur.fetchone()
        if edition_row and edition_row[0]:
            game['landscape_image'] = edition_row[0]
        else:
            # Fallback to original image if no edition exists
            game['landscape_image'] = game['image']
    
    conn.close()
    
    # Calculate statistics
    total_games = len(games)
    action_games = sum(1 for game in games if game.get('genre') and 'Action' in game['genre'])
    rpg_games = sum(1 for game in games if game.get('genre') and 'RPG' in game['genre'])
    strategy_games = sum(1 for game in games if game.get('genre') and 'Strategy' in game['genre'])
    indie_games = sum(1 for game in games if game.get('genre') and 'Indie' in game['genre'])
    adventure_games = sum(1 for game in games if game.get('genre') and 'Adventure' in game['genre'])
    
    prices = [game.get('price', 0) for game in games if game.get('price')]
    total_value = sum(prices)
    avg_price = total_value / len(prices) if prices else 0
    max_price = max(prices) if prices else 0
    min_price = min(prices) if prices else 0
    
    # Genre distribution for chart
    genre_stats = {
        'Action': action_games,
        'RPG': rpg_games,
        'Strategy': strategy_games,
        'Indie': indie_games,
        'Adventure': adventure_games
    }
    
    # Top 5 most expensive games
    sorted_games = sorted(games, key=lambda x: x.get('price', 0), reverse=True)[:5]
    top_games = [{'title': g['title'], 'price': g.get('price', 0)} for g in sorted_games]
    
    # Rating distribution (group by rating ranges)
    # Filter out non-numeric ratings and handle SQL Server Decimal types
    ratings = []
    for game in games:
        rating = game.get('rating')
        if rating is not None:
            try:
                # Convert to float - handles int, float, Decimal, and numeric strings
                rating_val = float(rating)
                if 0 <= rating_val <= 10:  # Only valid ratings
                    ratings.append(rating_val)
            except (ValueError, TypeError):
                pass  # Skip invalid ratings (like 'M' strings)
    
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    # Rating distribution buckets
    rating_dist = {
        '9-10': sum(1 for r in ratings if 9 <= r <= 10),
        '8-9': sum(1 for r in ratings if 8 <= r < 9),
        '7-8': sum(1 for r in ratings if 7 <= r < 8),
        '6-7': sum(1 for r in ratings if 6 <= r < 7),
        '0-6': sum(1 for r in ratings if 0 <= r < 6)
    }
    
    # Top 5 highest rated games
    games_with_ratings = [g for g in games if g.get('rating') is not None]
    try:
        sorted_by_rating = sorted(games_with_ratings, key=lambda x: float(x.get('rating', 0)), reverse=True)[:5]
        top_rated_games = [{'title': g['title'], 'rating': float(g.get('rating', 0))} for g in sorted_by_rating]
    except (ValueError, TypeError):
        top_rated_games = []
    
    stats = {
        'total_games': total_games,
        'action_games': action_games,
        'rpg_games': rpg_games,
        'total_value': total_value,
        'avg_price': avg_price,
        'max_price': max_price,
        'min_price': min_price,
        'genre_stats': genre_stats,
        'top_games': top_games,
        'avg_rating': avg_rating,
        'rating_dist': rating_dist,
        'top_rated_games': top_rated_games
    }
    
    return render_template('admin_index.html', games=games, stats=stats)

@app.route('/admin/add', methods=['GET', 'POST'])
def admin_add():
    if not is_admin():
        flash("Access Denied: Admin Clearance Required.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO dbo.games (title, price, original_price, image, trailer, description, genre, rating, stock_quantity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (request.form['title'], request.form['price'], request.form['original_price'] or None, request.form['image'], request.form['trailer'], request.form['description'], request.form['genre'], request.form['rating'], request.form['stock_quantity']))
        conn.commit()
        conn.close()
        flash(f"Game '{request.form['title']}' added successfully.")
        return redirect(url_for('admin_index'))

    return render_template('admin_form.html', game={})

@app.route('/admin/edit/<int:game_id>', methods=['GET', 'POST'])
def admin_edit(game_id):
    if not is_admin():
        flash("Access Denied: Admin Clearance Required.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        cur.execute('UPDATE dbo.games SET title=?, price=?, original_price=?, image=?, trailer=?, description=?, genre=?, rating=?, stock_quantity=? WHERE id=?',
                     (request.form['title'], request.form['price'], request.form['original_price'] or None, request.form['image'], request.form['trailer'], request.form['description'], request.form['genre'], request.form['rating'], request.form['stock_quantity'], game_id))
        conn.commit()
        conn.close()
        flash(f"Game '{request.form['title']}' updated successfully.")
        return redirect(url_for('admin_index'))

    cur.execute('SELECT * FROM dbo.games WHERE id = ?', (game_id,))
    game = fetch_one_dict(cur)
    conn.close()
    if game is None:
        flash("Game not found.")
        return redirect(url_for('admin_index'))

    return render_template('admin_form.html', game=game)

@app.route('/admin/delete/<int:game_id>', methods=['POST'])
def admin_delete(game_id):
    if not is_admin():
        flash("Access Denied: Admin Clearance Required.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM dbo.games WHERE id = ?', (game_id,))
    conn.commit()
    conn.close()
    flash("Game deleted successfully.")
    return redirect(url_for('admin_index'))

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.json
    game_id = data.get('game_id')

    # Check stock availability
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT stock_quantity FROM dbo.games WHERE id = ?', (game_id,))
    result = cur.fetchone()
    conn.close()
    
    if not result or (result[0] is not None and result[0] <= 0):
        return jsonify({"status": "out_of_stock", "message": "This game is out of stock"}), 400

    if 'cart' not in session:
        session['cart'] = []

    if game_id not in session['cart']:
        session['cart'].append(game_id)
        session.modified = True
        return jsonify({"status": "success", "cart_count": len(session['cart'])})
    else:
        return jsonify({"status": "exists", "cart_count": len(session['cart'])})


@app.route('/cart')
def view_cart():
    if 'cart' not in session or not session['cart']:
        return render_template('cart.html', games=[], total=0)

    conn = get_db_connection()
    cur = conn.cursor()
    placeholders = ','.join('?' for _ in session['cart'])
    query = f'SELECT * FROM dbo.games WHERE id IN ({placeholders})'
    cur.execute(query, session['cart'])
    cart_games = fetch_all_dicts(cur)
    conn.close()

    total_price = sum(game['price'] for game in cart_games)
    return render_template('cart.html', games=cart_games, total=round(total_price, 2))

@app.route('/remove_from_cart/<int:game_id>')
def remove_from_cart(game_id):
    if 'cart' in session:
        cart = session['cart']
        session['cart'] = [id for id in cart if id != game_id]
        session.modified = True
    return redirect(url_for('view_cart'))

@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('home'))

@app.route('/checkout')
def checkout():
    if 'cart' not in session or not session['cart']:
        return redirect(url_for('home'))

    conn = get_db_connection()
    cur = conn.cursor()
    placeholders = ','.join('?' for _ in session['cart'])
    query = f'SELECT * FROM dbo.games WHERE id IN ({placeholders})'
    cur.execute(query, session['cart'])
    cart_games = fetch_all_dicts(cur)

    purchased_items = []
    total_price = 0
    user_id = session.get('user_id')

    for game in cart_games:
        part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        part3 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        part4 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        fake_key = f"{part1}-{part2}-{part3}-{part4}"

        purchased_items.append({
            'title': game['title'],
            'image': game['image'],
            'key': fake_key
        })
        total_price += game['price']

        if user_id:
            cur.execute('INSERT INTO dbo.orders (user_id, game_id, [key]) VALUES (?, ?, ?)',
                         (user_id, game['id'], fake_key))
            
            # Decrease stock quantity by 1
            cur.execute('UPDATE dbo.games SET stock_quantity = stock_quantity - 1 WHERE id = ? AND stock_quantity > 0',
                         (game['id'],))

    if user_id:
        conn.commit()

    conn.close()
    session.pop('cart', None)
    return render_template('order_success.html', items=purchased_items, total=total_price)

@app.route('/chat', methods=['POST'])
def chat():
    if not model:
        return jsonify({"reply": "Error: AI Model failed to load."})

    data = request.json
    user_input = data.get('message')
    history = data.get('history', [])

    chat_session = model.start_chat(history=history)
    current_game_inventory = get_all_game_specs()
    today = datetime.date.today().strftime("%B %d, %Y")

    current_context = (
        f"IMPORTANT SYSTEM CONTEXT:\n"
        f"1. TODAY'S DATE: {today}.\n"
        f"2. HARDWARE STATUS (Released & In Stock): NVIDIA RTX 5090 (Released Jan 2025, $1999, 32GB VRAM).\n"
        f"3. GAME STATUS (Based on Store Data):\n"
        f"{current_game_inventory}\n"
        f"4. SPECIAL ALERTS:\n"
        f"   - GTA VI: DELAYED to Nov 2026. (Pre-order only).\n"
        f"5. ROLE: You are the Assistant for 'GamerZ'.\n"
        f"   - Use the inventory list above for all pricing and game facts.\n"
        f"6. FORMATTING RULES:\n"
        f"   - Use bold for key terms (Game Titles, Prices, Specs).\n"
        f"   - Use bullet points for lists (Editions, DLCs, Specs).\n"
        f"   - Keep answers concise and easy to read.\n"
    )

    full_message = f"{current_context}\nUser Query: {user_input}"

    try:
        response = chat_session.send_message(full_message)
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"AI ERROR: {e}")
        return jsonify({"reply": f"Technical Error: {e}"})


def mh_wilds():
    item = {
        'title': "Monster Hunter Wilds",
        'image': "/static/assets/featured/featured_mh.jpg",
        'category': "Action RPG",
        'rating': "TBD",
        'description': "The next generation of the hunt is here. Monster Hunter Wilds brings a new level of immersion, seamless open-world exploration, and the most ferocious monsters yet. Pre-order now to secure exclusive in-game bonuses.",
        'price': "69.99",
        'specs': [
            "Release Date: Feb 28, 2025",
            "Platform: PC, PS5, Xbox Series X",
            "Co-op: Up to 4 Players",
            "Engine: RE Engine",
            "Open World: Seamless"
        ]
    }
    return render_template('hardware_details.html', item=item)

@app.route('/preorder-gta6')
def gta6_preorder():
    item = {
        'title': "Grand Theft Auto VI",
        'image': "/static/assets/featured/featured_gta.jpg",
        'category': "Open World Action",
        'rating': "RP",
        'description': "Welcome to Leonida. Grand Theft Auto VI heads to the state of Leonida, home to the neon-soaked streets of Vice City and beyond in the biggest, most immersive evolution of the Grand Theft Auto series yet.",
        'price': "69.99",
        'specs': [
            "Release Date: Fall 2025 (Delayed to Nov 2026)",
            "Location: Vice City / Leonida",
            "Protagonists: Lucia & Jason",
            "Map Size: Largest ever",
            "Online: GTA Online 2.0 included"
        ]
    }
    return render_template('hardware_details.html', item=item)

@app.route('/hardware/<id>')
def hardware_details(id):
    # Hardcoded data for demo purposes
    if id == '5090':
        item = {
            'title': "NVIDIA GeForce RTX 5090",
            'image': "/static/assets/featured/featured_rtx.jpg",
            'category': "Graphics Card",
            'rating': "9.9",
            'description': "The new king of gaming GPUs. Powered by the Blackwell architecture, the RTX 5090 delivers unprecedented performance for 8K gaming and professional AI workflows. Featuring 32GB of next-gen GDDR7 memory and DLSS 4.0 support.",
            'price': "1,999.00",
            'specs': [
                "Architecture: Blackwell",
                "VRAM: 32GB GDDR7",
                "Bus Width: 512-bit",
                "Boost Clock: 3.1 GHz",
                "DLSS 4.0 with Frame Gen 2"
            ]
        }
        return render_template('hardware_details.html', item=item)
    return "Item not found", 404


@app.route('/view_all/<category>')
def view_all(category):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Map friendly category names to SQL queries
    if category == 'Trending':
        # Logic for "Trending Now" - 2025 releases
        cur.execute("""
            SELECT g.*, 
            (SELECT TOP 1 image FROM dbo.game_editions e WHERE e.game_id = g.id) as landscape_image
            FROM dbo.games g 
            WHERE g.genre NOT IN ('DLC', 'Edition') 
            ORDER BY g.title ASC
        """)
        all_games = fetch_all_dicts(cur)
        games = [g for g in all_games if g.get('release_date') and '2025' in str(g['release_date'])]
        
    elif category == 'Special Editions':
        cur.execute("""
            SELECT g.*, 
            (SELECT TOP 1 image FROM dbo.game_editions e WHERE e.game_id = g.id) as landscape_image
            FROM dbo.games g 
            WHERE g.genre = 'Edition' 
            ORDER BY g.title ASC
        """)
        games = fetch_all_dicts(cur)
        
    elif category == 'DLCs':
        cur.execute("""
            SELECT g.*, 
            (SELECT TOP 1 image FROM dbo.game_editions e WHERE e.game_id = g.id) as landscape_image
            FROM dbo.games g 
            WHERE g.genre = 'DLC' 
            ORDER BY g.title ASC
        """)
        games = fetch_all_dicts(cur)
        
    elif category == 'Survival Horror':
        horror_query = """
            SELECT g.*, 
            (SELECT TOP 1 image FROM dbo.game_editions e WHERE e.game_id = g.id) as landscape_image
            FROM dbo.games g 
            WHERE 
            (g.genre LIKE '%Horror%' OR g.genre LIKE '%Survival%' OR g.title LIKE '%Outlast%' OR g.title LIKE '%Amnesia%' OR g.title LIKE '%Dead Space%' OR g.title LIKE '%Silent Hill%' OR g.title LIKE '%Phasmophobia%' OR g.title LIKE '%The Forest%' OR g.title LIKE '%Resident Evil%' OR g.title LIKE '%Alien: Isolation%' OR g.title LIKE '%Evil Within%' OR g.title LIKE '%Five Nights at Freddy''s%' OR g.title LIKE '%Until Dawn%' OR g.title LIKE '%Soma%' OR g.title LIKE '%Dying Light%' OR g.title LIKE '%Left 4 Dead%')
            AND g.genre NOT IN ('DLC', 'Edition')
            ORDER BY g.title ASC
        """
        cur.execute(horror_query)
        games = fetch_all_dicts(cur)
        
    elif category == 'Open World':
        cur.execute("""
            SELECT g.*, 
            (SELECT TOP 1 image FROM dbo.game_editions e WHERE e.game_id = g.id) as landscape_image
            FROM dbo.games g 
            WHERE 
            (g.genre LIKE '%Open World%' OR g.genre LIKE '%Adventure%' OR g.genre LIKE '%RPG%' OR g.title LIKE '%GTA%' OR g.title LIKE '%Red Dead%' OR g.title LIKE '%Cyberpunk%' OR g.title LIKE '%Elden Ring%' OR g.title LIKE '%Ghost of Tsushima%' OR g.title LIKE '%Assassin''s Creed%' OR g.title LIKE '%Far Cry%' OR g.title LIKE '%Horizon%')
            AND g.genre NOT IN ('DLC', 'Edition')
            ORDER BY g.title ASC
        """)
        games = fetch_all_dicts(cur)
        
    elif category == 'All Games':
        cur.execute("""
            SELECT g.*, 
            (SELECT TOP 1 image FROM dbo.game_editions e WHERE e.game_id = g.id) as landscape_image
            FROM dbo.games g 
            WHERE g.genre NOT IN ('DLC', 'Edition') 
            ORDER BY g.title ASC
        """)
        games = fetch_all_dicts(cur)
        
    else:
        # Standard Genre Filter
        cur.execute("""
            SELECT g.*, 
            (SELECT TOP 1 image FROM dbo.game_editions e WHERE e.game_id = g.id) as landscape_image
            FROM dbo.games g 
            WHERE g.genre LIKE ? AND g.genre NOT IN ('DLC', 'Edition') 
            ORDER BY g.title ASC
        """, (f'%{category}%',))
        games = fetch_all_dicts(cur)
    
    conn.close()
    
    # Pagination Logic
    total_games = len(games)
    total_pages = (total_games + per_page - 1) // per_page
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages)) if total_pages > 0 else 1
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated_games = games[start:end]
    
    # Smart Pagination: 1 ... 4 5 6 ... 20
    page_range = []
    if total_pages <= 7:
        page_range = list(range(1, total_pages + 1))
    else:
        # Always show first page
        page_range.append(1)
        
        if page > 3:
            page_range.append(None) # Ellipsis
            
        # Neighbors
        start_p = max(2, page - 1)
        end_p = min(total_pages - 1, page + 1)
        
        for p in range(start_p, end_p + 1):
            page_range.append(p)
            
        if page < total_pages - 2:
            page_range.append(None) # Ellipsis
            
        # Always show last page
        page_range.append(total_pages)

    return render_template('view_all.html', 
                           games=paginated_games, 
                           category=category, 
                           page=page, 
                           total_pages=total_pages,
                           total_games=total_games,
                           page_range=page_range)


@app.route('/api/games')
def api_games():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, image FROM dbo.games")
        games = fetch_all_dicts(cur)
        conn.close()
        
        # Format for frontend
        game_list = []
        for g in games:
            game_list.append({
                "title": g['title'],
                "image": g['image'],
                "link": f"/game/{g['id']}"
            })
            
        return jsonify(game_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/game/<int:game_id>/screenshots')
def get_game_screenshots(game_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT image_url FROM dbo.game_screenshots WHERE game_id = ?', (game_id,))
        rows = cur.fetchall()
        conn.close()
        
        screenshots = [row[0] for row in rows]
        return jsonify(screenshots)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
