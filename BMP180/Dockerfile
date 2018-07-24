FROM ubuntu:rolling

RUN apt-get update && \
	apt-get install --no-install-recommends -y python3-dev python3-distutils python3-smbus i2c-tools build-essential curl ca-certificates && \
	curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
	python3 get-pip.py && \
	pip3 install paho-mqtt adafruit-bmp && \
	apt-get purge --autoremove -y python3-dev build-essential curl ca-certificates && \
	rm -rf /var/lib/apt/lists/*

COPY BMP180.py /usr/bin/BMP180.py
RUN chmod +x /usr/bin/BMP180.py

CMD /usr/bin/BMP180.py