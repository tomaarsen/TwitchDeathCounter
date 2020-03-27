from TwitchWebsocket import TwitchWebsocket
from num2words import num2words
import logging, time

from Log import Log
Log(__file__)

from Settings import Settings
from Database import Database

class DeathCounter:
    def __init__(self):
        self.host = None
        self.port = None
        self.chan = None
        self.nick = None
        self.auth = None
        self.boss_name = None
        self.japanese = None
        self.prev_increment = 0
        
        # Fill previously initialised variables with data from the settings.txt file
        Settings(self)

        database_dir = "DeathCounter.db"
        self.db = Database(database_dir, self.chan)

        self.ws = TwitchWebsocket(host=self.host, 
                                  port=self.port,
                                  chan=self.chan,
                                  nick=self.nick,
                                  auth=self.auth,
                                  callback=self.message_handler,
                                  capability="tags",
                                  live=True)
        self.ws.start_bot()

    def set_settings(self, host, port, chan, nick, auth, boss_name, japanese):
        self.host = host
        self.port = port
        self.chan = chan
        self.nick = nick
        self.auth = auth
        self.boss_name = boss_name
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
                elif m.message == "!death" and self.check_user_soft(m):
                    # Only allow one !death per 30 seconds. 
                    # If multiple people type the command within this timeframe, only one death is counted.
                    if time.time() - self.prev_increment > 30:
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
                
                # Change the boss name if the user is a mod or higher
                elif m.message.startswith("!setfight") and self.check_user_hard(m):
                    split_message = m.message.split(" ")
                    if len(split_message) > 1:
                        logging.info(f"Death counter before switching fights is {self.db.get_deaths()}.")
                        self.boss_name = " ".join(split_message[1:]).strip()
                        # Set the death counter to 0 for the new fight
                        self.db.set_death_counter(0)
                        # Send the new death counter with "Is now"
                        self.send_death_counter(changed=True)
                        logging.info(f"Switched fight to \"{self.boss_name}\".")
                    else:
                        self.ws.send_message("Expected format is `!setfight boss name` where `boss name` is the name of the boss.")

                elif m.message.startswith("!help"):
                    self.ws.send_message("!deathcount or !deaths to get Death Counter. !death to increment death counter. (sub+) !setdeaths 5 to set death counter to 5 (mod+)")

        except Exception as e:
            logging.error(e)
    
    def check_user_hard(self, m):
        return "moderator" in m.tags["badges"] or "broadcaster" in m.tags["badges"] or "cubiedev" == m.user.lower()
    
    def check_user_soft(self, m):
        return self.check_user_hard(m) or "subscriber" in m.tags["badges"] or "vip" in m.tags["badges"]

    def send_death_counter(self, changed):
        count = self.db.get_deaths()
        if self.japanese:
            message = f"{self.boss_name} Death Counter{' is now' if changed else ''}: {num2words(count, lang='ja', to='cardinal')} ({count})"
        else:
            message = f"{self.boss_name} Death Counter{' is now' if changed else ''}: {count}"
        logging.info(message)
        self.ws.send_message(message)

if __name__ == "__main__":
    DeathCounter()
