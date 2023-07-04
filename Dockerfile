FROM python:slim

COPY ./rainbondSpider /

WORKDIR /rainbondSpider

RUN pip install scrapy

CMD scrapy crawl helmchart


