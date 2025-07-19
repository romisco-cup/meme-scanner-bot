import sqlite3

def get_db_connection():
    conn = sqlite3.connect('memecoins.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    conn.execute('DROP TABLE IF EXISTS tokens')  # Use DROP TABLE for easy rerunning during development
    conn.execute('''
        CREATE TABLE tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            name TEXT NOT NULL,
            symbol TEXT NOT NULL,
            address TEXT NOT NULL UNIQUE,
            price REAL,
            volume REAL,
            liquidity REAL,
            holders INTEGER,
            age_hours INTEGER,
            dexscreener_url TEXT,
            rugcheck_url TEXT,
            bubblemap_url TEXT,
            tweetscout_url TEXT,
            telegram_alert_sent BOOLEAN DEFAULT FALSE,
            twitter_trending BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    conn.close()

def log_token(token_data):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO tokens (name, symbol, address, price, volume, liquidity, holders, age_hours, dexscreener_url, rugcheck_url, bubblemap_url, tweetscout_url, twitter_trending)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            token_data['name'],
            token_data['symbol'],
            token_data['address'],
            token_data['price'],
            token_data['volume'],
            token_data['liquidity'],
            token_data['holders'],
            token_data['age_hours'],
            token_data['dexscreener_url'],
            token_data['rugcheck_url'],
            token_data['bubblemap_url'],
            token_data['tweetscout_url'],
            token_data['twitter_trending']
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        # Token with this address already exists
        pass
    finally:
        conn.close()

def update_token_alert_status(token_address):
    conn = get_db_connection()
    conn.execute('UPDATE tokens SET telegram_alert_sent = TRUE WHERE address = ?', (token_address,))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_table()
    print("Database table 'tokens' created successfully.")
