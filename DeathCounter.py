from TwitchWebsocket import TwitchWebsocket
from num2words import num2words
import json, sqlite3, time, logging, os

class Logging:
    def __init__(self):
        # Either of the two will be empty depending on OS
        prefix = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-1]) + "\\".join(os.path.dirname(os.path.realpath(__file__)).split("\\")[:-1]) 
        prefix += "/Logging/"
        try:
            os.mkdir(prefix)
        except FileExistsError:
            pass
        log_file = prefix + os.path.basename(__file__).split('.')[0] + ".txt"
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            format="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        # Spacer
        logging.info("")

class Database:
    def __init__(self, database_dir, streamer):
        self.database_dir = database_dir
        # Remove the # which may be present in the name
        self.streamer = streamer.lower().replace("#", "")
        # Add the streamer with 0 deaths initially, unless it already exists.
        logging.debug("Creating Database...")
        self.execute('CREATE TABLE IF NOT EXISTS DeathCounter (streamer varchar(30), counter INTEGER, PRIMARY KEY (streamer));')
        logging.debug("Database created.")
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

class Settings:
    def __init__(self, bot):
        logging.debug("Loading settings.txt file...")
        try:
            # Try to load the file using json.
            # And pass the data to the GoogleTranslate class instance if this succeeds.
            with open("settings.txt", "r") as f:
                settings = f.read()
                data = json.loads(settings)
                bot.set_settings(data['Host'],
                                data['Port'],
                                data['Channel'],
                                data['Nickname'],
                                data['Authentication'],
                                data['Japanese'])
                logging.debug("Settings loaded into Bot.")
        except ValueError:
            logging.error("Error in settings file.")
            raise ValueError("Error in settings file.")
        except FileNotFoundError:
            # If the file is missing, create a standardised settings.txt file
            # With all parameters required.
            logging.error("Please fix your settings.txt file that was just generated.")
            with open('settings.txt', 'w') as f:
                standard_dict = {
                                    "Host": "irc.chat.twitch.tv",
                                    "Port": 6667,
                                    "Channel": "#<channel>",
                                    "Nickname": "<name>",
                                    "Authentication": "oauth:<auth>",
                                    "Japanese": False
                                }
                f.write(json.dumps(standard_dict, indent=4, separators=(',', ': ')))
            raise ValueError("Please fix your settings.txt file that was just generated.")

class DeathCounter:
    def __init__(self):
        self.host = None
        self.port = None
        self.chan = None
        self.nick = None
        self.auth = None
        self.japanese = None
        self.prev_increment = 0
        
        # Fill previously initialised variables with data from the settings.txt file
        Settings(self)

        database_dir = "DeathCounter.db"
        self.db = Database(database_dir, self.chan)

        self.ws = TwitchWebsocket(self.host, self.port, self.message_handler, live=True)
        self.ws.login(self.nick, self.auth)
        self.ws.join_channel(self.chan)
        self.ws.add_capability(["tags"])

    def set_settings(self, host, port, chan, nick, auth, japanese):
        self.host = host
        self.port = port
        self.chan = chan
        self.nick = nick
        self.auth = auth
        self.japanese = japanese

    def message_handler(self, m):
        try:
            if m.type == "366":
                logging.info(f"Successfully joined channel: #{m.channel}")

            elif m.type == "NOTICE":
                logging.info(m.message)

            elif m.type == "PRIVMSG":
                # On death counter request, send death counter
                if m.message.startswith(("!deathcount", "!deaths")):
                    self.send_death_counter(changed=False)
                
                # Increment death counter if user is a sub or higher
                elif m.message.startswith("!death") and self.check_user_soft(m):
                    # Only allow one !death per 5 seconds. 
                    # If multiple people type the command within this timeframe, only one death is counted.
                    if time.time() - self.prev_increment > 5:
                        self.db.increment()
                        self.send_death_counter(changed=True)
                        self.prev_increment = time.time()
                
                # Set the death counter to some value if the user is a mod or higher
                elif m.message.startswith("!setdeaths") and self.check_user_hard(m):
                    try:
                        death_count = int(m.message.split(" ")[1])
                    except:
                        return
                    self.db.set_death_counter(death_count)
                    # Send the new death counter with "Is now"
                    self.send_death_counter(changed=True)
                
                elif m.message.startswith("!help"):
                    self.ws.send_message("!deathcount or !deaths to get Death Counter. !death to increment death counter. (sub+) !setdeaths 5 to set death counter to 5 (mod+)")

        except Exception as e:
            logging.error(e)
    
    def check_user_hard(self, m):
        return "moderator" in m.tags["badges"] or "broadcaster" in m.tags["badges"] or "cubiedev" == m.user.lower()
    
    def check_user_soft(self, m):
        return self.check_user_hard(m) or "subscriber" in m.tags["badges"]

    def send_death_counter(self, changed):
        count = self.db.get_deaths()
        if self.japanese:
            message = f"Death Counter{' is now' if changed else ''}: {num2words(count, lang='ja', to='cardinal')} ({count})"
        else:
            message = f"Death Counter{' is now' if changed else ''}: {count}"
        logging.info(f"Death Counter{' is now' if changed else ''}: {count}")
        self.ws.send_message(message)

if __name__ == "__main__":
    Logging()
    DeathCounter()
