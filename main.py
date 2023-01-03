import discord
from discord.ui import Button, View

import os
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

client = discord.Client(intents=intents)


async def create_role(guild):
    role = await guild.create_role(
        name="Verified",
        colour=discord.Colour.blue(),
        permissions=discord.Permissions(
            read_messages=True,
            send_messages=True,
            read_message_history=True,
            manage_roles=False,
            manage_channels=True,  # Add this permission to give the role the ability to manage channels
            manage_messages=False
        ),
        hoist=True  # Add this parameter to give the role a separate category in the server
        )

    print(f"Created role {role} in guild {guild}")

    # Create a category for the role
    category = await guild.create_category(name=role.name)

    # Get the "verification" and "verified" channels
    verification_channel = discord.utils.get(guild.channels, name="verification")
    print(verification_channel)
    verified_channel = discord.utils.get(guild.channels, name="verified")
    print(verified_channel)
    
    # Move the "moderators" channel into the role's category
    await verified_channel.edit(category=category)
    
    # Remove the role's access to the "verification" channel
    await verification_channel.set_permissions(role, read_messages=False)

    # Hide the "moderators" channel from users that have just joined the server
    await verified_channel.set_permissions(guild.default_role, read_messages=False)


async def ask_for_token(guild):
    
    # Get the guild owner
    owner = guild.owner

    # Create a DM channel with the guild owner
    dm_channel = await owner.create_dm()
    
    # Send the message to the DM channel
    await dm_channel.send('Please, write your Arena Token below. You can find it in "Settings".')
    
    # Wait for a response from the user
    response = await client.wait_for('message', check=lambda message: message.author == owner)
    
    # Store the user's response in a file
    with open('arena_tokens.txt', 'r') as f:
        arena_tokens = f.read()
    
    arena_tokens += f'{guild.id}: {response.content}\n'
    
    with open('arena_tokens.txt', 'w') as f:
        f.write(arena_tokens)

    print(arena_tokens)


@client.event
async def on_ready():
    await client.wait_until_ready()
    print(f'Bot is ready. We have logged in as {client.user}.')
    

@client.event
async def on_guild_join(guild):
    
    await create_role(guild=guild)

    await ask_for_token(guild=guild)


@client.event
async def on_message(message):

    try:
        # If the message was sent in the channel 'verification' and not by the bot itself
        if message.channel.name == "verification" and message.author != client.user:
            
            # Si el mensaje lo manda el webhook
            if message.webhook_id:

                guild = message.guild

                # Cuando el webhook manda el mensaje indicando que se realizo la verificacion, el bot agrega el rol correspondiente al usuario y borro el webhook.
                channel_webhooks = await message.channel.webhooks()
                for webhook in channel_webhooks:
                    if webhook.name == 'Arena Webhook':
                        await webhook.delete()
                
                print(f'Message content: {message.content}')

                for word in message.content.split():
                    try:
                        member_id = int(word)
                    except ValueError:
                        pass

                print(f'User ID: {member_id}')
                member = guild.get_member(member_id)

                verified_role = discord.utils.get(guild.roles, name='Verified')
                await member.add_roles(verified_role)

                print(f'We have added the role "{verified_role}" to the member {member}')

            # Si el mensaje lo manda el usuario
            else:

                guild = message.guild

                # Open the file in read mode
                with open('arena_tokens.txt', 'r') as f:
                    # Read the contents of the file into a string
                    data = f.read()

                    # Split the data into a list of lines
                    lines = data.split('\n')

                    # Find the line that starts with the key you're looking for
                    guild_id = guild.id
                    for line in lines:
                        if line.startswith(str(guild_id)):
                            # Split the line on the colon and space to extract the value
                            arena_token = line.split(': ')[1]
                
                # Crea un webhook temporal con nombre Arena Webhook. El id y token del webhook lo pone discord
                hook = await message.channel.create_webhook(name='Arena Webhook', reason="It's a temporal webhook only for verification purposes. It will be deleted after the verification.")
                
                # Send a message to the user via an embed
                embed = discord.Embed(title="Title", color=0x00ff00)
                embed.add_field(name="Message", value="This is the message", inline=True)

                # Dentro de la url mando el id y token del webhook para poder recibirlo desde bento-api y saber a que webhook mandar el mensaje.
                button_1 = Button(label='Verify', style=discord.ButtonStyle.primary, url=f'http://localhost:3000/discord_connections?user_id={message.author.id}&user_handle={message.author.name}&arena_token={arena_token}&hook_id={hook.id}&hook_token={hook.token}', emoji='✔️')

                view = View()
                view.add_item(button_1)

                await message.channel.send(embed=embed, view=view)
    
    except AttributeError:
        pass

if __name__ == "__main__":
    load_dotenv()
    token = os.getenv('TOKEN')
    client.run(token)
