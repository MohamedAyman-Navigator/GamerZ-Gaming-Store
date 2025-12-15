# GamerZ - Ultimate Game Store Platform

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)
![SQL Server](https://img.shields.io/badge/Database-SQL%20Server-red)
![Gemini AI](https://img.shields.io/badge/AI-Google%20Gemini-purple)

**GamerZ** is a modern, full-featured e-commerce web application designed for gamers. It offers a seamless platform to browse, purchase, and manage video games, DLCs, and special editions. Powered by **Flask** and **SQL Server**, it integrates **Google's Gemini AI** to provide an intelligent shopping assistant that knows the store's inventory in real-time.

---

## Features

*   **Comprehensive Storefront**: Browse a vast catalog of Games, DLCs, and Special Editions.
*   **AI-Powered Assistant**: Integrated Chatbot (powered by Google Gemini) that answers questions about game specs, prices, and stock availability.
*   **User Accounts**: Secure registration and login system with profile management and avatar uploads.
*   **Shopping Cart & Checkout**: Full cart functionality with simulated checkout and digital key generation.
*   **Order History**: Users can view their purchased games and access their unique activation keys.
*   **Admin Dashboard**: Powerful admin interface to add, edit, or delete games and view sales statistics.
    *   **New**: Light/Dark mode toggle for the admin dashboard.
    *   **New**: Enhanced charts and data visualization.
*   **Analytics**: Real-time dashboard showing sales data, genre distribution, and top-rated games.
*   **Hardware Section**: Dedicated pages for hardware showcases (e.g., RTX 5090).

---

## Tech Stack

*   **Backend**: Python (Flask Framework)
*   **Database**: Microsoft SQL Server (via `pyodbc`)
*   **Frontend**: HTML5, CSS3, JavaScript (Jinja2 Templates)
*   **AI Integration**: Google Generative AI (Gemini 2.0 Flash)
*   **Authentication**: Session-based auth with password hashing (`werkzeug.security`)

---

## Getting Started

### Prerequisites

*   Python 3.8 or higher
*   Microsoft SQL Server (Local or Remote instance)
*   ODBC Driver 18 for SQL Server
*   Google Gemini API Key

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/MohamedAyman-Navigator/GamerZ-Gaming-Store.git
    cd GamerZ-Gaming-Store
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Database Setup**
    *   Ensure SQL Server is running.
    *   Create a database named `Gamerz__db`.
    *   Update the `DB_CONFIG` dictionary in `app.py` with your server credentials:
        ```python
        DB_CONFIG = {
            "DRIVER": "{ODBC Driver 18 for SQL Server}",
            "SERVER": "localhost",
            "DATABASE": "Gamerz__db",
            "UID": "your_username",
            "PWD": "your_password",
        }
        ```
    *   *Note: Ensure your database schema matches the application's expected tables (`users`, `games`, `orders`, etc.).*
    *   **Initialize the Database**: Run the provided `schema.sql` script in SQL Server Management Studio (SSMS) or via `sqlcmd` to create the database and tables.

5.  **Seed the Database**
    *   Populate your store with real game data from Steam by running the import script:
        ```bash
        python import_steam.py
        ```

6.  **Configure AI API**
    *   Open `app.py` and replace the placeholder with your API key:
        ```python
        GEMINI_API_KEY = "YOUR_GOOGLE_GEMINI_API_KEY"
        ```

### Running the Application

```bash
python app.py
```
The application will start at `http://127.0.0.1:5000`.

---

## Project Structure

```
GamerZ/
├── app.py              # Main application entry point and routes
├── import_steam.py     # Utility script to import game data
├── requirements.txt    # Python dependencies
├── static/             # Static assets (CSS, JS, Images, Uploads)
├── templates/          # HTML Templates (Jinja2)
├── old_version/        # Deprecated files
└── README.md           # Project documentation
```

---

## Admin Access

To access the Admin Dashboard:
1.  Register a new user account.
2.  In the database, update the user's `id` to `1` (or modify the `is_admin()` check in `app.py`).
3.  Navigate to `/admin` after logging in.

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## License

This project is open-source and available under the [MIT License](LICENSE).
