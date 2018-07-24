FROM alpine

RUN apk update && apk upgrade && \
    apk add --no-cache python3 && \
    pip3 install --upgrade pip setuptools && \
    pip3 install paho-mqtt adafruit-bmp

COPY BMP180.py /usr/bin/BMP180.py
RUN chmod +x /usr/bin/BMP180.py

CMD /usr/bin/BMP180.py