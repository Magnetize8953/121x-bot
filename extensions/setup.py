from components.email import EmailModal
import sqlite3
import config
import hikari
import miru
import arc

plugin = arc.GatewayPlugin("setup")
setup = plugin.include_slash_group("setup", "Setup the server for the semester")
roles = setup.include_subgroup("roles", "Setup server roles for the semester")
channels = setup.include_subgroup("channels", "Setup server channels for the semester")

conn: sqlite3.Connection | None = None
curr: sqlite3.Cursor | None = None

@setup.include
@arc.with_hook(arc.has_permissions(hikari.Permissions.MANAGE_GUILD))
@arc.slash_subcommand("assignments", "Setup TA assignments for claiming")
async def assignments(
    ctx: arc.GatewayContext,
    csv: arc.Option[hikari.Attachment, arc.AttachmentParams("Text file following 'email,courses,leads,sections,teams' format with heading")],
) -> None:

    if conn is None or curr is None:
        raise RuntimeError("Database did not properly connect during loading")

    file = await csv.read()

    # reading in as bytes, so convert to chars, then a string, then a list of strings
    text = "".join([chr(letter) for letter in file]).strip().split("\n")
    if text[0] != "email,courses,leads,sections,teams":
        raise RuntimeError("Incorrect file heading. Please ensure the first line of the file is 'email,courses,leads,sections,teams' (without quotes)")

    # populate database
    # 1 is the header
    for line in text[1:]:
        email, courses, leads, sections, teams = line.strip().split(",")
        values = {
            "email": email,
            "courses": courses,
            "leads": leads if leads != "" else None,
            "sections": sections,
            "teams": teams,
        }
        curr.execute(f"INSERT INTO {config.ASSIGNMENT_TABLE} VALUES(:email, :courses, :leads, :sections, :teams)", values)
        conn.commit()

    await ctx.respond("TA assignments saved. Individual TAs need to claim their roles using `/claim`")


@roles.include
@arc.with_hook(arc.has_permissions(hikari.Permissions.MANAGE_GUILD))
@arc.slash_subcommand("create", "Create a new role and add it to the database for later assignment")
async def create(
    ctx: arc.GatewayContext,
    name: arc.Option[str, arc.StrParams("Name of the role to create")],
) -> None:

    if conn is None or curr is None:
        raise RuntimeError("Database did not properly connect during loading")

    role = await plugin.client.rest.create_role(ctx.guild_id, name=name)
    # TODO: role positioning?
    # currently, the role new gets added as the last
    # rest function reposition_role() does this, it's just a matter of modularising the ordering
    # await plugin.client.rest.reposition_roles(ctx.guild_id, { <int>: role.id })

    values = {
        "role": name,
        "discord_id": role.id,
    }
    curr.execute(f"INSERT INTO {config.ROLE_TABLE} VALUES(:role, :discord_id)", values)
    conn.commit()

    await ctx.respond("Role created and saved to database")


@roles.include
@arc.with_hook(arc.has_permissions(hikari.Permissions.MANAGE_GUILD))
@arc.slash_subcommand("individual", "Add an individual existing role to database")
async def individual(
    ctx: arc.GatewayContext,
    role: arc.Option[hikari.Role, arc.RoleParams("Role to add")],
    name: arc.Option[str, arc.StrParams("Name to use in database. Defaults to role name with spaces replaced with underscores (_)")] = "",
) -> None:

    if conn is None or curr is None:
        raise RuntimeError("Database did not properly connect during loading")

    if name == "":
        name = role.name.replace(" ", "_")

    values = {
        "role": name,
        "discord_id": role.id,
    }
    curr.execute(f"INSERT INTO {config.ROLE_TABLE} VALUES(:role, :discord_id)", values)
    conn.commit()

    await ctx.respond("Role created and saved to database")


@roles.include
@arc.with_hook(arc.has_permissions(hikari.Permissions.MANAGE_GUILD))
@arc.slash_subcommand("file", "Setup roles for the semester")
async def file(
    ctx: arc.GatewayContext,
    csv: arc.Option[hikari.Attachment, arc.AttachmentParams("Text file following 'role,discord_id' format with heading")],
) -> None:

    if conn is None or curr is None:
        raise RuntimeError("Database did not properly connect during loading")

    file = await csv.read()

    # reading in as bytes, so convert to chars, then a string, then a list of strings
    text = "".join([chr(letter) for letter in file]).strip().split("\n")
    if text[0] != "role,discord_id":
        raise RuntimeError("Incorrect file heading. Please ensure the first line of the file is 'role,discord_id' (without quotes)")

    # populate database
    # 1 is the header
    for line in text[1:]:
        role, discord_id = line.strip().split(",")
        values = {
            "role": role,
            "discord_id": discord_id,
        }
        curr.execute(f"INSERT INTO {config.ROLE_TABLE} VALUES(:role, :discord_id)", values)
        conn.commit()

    await ctx.respond("Roles saved.")


