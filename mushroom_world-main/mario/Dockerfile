FROM python:3.14-alpine

WORKDIR /mario

RUN apk add --no-cache wget

COPY ./requirements.txt ./
RUN python3 -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "main.py"]
