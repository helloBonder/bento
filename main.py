import discord
from discord.ui import Button, View
from discord import app_commands
from discord.errors import HTTPException

from modals import UserModal, NewQuestionsModal

import base64 
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import os
import json
from dotenv import load_dotenv
import urllib.parse

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.reactions = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def encrypt(raw):
    raw = pad(raw.encode(),16)
    cipher = AES.new(encription_key.encode('utf-8'), AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(raw)).decode('utf-8', 'ignore').replace("b'", "").replace("'", "")


async def create_channels(guild):
    # Create the channels category
    category = await guild.create_category(name='Verification')
    
    # Get the guild owner's role
    owner_role = guild.owner.top_role
    add_questions = await guild.create_text_channel(name="add-questions")

    # Create a permission overwrite for the owner role
    owner_overwrite = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    # Set the overwrite for the owner role on the "add-questions" channel
    await add_questions.set_permissions(owner_role, overwrite=owner_overwrite)

    # Create a permission overwrite for @everyone
    everyone_overwrite = discord.PermissionOverwrite(read_messages=False, send_messages=False)

    # Set the overwrite for @everyone on the "add-questions" channel
    await add_questions.set_permissions(guild.default_role, overwrite=everyone_overwrite)

    # Create text channels and set their categories
    verification = await guild.create_text_channel(name="verification", category=category)
    verified = await guild.create_text_channel(name="verified", category=category)

    # Hide the "verified" channel from users that have just joined the server
    await verified.set_permissions(guild.default_role, read_messages=False)
    
    # create the embed message
    embed = discord.Embed(title='Verify your wallet', description='Please, react with a 👍 emoji to this message in order to get verified and get access to exclusive content.', color=0x00ff00)
    
    # send the embed message
    await client.get_channel(verification.id).send(embed=embed)


async def create_role(guild):
    # Create the role "Verified"
    role = await guild.create_role(
        name="Verified",
        colour=discord.Colour.blue(),
        permissions=discord.Permissions(
            send_messages=True,
            read_message_history=True,
            manage_roles=False,
            manage_channels=False,
            manage_messages=False
        ),
        hoist=True  # Add this parameter to give the role a separate category in the server
        )

    # Get the "verification" and "verified" channels
    verification_channel = discord.utils.get(guild.channels, name="verification")
    verified_channel = discord.utils.get(guild.channels, name="verified")
        
    # Removes the role's access to the "verification" channel and gives access to the "verified" channel
    await verification_channel.set_permissions(role, read_messages=False)
    await verified_channel.set_permissions(role, read_messages=True)


# VERIFICAR SI UN TOKEN ES VALIDO O NO!
async def get_arena_token(guild: discord.Guild):
    # Get the guild owner
    owner = guild.owner

    # Create a DM channel with the guild owner
    dm_channel = await owner.create_dm()

    # Create the embed
    embed = discord.Embed(
        title="Arena Token",
        description="Thanks for inviting me to your server!\nPlease, write your Arena Token below. You can find it [here](http://beta.getarena.xyz/settings)",
        color=discord.Color.blue()
    )

    # Send the message to the DM channel
    message = await dm_channel.send(embed=embed)

    # Wait for a response
    def check(response):
        return response.author == owner and response.channel == message.channel
    response = await client.wait_for('message', check=check)

    # Read the existing tokens from the file
    try:
        with open(ARENA_TOKENS_FILE, 'r', encoding='utf-8') as f:
            existing_tokens = f.read()
    except FileNotFoundError:
        # Create an empty file
        with open(ARENA_TOKENS_FILE, 'w') as f:
            pass
        existing_tokens = ''

    # Check if the guild already has a token
    if str(guild.id) not in existing_tokens:
        # Encrypt the user's response
        encrypted_token = encrypt(response.content)

        # Add the new token to the existing tokens
        new_tokens = f'{guild.id}: {encrypted_token}\n{existing_tokens}'

        # Write the new tokens to the file
        with open(ARENA_TOKENS_FILE, 'w', encoding='utf-8') as f:
            f.write(new_tokens)    

# async def ask_for_token(guild):
    
#     # Get the guild owner
#     owner = guild.owner

#     # Create a DM channel with the guild owner
#     dm_channel = await owner.create_dm()

#     # Create the embed
#     embed = discord.Embed(title="Arena Token", description="Thanks for inviting me to your server!\nPlease, write your Arena Token below. You can find it [here](http://beta.getarena.xyz/settings)", color=discord.Color.blue())

#     # Send the message to the DM channel
#     message = await dm_channel.send(embed=embed)





