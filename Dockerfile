FROM python:3.7-alpine
COPY . /app
WORKDIR /app
#COPY requirements.txt requirements.txt // COPY FILES
RUN pip install discord
RUN pip install google-auth
EXPOSE 5000
CMD ["python", "main.py"]