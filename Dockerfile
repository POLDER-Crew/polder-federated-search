FROM python:3.9

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get install yarn
RUN yarn install
RUN yarn build

COPY . .
EXPOSE 8000
CMD ["gunicorn", "--conf", "gunicorn_conf.py", "--bind", "0.0.0.0:8000", "main:app"]