#     # Verificar el token en el server nuevo!!!!!!





#     # Wait for a response
#     def check(m):
#         return m.author == owner and m.channel == message.channel
#     response = await client.wait_for('message', check=check)

#     # Store the user's response in a file
#     with open('arena_tokens.txt', 'r', encoding='utf-8') as f:
#         arena_tokens = f.read()
    
#     if str(guild.id) not in arena_tokens:
        
#         encrypted_token = encrypt(response.content)
        
#         arena_tokens += f'{guild.id}: {encrypted_token}\n'
    
#     with open('arena_tokens.txt', 'w', encoding='utf-8') as f:
#         f.write(arena_tokens)


def save_server_info(guild):
    
    client_info = {
            'server_id': guild.id,
            'server_name': guild.name,
            "client_name": guild.owner.name,
            "client_id": guild.owner.id
        }

    filename = 'clients.json'
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    try:
        with open(filename, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {'clients': []}

    data['clients'].append(client_info)

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

    # try:
    #     data['clients'].append(client_info)
    # except KeyError:
    #     data['clients'] = [client_info]

    # with open('clients.json', 'w') as f:
    #     f.write(json.dumps(data, indent=2))


@client.event
async def on_ready():
    await client.wait_until_ready()
    await tree.sync()
    print(f'Bot is ready. We have logged in as {client.user}.')


@client.event
async def on_guild_join(guild):

    await create_channels(guild=guild)
    
    await create_role(guild=guild)

    await get_arena_token(guild=guild)

    save_server_info(guild=guild)


@client.event
async def on_message(message):

    try:
        guild = message.guild
        
        if not guild and message.author != client.user:
            embed = discord.Embed(title="Arena Token", description="Thank you!! Your token has been logged.", color=discord.Color.blue())
            await message.channel.send(embed=embed)

    except AttributeError:
        pass


@client.event
async def on_raw_reaction_add(payload):

    guild_id = payload.guild_id
    guild = discord.utils.find(lambda g: g.id == guild_id, client.guilds)
    member = discord.utils.find(lambda m: m.id == payload.user_id, guild.members)
    channel = discord.utils.get(guild.channels, id=payload.channel_id)
    role = discord.utils.get(guild.roles, name="Verified")
    role_id = role.id

    emoji = '👍'
    
    if channel.name == 'verification' and str(payload.emoji) == emoji:  # check the message that reaction is from and if it is the correct emoji
        
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
                  
        # Dentro de la url mando el id y token del webhook para poder recibirlo desde la api de arena y saber a que webhook mandar el mensaje.
        guild_name = urllib.parse.quote(guild.name)
        user_id = member.id
        user_handle = f'{member.name}%23{member.discriminator}'
        arena_token = urllib.parse.quote(arena_token)
        
        url_endpoint = f"{dashboard_endpoint}/discord_connections?"
        url_params = f"user_id={user_id}&user_handle={user_handle}&arena_token={arena_token}&guild_name={guild_name}&guild_id={guild_id}&role_id={role_id}"
        button_url = url_endpoint + url_params

        # Send a message to the user via an embed
        embed = discord.Embed(color=0x00ff00)
        embed.add_field(name="Verification", value="Please, click on the button below to get verified.", inline=True)
        
        button = Button(label='Verify Wallet', style=discord.ButtonStyle.primary, url=button_url, emoji='✔️')

        view = View()
        view.add_item(button)

        # create a direct message channel with the user
        dm_channel = await member.create_dm()

        # send the new embed message
        await member.dm_channel.send(embed=embed, view=view)


@tree.command(name = "data", description = "User Form")
async def user_form(interaction: discord.Interaction):
    gid = interaction.guild_id

    try:
        await interaction.response.send_modal(UserModal(guild_id=gid))
    except HTTPException as err:
        print(err)
        await interaction.response.send_message(content="The server owner didn't setup a Form yet.", ephemeral=True)
    except KeyError as err:
        print(err)
        await interaction.response.send_message(content="The server owner didn't setup a Form yet.", ephemeral=True)
    

@tree.command(name='add_questions', description='Adds questions to modal')
@app_commands.default_permissions()
@app_commands.describe(option="Choose the amount of questions you would like to have in your form")
@app_commands.choices(option=[
        app_commands.Choice(name="1", value=1),
        app_commands.Choice(name="2", value=2),
        app_commands.Choice(name="3", value=3),
        app_commands.Choice(name="4", value=4),
        app_commands.Choice(name="5", value=5)
    ])
async def add_questions(interaction: discord.Interaction, option: app_commands.Choice[int]):

    server_id = interaction.guild_id

    # Checks if the server already has a user form loaded with questions.
    with open('clients.json', 'r') as f:
        data = json.load(f)

    for client in data['clients']:
        if server_id == client['server_id']:
            if 'questions' in client.keys():
                await interaction.response.send_message(content='You already added questions to the user form.', ephemeral=True)
                return
            if 'client_sheet_id' not in client.keys():
                await interaction.response.send_message(content='First load a Google Sheet URL using the command /gsheet.', ephemeral=True)
                return

    if interaction.channel.name != 'add-questions':
        await interaction.response.send_message(content="This is not the correct channel. Go to the 'add-questions' channel.", ephemeral=True)
    else:
        new_questions_modal = NewQuestionsModal(option.value)
        await interaction.response.send_modal(new_questions_modal)


@tree.command(name='gsheet', description='Google Sheet url')
@app_commands.describe(url="Input the Google Sheet URL where you want the answers to be stored.")
@app_commands.default_permissions()
async def ghseet(interaction: discord.Interaction, url: str):

    server_id = interaction.guild_id

    with open('clients.json', 'r') as f:
        data = json.load(f)

    sheet_id = url.split('/')[-2]
    print(sheet_id)

    for client in data['clients']:
        if server_id == client['server_id']:
            client['client_sheet_id'] = sheet_id
    
            with open('clients.json', 'w') as f:
                    f.write(json.dumps(data, indent=2))

            await interaction.response.send_message('The Google Sheet URL has been logged. You can now add questions to your form with the command /add_questions', ephemeral=True)


@tree.command(name='house_keeping', description='Removes everything created by the Bento. Use this command CAREFULLY.')
@app_commands.default_permissions()
async def house_keeping(interaction: discord.Interaction):
    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.response.send_message('I don\'t have the necessary permissions to delete roles.')
        return

    guild = interaction.guild
    guild_id = guild.id

    file_path_tokens = 'arena_tokens.txt'
    file_path_clients = 'clients.json'

    bot_role = discord.utils.get(guild.roles, name='Bento Test')
    print('Bot Role Position', bot_role.position)


    # --------------------------- Remove the user token from the file "arena_tokens.txt" --------------------------- #

    try:
        # read the file into a list of lines
        with open(file_path_tokens, 'r') as file:
            lines = file.readlines()
        # create a new list of lines excluding the line with the guild ID
        new_lines = [line for line in lines if str(guild_id) not in line]
        # write the modified list back to the file
        with open(file_path_tokens, 'w') as file:
            file.writelines(new_lines)
    except FileNotFoundError:
        pass


    # --------------------------- Remove the user from the file "clients.json" --------------------------- #


    try:
        # read the file into a dictionary
        with open(file_path_clients, 'r') as file:
            data = json.load(file)
        # find the index of the dictionary with the given guild ID
        client_index = None
        for i, client in enumerate(data['clients']):
            if client['server_id'] == guild_id:
                client_index = i
                break
        # remove the client from the list if found
        if client_index is not None:
            del data['clients'][client_index]
            print(f"Removed client with server_id {guild_id}")
        else:
            print(f"Client with server_id {guild_id} not found")
        # write the modified dictionary back to the file
        with open(file_path_clients, 'w') as file:
            json.dump(data, file)
    except FileNotFoundError:
        pass


    # --------------------------- Remove the channels, categories and roles created by the bot on_guild_join --------------------------- #


    # Iterate through all channels, categories and roles in the guild
    for channel in guild.channels:
        # Check if the channel is a text channel and if it was created by the bot
        if isinstance(channel, discord.TextChannel) and (channel.name == 'verification' or channel.name == 'verified' or channel.name == 'add-questions'):
            await channel.delete()
    for category in guild.categories:
        if isinstance(category, discord.CategoryChannel) and category.name == 'Verification':
            await category.delete()
    for role in guild.roles:
        print('Manage Roles Permission', guild.me.guild_permissions.manage_roles)
        if isinstance(role, discord.Role) and role.name == 'Verified':
            print('Nombre: ', role.name)
            print('Creado por el bot: ', isinstance(role, discord.Role))
            await role.delete()
    
    await interaction.response.send_message('The channel is clean. You can kick me from the server now.', ephemeral=True)


if __name__ == "__main__":

    load_dotenv()
    ARENA_TOKENS_FILE = "arena_tokens.txt"
    CLIENTS_FILE = "clients.json"
    token = os.getenv('TOKEN')
    encription_key = os.getenv('ENCRYPTION_KEY')
    dashboard_endpoint = os.getenv("ARENA_DASHBOARD_URL")
    
    client.run(token)
