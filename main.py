import discord
from discord.ui import Button, View, Modal, TextInput
from discord import app_commands

import base64 
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import os
import json
from dotenv import load_dotenv
import urllib.parse

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.reactions = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


class MyModal(Modal, title='User Form'):

    def __init__(self, guild_id):
        super().__init__()

        # Predefined questions
        self.questions = []
        self.answers = [
            TextInput(label='What is your name?', placeholder='First and Last name', required=False),
            TextInput(label='What is your email?', placeholder='name@email.com', required=False),
            TextInput(label='What is your twitter handle?', placeholder='@twitter_handle', required=False)
        ]

        for answer in self.answers:
            self.questions.append(answer.label)
            self.add_item(answer)

        self.spreadsheet_id = '1fxV8yGONBjmykh8oLRGbt_D4_XGCwfpz7sU9O82tJmg'


        # # Read questions from a file
        # with open('clients.json', 'r') as f:
        #     data = json.load(f)

        # for company in data['clients']:
        #     if guild_id == company['server_id']:
        #         self.spreadsheet_id = company['client_sheet_id']
        #         self.answers = []
        #         self.questions = []
        #         for i in range(len(company['questions'])):
                    
        #             #  Step 2) defining the inputs
        #             self.answer = TextInput(label=company['questions'][i][0], required=company['questions'][i][1])
        #             self.answers.append(self.answer)
        #             self.questions.append(self.answer.label)
                    
        #             # Step 3) adding the inputs
        #             self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):

        creds = None
        """
        The file token.json stores the user's access and refresh tokens, and is
        created automatically when the authorization flow completes for the first time.
        """
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        """
        If there are no (valid) credentials available, let the user log in.
        """
        if not creds or not creds.valid:
            if creds and creds.refresh_token and creds.expired:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            """
            Save the credentials for the next run
            """
            with open('token.json', 'w') as f:
                f.write(creds.to_json())

        try:
            service = build('sheets', 'v4', credentials=creds)
            user_discord_id = interaction.id

            """
            I check if the first row is written
            If it is, get the values for the next available row
            """
            response = service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range="A1").execute()
            try:
                assert response['values']
                values = [
                    [f'{interaction.user}']
                ]
                for answer in self.answers:
                    values[0].append(f'{answer.value}')

            # If it isn't, get the values of the first two rows
            except KeyError:
                values = [
                    ['Discord ID'],
                    [f'{interaction.user}']
                ]
                for question in self.questions:
                    values[0].append(f'{question}')
                for answer in self.answers:
                    values[1].append(f'{answer.value}')

            body = {
                'values': values
            }

            # Write the values in the spreadsheet
            service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=RANGE_NAME,
                valueInputOption="RAW",
                body=body
            ).execute()

        except HttpError as err:
            print(err)

        await interaction.response.send_message('Thank you! Your answers have been logged', ephemeral=True)


def encrypt(raw):
    raw = pad(raw.encode(),16)
    cipher = AES.new(encription_key.encode('utf-8'), AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(raw))


async def create_verification_channels(guild):
    # Create the channels category
    category = await guild.create_category(name='Verification')

    # Create text channels and set their categories
    verification = await guild.create_text_channel(name="verification", category=category)
    verified = await guild.create_text_channel(name="verified", category=category)
    
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

    # Hide the "verified" channel from users that have just joined the server
    await verified_channel.set_permissions(guild.default_role, read_messages=False)


# VERIFICAR SI UN TOKEN ES VALIDO O NO!
async def ask_for_token(guild):
    
    # Get the guild owner
    owner = guild.owner

    # Create a DM channel with the guild owner
    dm_channel = await owner.create_dm()

    # Create the embed
    embed = discord.Embed(title="Arena Token", description="Thanks for inviting me to your server!\nPlease, write your Arena Token below. You can find it in 'Settings'.", color=discord.Color.blue())

    # Send the message to the DM channel
    message = await dm_channel.send(embed=embed)
        
    # Wait for a response
    def check(m):
        return m.author == owner and m.channel == message.channel
    response = await client.wait_for('message', check=check)
    
    # Store the user's response in a file
    with open('arena_tokens.txt', 'r', encoding='utf-8') as f:
        arena_tokens = f.read()
    
    if str(guild.id) not in arena_tokens:
        
        encrypted_token = encrypt(response.content).decode('utf-8', 'ignore').replace("b'", "").replace("'", "")
        
        arena_tokens += f'{guild.id}: {encrypted_token}\n'
    
    with open('arena_tokens.txt', 'w', encoding='utf-8') as f:
        f.write(arena_tokens)


@client.event
async def on_ready():
    await client.wait_until_ready()
    await tree.sync()
    print(f'Bot is ready. We have logged in as {client.user}.')


@client.event
async def on_guild_join(guild):

    await create_verification_channels(guild=guild)
    
    await create_role(guild=guild)

    await ask_for_token(guild=guild)


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


@tree.command(name = "data", description = "User Form") #Add the guild ids in which the slash command will appear. If it should be in all, remove the argument, but note that it will take some time (up to an hour) to register the command if it's for all guilds.
async def user_form(interaction: discord.Interaction):
    gid = interaction.guild_id
    await interaction.response.send_modal(MyModal(guild_id=gid))


@tree.command(name='add_questions', description='Adds questions to modal')
async def add_questions(interaction: discord.Interaction):
    if interaction.user == interaction.guild.owner:
        # Ask the server owner for the questions
        await interaction.response.send_message("Please enter the questions one by one. Type 'done' when you are finished.", ephemeral=True)
        questions = []
        while True:
            question = await client.wait_for('message', check=lambda message: message.author == interaction.user)
            if question.content.lower() == "done":
                break
            questions.append(question.content)
        
        # Store the questions in a database or file
        print(questions)
        await interaction.edit_original_response(content="Questions have been added!")
    else:
        await interaction.response.send_message(content="You do not have permission to use this command.", ephemeral=True)


if __name__ == "__main__":

    load_dotenv()
    token = os.getenv('TOKEN')
    encription_key = os.getenv('ENCRYPTION_KEY')
    dashboard_endpoint = os.getenv("ARENA_DASHBOARD_ENDPOINT")

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # The ID and range of the spreadsheet.
    RANGE_NAME = 'Hoja 1!A1'

    client.run(token)
