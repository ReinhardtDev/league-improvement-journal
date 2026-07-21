import sqlite3

class DatabaseService:
    def __init__(self, db_path="lol_journal.db"):
        self.db_path = db_path
        self.init_db()
        print("database initialized")

    def get_connection(self):
        """Helper to get a connection where rows can be accessed like dictionaries."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Creates tables if they don't already exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS grinds
                           (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               title TEXT NOT NULL,
                               summoner_name TEXT NOT NULL,
                               start_date INTEGER NOT NULL,
                               start_rank TEXT NOT NULL,
                               current_rank TEXT NOT NULL,
                               puuid TEXT NOT NULL,
                               platform TEXT NOT NULL
                           )
                           ''')

            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS matches
                           (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               grind_id INTEGER NOT NULL,
                               date INTEGER NOT NULL,
                               result TEXT NOT NULL,
                               lp_gain INTEGER NOT NULL,
                               champion TEXT NOT NULL,
                               opponent TEXT NOT NULL,
                               cs INTEGER NOT NULL,
                               match_length TEXT NOT NULL,
                               kills INTEGER NOT NULL,
                               deaths INTEGER NOT NULL,
                               assists INTEGER NOT NULL,
                               notes TEXT,
                               FOREIGN KEY ( grind_id ) REFERENCES grinds ( id ) ON DELETE CASCADE
                               )
                           ''')

            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS champion_pools
                           (
                               id       INTEGER PRIMARY KEY AUTOINCREMENT,
                               grind_id INTEGER NOT NULL UNIQUE,
                               FOREIGN KEY (grind_id) REFERENCES grinds (id) ON DELETE CASCADE
                           )
                           ''')

            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS pool_champions
                           (
                               id           INTEGER PRIMARY KEY AUTOINCREMENT,
                               pool_id      INTEGER NOT NULL,
                               champion     TEXT NOT NULL,
                               notes        TEXT,
                               FOREIGN KEY (pool_id) REFERENCES champion_pools (id) ON DELETE CASCADE
                           )
                           ''')

            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS match_ups
                           (
                               id           INTEGER PRIMARY KEY AUTOINCREMENT,
                               pool_champion_id  INTEGER NOT NULL,
                               opponent     TEXT NOT NULL,
                               todo         TEXT DEFAULT '""',
                               not_todo     TEXT DEFAULT '""',
                               notes        TEXT DEFAULT '""',
                               FOREIGN KEY (pool_champion_id) REFERENCES pool_champions (id) ON DELETE CASCADE
                           )
                           ''')

            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS goals
                           (
                               id               INTEGER PRIMARY KEY AUTOINCREMENT,
                               grind_id         INTEGER NOT NULL,
                               goal_type        TEXT    NOT NULL,
                               description      TEXT DEFAULT '""',
                               reached          INTEGER DEFAULT 0,
                               target_lp        INTEGER,
                               FOREIGN KEY (grind_id) REFERENCES grinds (id) ON DELETE CASCADE
                           );
                           ''')

            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_one_rank_goal ON goals(grind_id) WHERE goal_type = 'rank';")

            cursor.execute("CREATE TABLE IF NOT EXISTS settings ( api_key TEXT NOT NULL PRIMARY KEY );")

            conn.commit()

db = DatabaseService()