import config
import hikari
import miru

class EmailModal(miru.Modal, title="University Email"):

    email = miru.TextInput(
        label="Email",
        placeholder=f"Type your @{config.DOMAINS[0]} email",
        required=True,
    )

    async def modal_check(self, ctx: miru.ModalContext) -> bool:
        email = ctx.values[self.email].lower()
        if not any("@" + domain in email for domain in config.DOMAINS):
            await ctx.respond(f"Invalid email. Please ensure that you are including the @{config.DOMAINS[0]}", flags=hikari.MessageFlag.EPHEMERAL)
            return False

        return True

    async def callback(self, ctx: miru.ModalContext) -> None:
        await ctx.respond("Processing role claim...", flags=hikari.MessageFlag.EPHEMERAL)

        # remove the domain from the email
        email = ctx.values[self.email].lower()
        self.email.value = email[:email.index("@")]

        self.stop()
