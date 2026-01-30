FROM python:3.14-alpine

WORKDIR /toad

COPY ./requirements.txt ./
RUN python3 -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY utils/crontab_toad /etc/cron.d/crontab_toad
RUN chmod 0644 /etc/cron.d/crontab_toad
RUN crontab /etc/cron.d/crontab_toad

CMD ["crond", "-f", "-l", "8", "-L", "/dev/stdout"]
