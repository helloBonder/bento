FROM python:3.10.4-slim-buster
RUN pip install --upgrade pip

COPY . /app

WORKDIR /app

COPY requirements.txt requirements.txt
COPY arena_tokens.txt arena_tokens.txt
COPY clients.json clients.json

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python3", "main.py"]