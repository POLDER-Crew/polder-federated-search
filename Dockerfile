FROM python:3.9

COPY ./requirements.txt .
COPY ./package.json .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY . .

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && \
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list && \
    apt-get update && \
    apt-get install -qq -y yarn
RUN yarn install
RUN yarn docker

EXPOSE 8000
CMD ["gunicorn", "--conf", "gunicorn_conf.py", "--bind", "0.0.0.0:8000", "main:app"]