@channels.include
@arc.with_hook(arc.has_permissions(hikari.Permissions.MANAGE_GUILD))
@arc.slash_subcommand("course", "Setup course channels for the semester")
async def course(
    ctx: arc.GatewayContext,
    course: arc.Option[str, arc.StrParams("Course the channels will be for")],
    category: arc.Option[hikari.GuildCategory, arc.ChannelParams("Category available for all course TAs")],
    lead_category: arc.Option[hikari.GuildCategory, arc.ChannelParams("Category available for only course lead TAs")],
) -> None:

    if conn is None or curr is None:
        raise RuntimeError("Database did not properly connect during loading")

    values = { "course": course }
    curr.execute(f"SELECT discord_id FROM {config.ROLE_TABLE} WHERE role = :course", values)
    regular_ta_role = int(curr.fetchone()[0])
    curr.execute(f"SELECT discord_id FROM {config.ROLE_TABLE} WHERE role = CONCAT(:course, ' Lead')", values)
    lead_ta_role = int(curr.fetchone()[0])

    guild = ctx.get_guild()
    if guild is None:
        raise RuntimeError("Error getting guild")

    # NOTE: the permission_overwrites argument does not allow for disabling @everyone from viewing
    # the solution used here dedpends on the category already being set to disallow @everyone from viewing channels within it
    # each channel created within the category syncs this permission by default

    # regular TA channels
    reg_general = await guild.create_text_channel(f"{course}-general", category=category)
    await reg_general.edit_overwrite(
        target=regular_ta_role,
        target_type=hikari.PermissionOverwriteType.ROLE,
        allow=hikari.Permissions.VIEW_CHANNEL,
    )
    reg_shift_cov = await guild.create_text_channel(f"{course}-shift-coverage", category=category)
    await reg_shift_cov.edit_overwrite(
        target=regular_ta_role,
        target_type=hikari.PermissionOverwriteType.ROLE,
        allow=hikari.Permissions.VIEW_CHANNEL,
    )

    # lead TA channels
    lead_general = await guild.create_text_channel(f"{course}-lead-general", category=lead_category)
    await lead_general.edit_overwrite(
        target=lead_ta_role,
        target_type=hikari.PermissionOverwriteType.ROLE,
        allow=hikari.Permissions.VIEW_CHANNEL,
    )
    lead_shift_cov = await guild.create_text_channel(f"{course}-lead-shift-coverage", category=lead_category)
    await lead_shift_cov.edit_overwrite(
        target=lead_ta_role,
        target_type=hikari.PermissionOverwriteType.ROLE,
        allow=hikari.Permissions.VIEW_CHANNEL,
    )

    await ctx.respond("Course channels created")


@channels.include
@arc.with_hook(arc.has_permissions(hikari.Permissions.MANAGE_GUILD))
@arc.slash_subcommand("team", "Setup team channels for the semester")
async def team(
    ctx: arc.GatewayContext,
    category: arc.Option[hikari.GuildCategory, arc.ChannelParams("Teams category")],
    team_prefix: arc.Option[str, arc.StrParams("Common prefix for team role names")] = "Team ",
) -> None:

    if conn is None or curr is None:
        raise RuntimeError("Database did not properly connect during loading")

    curr.execute(f"SELECT DISTINCT team FROM {config.ASSIGNMENT_TABLE} WHERE team <> ''")
    teams = [name[0] for name in curr.fetchall()]
    if len(teams) == 0:
        raise RuntimeError("No teams found")

    guild = ctx.get_guild()
    if guild is None:
        raise RuntimeError("Error getting guild")

    # NOTE: the permission_overwrites argument does not allow for disabling @everyone from viewing
    # the solution used here dedpends on the category already being set to disallow @everyone from viewing channels within it
    # each channel created within the category syncs this permission by default

    for team in teams:
        values = { "team": team }
        curr.execute(f"SELECT discord_id FROM {config.ROLE_TABLE} WHERE role = :team", values)
        role_id = int(curr.fetchone()[0])

        role = guild.get_role(role_id)
        if role is None:
            label = team
        else:
            label = role.name.replace(team_prefix, "")

        team_channel = await guild.create_text_channel(f"team-{label}", category=category)
        await team_channel.edit_overwrite(
            target=role_id,
            target_type=hikari.PermissionOverwriteType.ROLE,
            allow=hikari.Permissions.VIEW_CHANNEL,
        )

    await ctx.respond("Team channels created")


