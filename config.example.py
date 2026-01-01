from dotenv import load_dotenv
import os

load_dotenv()

# discord bot api key
TOKEN: str | None = os.getenv("BOT_TOKEN")
if TOKEN == None:
    raise NameError("BOT_TOKEN environment variable not defined")

# sqlite database information
DATABASE_PATH: str = ""
ASSIGNMENT_TABLE: str = ""
TA_TABLE: str = ""
ROLE_TABLE: str = ""

# university email domains, do not include @
# put primary email domain at index 0
DOMAINS = [""]
