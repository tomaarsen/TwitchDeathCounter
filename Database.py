
import sqlite3, logging, random
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, database_dir, streamer):
        self.database_dir = database_dir

        # Remove the # which may be present in the name
        self.streamer = streamer.lower().replace("#", "")
        
        # Add the streamer with 0 deaths initially, unless it already exists.
        logger.debug("Creating Database...")
        self.execute('CREATE TABLE IF NOT EXISTS DeathCounter (streamer varchar(30), counter INTEGER, PRIMARY KEY (streamer));')
        logger.debug("Database created.")
        self.execute('INSERT OR IGNORE INTO DeathCounter(streamer, counter) VALUES (?, 0)', (self.streamer,))
    
    def execute(self, command, data="", fetch=False):
        ''' Execute Commands in SQLite '''
        with sqlite3.connect(self.database_dir) as connection:
            cursor = connection.cursor()
            cursor.execute(command, data)
            if fetch:
                return cursor.fetchall()
            connection.commit()

    def set_death_counter(self, death_counter):
        self.execute("UPDATE DeathCounter SET counter=? WHERE streamer=?", (death_counter, self.streamer))

    def get_deaths(self):
        return self.execute("SELECT counter FROM DeathCounter WHERE streamer=?", (self.streamer,), fetch=True)[0][0]
    
    def increment(self):
        self.execute("UPDATE DeathCounter SET counter=counter+1 WHERE streamer=?", (self.streamer,))