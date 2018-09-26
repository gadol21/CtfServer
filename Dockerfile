from alpine as build
RUN apk add --update python py-pip mongodb
RUN mkdir /www
COPY requirements.txt /www/requirements.txt
WORKDIR /www

# Install dependencies
RUN pip install -r requirements.txt
RUN mkdir /data
RUN mkdir /data/db

COPY . /www/
# Run!
CMD mongod --fork --syslog --dbpath /data/db
CMD python create_db.py
ENTRYPOINT ["python", "main.py"]

EXPOSE 80