# TODO: reset server by archiving channels, renaming, repositioning, and hiding roles
@plugin.include
@arc.with_hook(arc.has_permissions(hikari.Permissions.MANAGE_GUILD))
@arc.slash_command("reset", "Reset server for new semester. Database tables are dropped and roles are removed from users")
async def reset(
    ctx: arc.GatewayContext,
    client: miru.Client = arc.inject(),
) -> None:
    raise NotImplementedError


@plugin.include
@arc.slash_command("claim", "Claim your roles")
async def claim(
    ctx: arc.GatewayContext,
    client: miru.Client = arc.inject(),
) -> None:

    if conn is None or curr is None:
        raise RuntimeError("Database did not properly connect during loading")

    # TODO: improve this
    # currently very simple and basic with the sole intent of not having the email in the visible slash command
    # i'm pretty sure it isn't optimal
    modal = EmailModal()
    builder = modal.build_response(client)

    await ctx.respond_with_builder(builder)
    client.start_modal(modal)

    await modal.wait()
    email = modal.email.value
    values = { "email": email.lower() }

    curr.execute(f"SELECT * FROM {config.ASSIGNMENT_TABLE} WHERE email = :email", values)
    res = curr.fetchone()
    if res is None:
        await ctx.respond("Email was not found. Double check the email you entered, or contact the course administrator(s)", flags=hikari.MessageFlag.EPHEMERAL)
        return

    _, courses, leads, sections, teams = res
    courses = courses.split()
    leads = leads.split() if leads is not None else None
    sections = sections.split()
    teams = teams.split()

    course_ids = []
    for course in courses:
        values = { "role": course }
        curr.execute(f"SELECT discord_id FROM {config.ROLE_TABLE} WHERE role = :role", values)
        course_ids += curr.fetchall()

    lead_ids = []
    if leads:
        for lead in leads:
            values = { "course": lead }
            curr.execute(f"SELECT discord_id FROM {config.ROLE_TABLE} WHERE role = CONCAT(:course, ' Lead')", values)
            lead_ids += curr.fetchall()

    # TODO: distinguish between courses
    section_ids = []
    for course in courses:
        for section in sections:
            values = {
                "course": course,
                "section": section,
            }
            curr.execute(f"SELECT discord_id FROM {config.ROLE_TABLE} WHERE role = CONCAT('Section ', :section, ' - ', :course)", values)
            section_ids += curr.fetchall()

    # TODO: distinguish between courses
    team_ids = []
    for team in teams:
        values = { "team": team }
        curr.execute(f"SELECT discord_id FROM {config.ROLE_TABLE} WHERE role = :team", values)
        team_ids += curr.fetchall()

    role_ids = [int(id) for tup in course_ids + lead_ids + section_ids + team_ids for id in tup]
    for id in role_ids:
        await ctx.member.add_role(id)

    values = {
        "email": email,
        "discord_id": ctx.user.id,
    }
    curr.execute(f"INSERT INTO {config.TA_TABLE} VALUES(:email, :discord_id)", values)
    conn.commit()

    await ctx.respond(
        f"Added roles to {ctx.user.mention}: {[ctx.get_guild().get_role(role).name for role in role_ids]}"
        f"\nAdded {ctx.user.mention} to TAs table in database. This table will be dropped at the end of the semester"
    )


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    global conn, curr
    conn = sqlite3.connect(config.DATABASE_PATH)
    curr = conn.cursor()
    curr.executescript(f"""
        CREATE TABLE IF NOT EXISTS {config.ASSIGNMENT_TABLE} (
            email    TEXT PRIMARY KEY,
            courses  TEXT NOT NULL,
            leads    TEXT,
            sections TEXT NOT NULL,
            team     TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS {config.TA_TABLE} (
            email      TEXT PRIMARY KEY,
            discord_id TEXT NOT NULL,
            FOREIGN KEY(email) REFERENCES {config.ASSIGNMENT_TABLE}(email)
        );
        CREATE TABLE IF NOT EXISTS {config.ROLE_TABLE} (
            role       TEXT PRIMARY KEY,
            discord_id TEXT NOT NULL
        );
    """)
    conn.commit()

    client.add_plugin(plugin)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    if curr is not None: curr.close()
    if conn is not None: conn.close()
    client.remove_plugin(plugin)
