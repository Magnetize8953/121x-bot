import config
import hikari
import miru
import arc
import os

def main():

    if config.TOKEN == None:
        raise NameError("BOT_TOKEN environment variable not defined")

    bot = hikari.GatewayBot(token=config.TOKEN)
    arc_client = arc.GatewayClient(bot)
    miru_client = miru.Client.from_arc(arc_client)

    arc_client.load_extensions_from("extensions")

    bot.run()

if __name__ == "__main__":
    main()
