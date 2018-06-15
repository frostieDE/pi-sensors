FROM alpine

RUN apk update && apk upgrade && \
    apk add --no-cache --virtual .build-deps git gcc python3-dev musl-dev && \
    apk add --no-cache python3 && \
    pip3 install --upgrade pip setuptools && \
    git clone https://github.com/adafruit/Adafruit_Python_DHT.git && \
    cd Adafruit_Python_DHT && \
    python3 setup.py install --force-pi2 && \
    pip install influxdb && \
    apk del .build-deps

COPY DHT22.py /usr/bin/DHT22.py
RUN chmod +x /usr/bin/DHT22.py

ENTRYPOINT /usr/bin/DHT22.py