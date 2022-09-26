FROM python:3.9

COPY ./requirements.txt .
COPY ./package.json .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -qq -y gcc nodejs npm
RUN npm i -g corepack
RUN yarn install
RUN yarn docker

EXPOSE 8000
CMD ["gunicorn", "--conf", "gunicorn_conf.py", "--bind", "0.0.0.0:8000", "main:app"]
