from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

settings = get_project_settings()

crawler = CrawlerProcess(settings)
crawler.crawl('helmchart')  # 爬虫名
crawler.crawl('cnchart')  # 爬虫名
crawler.start()
crawler.start()
