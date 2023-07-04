FROM python:slim

COPY ./rainbondSpider /rainbondSpider

COPY ./scrapy.cfg /scrapy.cfg

WORKDIR /rainbondSpider

RUN pip install -r requirements.txt

CMD scrapy crawl helmchart

