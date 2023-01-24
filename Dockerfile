FROM python:3.10.2
COPY . /app
WORKDIR /app
COPY arena_tokens.txt arena_tokens.txt
COPY clients.json clients.json
COPY credentials.json credentials.json
COPY token.json token.json
RUN pip install 'discord>=2.0'
RUN pip install python-dotenv
RUN pip install pycrypto
RUN pip install pycryptodome
RUN pip install requests
RUN pip install google-auth
RUN pip install google-auth-oauthlib
RUN pip install google-api-python-client
EXPOSE 5000
CMD ["python3", "main.py"]