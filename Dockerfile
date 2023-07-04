FROM python:slim

COPY ./rainbondSpider /

WORKDIR /rainbondSpider

RUN pip install -r requirements.txt

CMD scrapy crawl helmchart


