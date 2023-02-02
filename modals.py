import json

from discord import Interaction
from discord.ui import Modal, TextInput

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class UserModal(Modal):

    def __init__(self, guild_id):
        super().__init__(title='User Form', timeout=None)

        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.range_name = 'Hoja 1!A1'

        # Read questions from a file
        with open('clients.json', 'r') as f:
            data = json.load(f)

        for company in data['clients']:
            if guild_id == company['server_id']:
                self.spreadsheet_id = company['client_sheet_id']
                self.answers = []
                self.questions = []
                for i in range(len(company['questions'])):

                    # Defining the inputs
                    self.answer = TextInput(
                        label=company['questions'][i][0], required=company['questions'][i][1])
                    self.answers.append(self.answer)
                    self.questions.append(self.answer.label)

                    # Adding the inputs
                    self.add_item(self.answer)

    async def on_submit(self, interaction: Interaction):

        with open('clients.json', 'r') as f:
            data = json.load(f)

        for client in data['clients']:
            if interaction.guild_id == client['server_id']:
                creds = Credentials.from_authorized_user_info(
                    info=client['creds'], scopes=self.scopes)

                if not creds.valid:
                    if creds.refresh_token and creds.expired:
                        creds.refresh(Request())

                    client['creds'] = json.loads(creds.to_json())

        with open('clients.json', 'w') as f:
            f.write(json.dumps(data, indent=2))

        try:
            service = build('sheets', 'v4', credentials=creds)
            user_discord_id = interaction.id

            values = [
                [f'{interaction.user}']
            ]
            for answer in self.answers:
                values[0].append(f'{answer.value}')

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

        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.range_name = 'Hoja 1!A1'

        self.creds_json = {
            "installed": {
                "client_id": "376305420688-ocjmlh3k69jiumrsj33ganh300rp4ef6.apps.googleusercontent.com",
                "project_id": "discord-bot-363820",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": "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",
                "redirect_uris": ["http://localhost"]
            }
        }

        self.i = 0
        self.questions = []

        while self.i < amnt_of_questions:

            q = TextInput(label='Add question', max_length=50)
            self.questions.append(q)
            self.add_item(q)
            self.i += 1

    async def on_submit(self, interaction: Interaction):

        creds = None

        # Store the questions in a file
        with open('clients.json', 'r') as f:
            data = json.load(f)

        server_id = interaction.guild_id
        user_questions = []

        for question in self.questions:
            user_questions.append([question.value, "False"])

        for client in data['clients']:
            if server_id == client['server_id']:
                client['questions'] = user_questions
                self.spreadsheet_id = client['client_sheet_id']

                if 'creds' in client.keys():

                    creds = Credentials.from_authorized_user_info(info=client['creds'], scopes=self.scopes)
                    """
                    If there are no (valid) credentials available, let the user log in.
                    """

                if not creds or not creds.valid:
                    # No existen las credenciales o existen, pero no son validas.
                    if creds and creds.refresh_token:
                        # Las credenciales existen y existe el refresh_token, pero no son validas, entonces las actualiza
                        creds.refresh(Request())
                    else:
                        # Crea las credenciales por primera vez.
                        flow = InstalledAppFlow.from_client_config(self.creds_json, self.scopes)
                        creds = flow.run_local_server(port=0)
                    break

        client['creds'] = json.loads(creds.to_json())

        with open('clients.json', 'w') as f:
            f.write(json.dumps(data, indent=2))

        try:
            service = build('sheets', 'v4', credentials=creds)
            user_discord_id = interaction.id

            values = [
                ['Discord ID']
            ]
            for question in self.questions:
                values[0].append(f'{question}')

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

        await interaction.response.send_message("Thank you! The User Form questions have been logged.", ephemeral=True)
