import os
import json

from discord import Interaction
from discord.ui import Modal, TextInput

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class UserModal(Modal):

    def __init__(self, guild_id, scopes, range_name):
        super().__init__(title='User Form')

        self.scopes = scopes
        self.range_name = range_name

        # Read questions from a file
        with open('clients.json', 'r') as f:
            data = json.load(f)

        for company in data['clients']:
            if guild_id == company['server_id']:
                self.spreadsheet_id = company['client_sheet_id']
                self.answers = []
                self.questions = []
                for i in range(len(company['questions'])):

                    #  Step 2) defining the inputs
                    self.answer = TextInput(
                        label=company['questions'][i][0], required=company['questions'][i][1])
                    self.answers.append(self.answer)
                    self.questions.append(self.answer.label)

                    # Step 3) adding the inputs
                    self.add_item(self.answer)

    async def on_submit(self, interaction: Interaction):

        creds = None

        creds_json = {
            "installed": {
                "client_id": "376305420688-ocjmlh3k69jiumrsj33ganh300rp4ef6.apps.googleusercontent.com",
                "project_id": "discord-bot-363820",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": "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",
                "redirect_uris": [
                    "http://localhost"
                ]
            }
        }

        with open('clients.json', 'r') as f:
            data = json.load(f)

        for client in data['clients']:
            if interaction.guild_id == client['server_id']:

                try:
                    creds = Credentials.from_authorized_user_info(
                        info=client['creds_json'], scopes=self.scopes)

                except KeyError:
                    pass

                if not creds or not creds.valid:
                    if creds and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_config(
                            creds_json, self.scopes)
                        creds = flow.run_local_server(port=0)
                        client['creds_json'] = json.loads(creds.to_json())

                    print(client['creds_json'])

        print(data)

        with open('clients.json', 'w') as f:
            f.write(json.dumps(data, indent=2))

        try:
            service = build('sheets', 'v4', credentials=creds)
            user_discord_id = interaction.id

            """
            I check if the first row is written
            If it is, get the values for the next available row
            """
            response = service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id, range="A1").execute()
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
                range=self.range_name,
                valueInputOption="RAW",
                body=body
            ).execute()

        except HttpError as err:
            print(err)

        await interaction.response.send_message('Thank you! Your answers have been logged', ephemeral=True)


class NewQuestionsModal(Modal):
    def __init__(self, amnt_of_questions):
        super().__init__(title='Add Questions to your form!')
        self.i = 0
        self.questions = []

        while self.i < amnt_of_questions:

            q = TextInput(label='Add question', max_length=50)
            self.questions.append(q)
            self.add_item(q)
            self.i += 1

    async def on_submit(self, interaction: Interaction):

        # Store the questions in a file
        with open('clients.json', 'r') as f:
            data = json.load(f)

        user_questions = []

        for question in self.questions:
            user_questions.append([question.value, "False"])

        client_info = {
            'server_id': interaction.guild.id,
            'server_name': interaction.guild.name,
            "client_name": interaction.guild.owner.name,
            "client_id": interaction.guild.owner.id,
            'questions':
                user_questions
        }

        try:
            data['clients'].append(client_info)
        except KeyError:
            data['clients'] = [client_info]

        with open('clients.json', 'w') as f:
            f.write(json.dumps(data, indent=2))

        await interaction.response.send_message('Thank you! The User Form questions have been logged', ephemeral=True)
