from backend.obj.library_obj import Library
import sqlite3

import logging
log = logging.getLogger(__name__)

class DB_Handler:

    def write_to_sqlite(l: Library, db_path: str) -> None:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # media table. clearerr owns this entirely, drop and rebuild
        cursor.execute("DROP TABLE IF EXISTS media")
        cursor.execute("""
            CREATE TABLE media (
                rating_key TEXT PRIMARY KEY,
                tmdb_key TEXT,
                title TEXT,
                media_type TEXT,
                deletion_score REAL,
                poster_url TEXT
            )
        """)

        cursor.execute("DROP TABLE IF EXISTS seasons")
        cursor.execute("""
            CREATE TABLE seasons (
                rating_key TEXT PRIMARY KEY,
                show_rating_key TEXT,
                tmdb_key TEXT,
                title TEXT,
                FOREIGN KEY (show_rating_key) REFERENCES media(rating_key)
            )
        """)

        # exempt table. web app owns this, just has to exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exempt (
                rating_key TEXT PRIMARY KEY,
                exempted_by TEXT,
                exempted_at INTEGER
            )
        """)

        # removal table. web app also owns this one
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS removal_queue (
                rating_key TEXT PRIMARY KEY,
                queued_by TEXT,
                queued_at INTEGER
            )
        """)
        
        # write all media
        for movie in l.movies:
            cursor.execute("""
                INSERT INTO media VALUES (?, ?, ?, ?, ?, ?)
            """, (movie.rating_key, movie.ids.get('tmdb'), movie.title, 'movie', movie.deletion_score,
                    movie.poster_url))

        for show in l.shows:
            cursor.execute("""
                INSERT INTO media VALUES (?, ?, ?, ?, ?, ?)
            """, (show.rating_key, show.ids.get('tmdb'), show.title, 'show', show.deletion_score,
                    show.poster_url))

            for season in show.seasons:
                cursor.execute("""
                    INSERT INTO seasons VALUES (?, ?, ?, ?)
                """, (season.rating_key, show.rating_key, season.ids.get('tmdb'), season.title))

        # clean up exempt and removal entries for media no longer in library
        cursor.execute("""
            DELETE FROM exempt WHERE rating_key NOT IN 
            (SELECT rating_key FROM media)
        """)
        cursor.execute("""
            DELETE FROM removal_queue WHERE rating_key NOT IN 
            (SELECT rating_key FROM media)
        """)

        conn.commit()
        conn.close()
        log.info(f"Library written to SQLite: {len(l.movies)} movies, {len(l.shows)} shows")