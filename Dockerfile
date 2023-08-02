FROM python:slim

COPY ./rainbondSpider /rainbondSpider

WORKDIR / .

COPY ./scrapy.cfg ./scrapy.cfg

COPY ./main.py ./main.py

RUN pip install -r ./rainbondSpider/requirements.txt

CMD python3 main.py

