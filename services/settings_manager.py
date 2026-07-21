from services.database_service import db


class SettingsManager:
    """
    Bunch of methods to handle the api key: set it, retrieve it from the db, validate it etc.
    """
    _cache = {}

    @classmethod
    def get(cls, key: str, default=None):
        if key in cls._cache:
            return cls._cache[key]
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT api_key FROM settings ")
            row = cursor.fetchone()
        if row:
            cls._cache[key] = row['api_key']
            return cls._cache[key]
        return default

    @classmethod
    def set(cls, key: str, value: str):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM settings")
            cursor.execute("INSERT INTO settings (api_key) VALUES (?)", (value,))
            conn.commit()
        cls._cache[key] = value

    @classmethod
    def get_api_key(cls):
        return cls.get('api_key')

    @classmethod
    def set_api_key(cls, api_key: str):
        cls.set('api_key', api_key)

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()