import discord
from discord.ui import Button, View

import os
from dotenv import load_dotenv


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    await client.wait_until_ready()
    print(f'Bot is ready. We have logged in as {client.user}.')


# @client.event
# async def on_member_join(member):
#     # Send a message to the user asking for their name
#     await member.send('Hello and welcome to the server! Could you please tell me your name?')


@client.event
async def on_message(message):

    # If the message was sent in the channel 'verificación' and not by the bot itself
    if message.channel.name == "verificacion" and message.author != client.user:

        # Send a message to the user asking for their name via an embed
        embed = discord.Embed(title="Title", color=0x00ff00)
        embed.add_field(name="Mensaje", value="Este es el mensaje", inline=True)

        button_1 = Button(label='Button 1', style=discord.ButtonStyle.primary, url='http://example.com', emoji='✔️')
        button_2 = Button(label='Button 2', style=discord.ButtonStyle.secondary, url='http://example.com', emoji='👺')

        view = View()
        view.add_item(button_1)
        view.add_item(button_2)

        await message.channel.send(embed=embed, view=view)


load_dotenv()
token = os.getenv('TOKEN')
client.run(token)
