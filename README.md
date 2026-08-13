# 121x Bot
A bot for managing a long-lasting TA Discord server.

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
