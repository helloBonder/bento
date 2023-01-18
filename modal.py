import os

from discord import Interaction
from discord.ui import Modal, TextInput

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class MyModal(Modal, title='User Form'):

    def __init__(self, guild_id, scopes, range_name):
        super().__init__()

        self.scopes = scopes
        self.range_name = range_name

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

    async def on_submit(self, interaction: Interaction):

        creds = None
        """
        The file token.json stores the user's access and refresh tokens, and is
        created automatically when the authorization flow completes for the first time.
        """
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', scopes=self.scopes)
        """
        If there are no (valid) credentials available, let the user log in.
        """
        if not creds or not creds.valid:
            if creds and creds.refresh_token and creds.expired:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.scopes)
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
                range=self.range_name,
                valueInputOption="RAW",
                body=body
            ).execute()

        except HttpError as err:
            print(err)

        await interaction.response.send_message('Thank you! Your answers have been logged', ephemeral=True)