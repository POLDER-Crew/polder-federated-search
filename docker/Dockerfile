FROM python:3.8-slim-buster
WORKDIR /usr/src/app

COPY ../requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["flask", "run"]
