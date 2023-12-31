FROM python:slim

WORKDIR / .

COPY ./rainbondSpider ./rainbondSpider

COPY ./scrapy.cfg ./scrapy.cfg

COPY ./main.py ./main.py

RUN pip3 install -r ./rainbondSpider/requirements.txt

CMD python3 main.py
