FROM python:3.9

COPY ./requirements.txt .
COPY ./package.json .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY . .

# get the PPA that has an actual node version from this decade
RUN curl -sL https://deb.nodesource.com/setup_18.x | bash -

RUN apt-get update
RUN apt-get install -qqy nodejs
RUN corepack enable \
    && yarn install \
    && yarn docker \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 8000
CMD ["gunicorn", "--conf", "gunicorn_conf.py", "--bind", "0.0.0.0:8000", "main:app"]
