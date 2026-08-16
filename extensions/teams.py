import sqlite3
import config
import hikari
import miru
import arc

plugin = arc.GatewayPlugin("teams")
teams = plugin.include_slash_group("teams", "Configure team")

conn: sqlite3.Connection | None = None
curr: sqlite3.Cursor | None = None

@teams.include
@arc.slash_subcommand("emoji", "Change team emoji. There can only be one emoji. The word 'Team' will still prefix the emoji")
async def emoji(
    ctx: arc.GatewayContext,
    emoji: arc.Option[hikari.Emoji, arc.EmojiParams("A single emoji for your team icon")],
    role_selection: arc.Option[int, arc.IntParams("If you have multiple teams, which do you want to update. 0 representing the highest team role")] = 0,
) -> None:

    if conn is None or curr is None:
        raise RuntimeError("Database did not properly connect during loading")

    # TODO: check for overlapping emojis
    # two teams should not have the same emoji

    # get the team id and the team name in the db
    # the name will be used for channel renaming
    team_ids, teams = get_team_roles(ctx)
    team_id, team = team_ids[role_selection], teams[role_selection]

    # rename role
    await plugin.client.rest.edit_role(ctx.guild_id, team_id, name=f"Team {emoji}")

    # rename channel
    values = { "channel": f"%{team}%" }
    curr.execute(f"SELECT discord_id FROM {config.CHANNEL_TABLE} WHERE channel LIKE :channel", values)
    channel_id = int(curr.fetchone()[0])
    await plugin.client.rest.edit_channel(channel_id, name=f"team-{emoji}")

    await ctx.respond(f"Team emoji has been changed to {emoji}")


@teams.include
@arc.slash_subcommand("color", "Change team colour")
async def color(
    ctx: arc.GatewayContext,
    colour: arc.Option[hikari.Color, arc.ColorParams("Primary colour for team. Provide a hex code (e.g. 0x005035 or #A49665)")],
    # gradient support was added with pr #2749, but that has yet to be fully released
    # colour_grad: arc.Option[hikari.Color | None, arc.ColorParams("Secondary colour for team. Include for gradient")] = None,
    role_selection: arc.Option[int, arc.IntParams("If you have multiple teams, which do you want to update. 0 representing the highest role")] = 0,
) -> None:

    if conn is None or curr is None:
        raise RuntimeError("Database did not properly connect during loading")

    # get the team id and the team name in the db
    team_ids, _ = get_team_roles(ctx)
    team_id = team_ids[role_selection]

    # change the role colour
    await plugin.client.rest.edit_role(ctx.guild_id, team_id, colour=colour)

    await ctx.respond("Team colour has been changed")


def get_team_roles(ctx: arc.GatewayContext) -> tuple[list[int], list[str]]:

    if conn is None or curr is None:
        raise RuntimeError("Database did not properly connect during loading")

    if ctx.member is None:
        raise RuntimeError("Called outside of server")

    values = { "discord_id": ctx.user.id }
    curr.execute(f"SELECT email FROM {config.TA_TABLE} WHERE discord_id = :discord_id", values)
    email = curr.fetchone()
    if email is None:
        raise RuntimeError("User email not found")

    values = { "email": email[0] }
    curr.execute(f"SELECT team FROM {config.ASSIGNMENT_TABLE} WHERE email = :email", values)
    teams = curr.fetchone()
    if teams is None:
        raise RuntimeError("User email not found")
    teams = teams[0].split()

    team_ids: list[int] = []
    for team in teams:
        values = { "role": team }
        curr.execute(f"SELECT discord_id FROM {config.ROLE_TABLE} WHERE role = :role", values)
        team_ids.append(int(curr.fetchone()[0]))
    team_ids, teams = (list(t) for t in zip(*sorted(zip(team_ids, teams), reverse=True)))

    return team_ids, teams


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    global conn, curr
    conn = sqlite3.connect(config.DATABASE_PATH)
    curr = conn.cursor()

    client.add_plugin(plugin)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    if curr is not None: curr.close()
    if conn is not None: conn.close()
    client.remove_plugin(plugin)
