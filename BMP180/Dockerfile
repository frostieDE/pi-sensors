FROM alpine

RUN apk update && apk upgrade && \
    apk add --no-cache --virtual .build-deps git gcc python3-dev musl-dev && \
    apk add --no-cache python3 && \
    pip3 install --upgrade pip setuptools && \
    pip3 install paho-mqtt adafruit-bmp && \
    apk del .build-deps

COPY BMP180.py /usr/bin/BMP180.py
RUN chmod +x /usr/bin/BMP180.py

CMD /usr/bin/BMP180.py