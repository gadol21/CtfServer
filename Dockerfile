from alpine
RUN apk add --update python py-pip mongodb
RUN mkdir /www
COPY . /www/
WORKDIR /www

# Install dependencies
RUN pip install -r requirements.txt
RUN mkdir /data
RUN mkdir /data/db
CMD mongod --fork --syslog

# Run!
CMD python create_db.py
CMD python main.py

EXPOSE 80