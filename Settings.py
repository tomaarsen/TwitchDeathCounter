
import logging, json
logger = logging.getLogger(__name__)

class Settings:
    """ Loads data from settings.txt into the bot """
    def __init__(self, bot):
        logger.debug("Loading settings.txt file...")
        try:
            # Try to load the file using json.
            # And pass the data to the Bot class instance if this succeeds.
            with open("settings.txt", "r") as f:
                settings = f.read()
                data = json.loads(settings)
                # Rename Prefix to BossName
                if "Prefix" in data:
                    data["BossName"] = data["Prefix"]
                bot.set_settings(data['Host'],
                                data['Port'],
                                data['Channel'],
                                data['Nickname'],
                                data['Authentication'],
                                data["BossName"],
                                data['Japanese'])
                # Update the settings file to rename "Prefix" to "BossName"
                if "Prefix" in data:
                    Settings.write(bot)
                logger.debug("Settings loaded into Bot.")
        
        except ValueError:
            logger.error("Error in settings file.")
            raise ValueError("Error in settings file.")
        
        except FileNotFoundError:
            # If the file is missing, create a standardised settings.txt file
            # With all parameters required.
            logger.error("Please fix your settings.txt file that was just generated.")
            with open('settings.txt', 'w') as f:
                standard_dict = {
                                    "Host": "irc.chat.twitch.tv",
                                    "Port": 6667,
                                    "Channel": "#<channel>",
                                    "Nickname": "<name>",
                                    "Authentication": "oauth:<auth>",
                                    "BossName": "",
                                    "Japanese": False
                                }
                f.write(json.dumps(standard_dict, indent=4, separators=(',', ': ')))
                raise ValueError("Please fix your settings.txt file that was just generated.")

    @staticmethod
    def write(bot):
        with open('settings.txt', 'w') as f:
            data = {
                "Host": bot.host,
                "Port": bot.port,
                "Channel": bot.chan,
                "Nickname": bot.nick,
                "Authentication": bot.auth,
                "BossName": bot.boss_name,
                "Japanese": bot.japanese
            }
            f.write(json.dumps(data, indent=4, separators=(',', ': ')))

