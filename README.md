# 121x Bot
A bot for managing a long-lasting TA Discord server.

## Commands
### `/setup assignments`
Arguments: One CSV file with assignments

Setup the server for the semester with TAs, their courses, lead positions, and section assignments.
This should be done once at the beginning of the semester.

The CSV file should have the following header line: `email,courses,leads,sections,teams`.
In situations where there are multiple values in a column (e.g. for multiple sections), values should be separated by a space.

As an example, this is a valid file:
```csv
email,courses,leads,sections,teams
abc,1212,1212,1 2,1212team1
def,1212,,1 3,1212team1
```

### `/setup roles file`
Arguments: One CSV file with existing roles

Setup the SQLite database with existing server roles.
This should ideally only be done once when the bot first joins the server, or if any roles are added manually.

The CSV file should have the following header line: `role,discord_id`.
The value of `role` should match the values under `courses`, `leads`, and `teams`.
Section roles should be formatted `Section <num> - <course>`.
Discord IDs for roles can be found by right clicking the role and selecting "Copy Role ID".
Developer mode may need to be enabled.

As an example, this is a valid file:
```csv
role,discord_id
1212 Lead,123456789
1212,987654321
Section 1 - 1212,135792468
1212team1,246813579
```

### `/setup roles individual`
Arguments: One string of the role name

Create a new Discord role and add it to the database.
This ideally should be done instead of manually adding roles to easily add IDs to the database.
Section roles should be formatted `Section <num> - <course>`.

### `/claim`
Claim roles as a TA.

When the command is run, a modal appears prompting the user for their university email address.
The first part of the email, before the `@`, is used to reference from the database to give the user appropriate roles.

### Planned
- [ ] Proper error handling
- [ ] Improved and expanded modals
- [ ] Office hours role assignments
- [ ] Shift coverage
- [ ] End of semester server resetting


## Running
These instructions assume you have a Discord app configured with as a Guild Install with "applications.commands" and "bot" Scopes and "Administrator" Permissions.
If you do not already have this, follow the instructions here: [Building your first Discord app - Step 1: Creating an app](https://discord.com/developers/docs/quick-start/getting-started#step-1-creating-an-app).

Additionally, uv is used for development and running.
If you do not already have uv installed, instructions can be found here: [Installing uv](https://docs.astral.sh/uv/getting-started/installation/).

1. Set an environment variable called `BOT_TOKEN` with the bot token
2. Rename `config.example.py` to `config.py`
3. Fill in the appropriate values for each variable
4. Run the bot with `uv run main.py`


## Acknowledgements
This project would not be possible without the following projects:
- [Discord](https://discord.com/developers/)
- [hikari](https://github.com/hikari-py/hikari/)
- [hikari-arc](https://github.com/hypergonial/hikari-arc)
- [hikari-miru](https://github.com/hypergonial/hikari-miru)
- [uv](https://github.com/astral-sh/uv)
