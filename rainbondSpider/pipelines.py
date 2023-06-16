from io import BytesIO
import os
import pymysql
import scrapy
from scrapy import Request
from scrapy.pipelines.files import FilesPipeline
import requests
import json

#
# RAINSTORE_URL
#
# MARKET_id
#
# CHART_REPO_URL
#
# HOST
#
# PORT
#
# USER_NAME
#
# PASS_WORD
#
# DATA_BASE




from scrapy.utils.misc import md5sum


class FileDownloadPipeline(FilesPipeline):

  def get_media_requests(self, item, info):
    if item["file_urls"]:
      for url in item["file_urls"]:
        tgz = url.split("/")[-1]
        name = tgz.split("-")[0]
        temp_version = tgz.split("-")[1]
        version = temp_version.rstrip(".tgz")
        mete = {
          "tgz": tgz,
          "name": name,
          "version": version,
        }
        yield Request(url, meta=mete)

  def file_downloaded(self, response, request, info, *, item=None):
    # path = self.file_path(request, response=response, info=info, item=item)
    buf = BytesIO(response.body)
    checksum = md5sum(buf)
    buf.seek(0)
    # upload to chart repo
    url = "http://8080.grc81b1e.qf85jobv.17f4cc.grapps.cn/api/charts"
    headers = {"Content-Type": "application/octet-stream"}
    chart_resp = requests.post(url, headers=headers, data=buf).json()
    if chart_resp.get("saved"):
      #上传应用信息
      try:
        post_db_pipelin = PostDbPipelin()
        post_db_pipelin.open_spider()
        post_db_pipelin.process_item(item)
        post_db_pipelin.close_spider()
      except Exception as e:
        print("上传应用商店异常:", e)
      # 更新数据库
      try:
        db_pipelin = DbPipelin()
        db_pipelin.open_spider()
        db_pipelin.process_item(item)
        db_pipelin.close_spider()
      except Exception as e:
        print("数据库操作异常:", e)
    return checksum

  def sql_handle(self):

    return



# 写入数据库操作
class DbPipelin():
  # 初始化
  def __int__(self):
    self.conn = None
    self.cursor = None
  # 开启
  def open_spider(self):
    self.conn = pymysql.connect(host="localhost",
                                    port=3306,
                                    user='root',
                                    password='gr123465!',
                                    database='helmDetail',
                                    charset="utf8mb4"
                                    )
    self.cursor = self.conn.cursor()
  # 关闭
  def close_spider(self):
    self.conn.commit()
    self.conn.close()
  # 进行中
  def process_item(self, item):
    package_id = item.get("package_id", '')
    name = item.get("name", '')
    version = item.get("version", '')
    description = item.get("description", '')
    readme = item.get("readme", '')
    logo_image_id = item.get("logo_image_id", '')

    # 检查 package_id 是否存在
    query = 'SELECT version FROM chartDetail WHERE package_id = %s'
    self.cursor.execute(query, (package_id,))
    result = self.cursor.fetchone()

    if result:
      db_version = result[0]
      if version != db_version:
        # 版本号不一致，执行更新操作
        query = 'UPDATE chartDetail SET version = %s, description = %s, readme = %s, logo_image_id = %s WHERE package_id = %s'
        self.cursor.execute(query, (version, description, readme, logo_image_id, package_id))
    else:
      # package_id 不存在，执行插入操作
      query = 'INSERT INTO chartDetail (package_id, name, version, description, readme, logo_image_id) VALUES (%s, %s, %s, %s, %s, %s)'
      self.cursor.execute(query, (package_id, name, version, description, readme, logo_image_id))

    return item

class PostDbPipelin():
    def __init__(self):
      self.conn = None
      self.cursor = None

    def open_spider(self):
      self.conn = pymysql.connect(
        host="localhost",
        port=3306,
        user='root',
        password='gr123465!',
        database='helmDetail',
        charset="utf8mb4"
      )
      self.cursor = self.conn.cursor()

    def close_spider(self):
      self.conn.commit()
      self.conn.close()

    def process_item(self, item):
      package_id = item.get("package_id", 0)
      version = item.get("version", '')

      if not self.check_package_exists(package_id):
        # 发送新增接口
        self.send_new_item(item)
      else:
        # 检查版本号是否一致
        if self.check_version_consistency(package_id, version):
          return item  # 版本一致，不做任何处理

        # 执行更新操作
        self.update_item(package_id, item)

      return item

    def check_package_exists(self, package_id):
      # 查询 package_id 是否存在
      self.cursor.execute('SELECT package_id FROM chartDetail WHERE package_id = %s', (package_id,))
      result = self.cursor.fetchone()
      return bool(result)

    def check_version_consistency(self, package_id, version):
      # 检查版本号是否一致
      self.cursor.execute('SELECT version FROM chartDetail WHERE package_id = %s', (package_id,))
      result = self.cursor.fetchone()
      return result[0] == version if result else False

    def send_new_item(self, item):
      #参数设置
      url = "http://4000.grc580e8.qf85jobv.17f4cc.grapps.cn/app-server/markets/b85ca319b29347748ffea620ce1cee6e/helm/app"
      data = {
        'package_id': item['package_id'],
        'version': item['version'],
        'name': item['name'],
        'description': item['description'],
        'readme': item['readme'],
        'logo_image_id': item['logo_image_id'],
      }
      headers = {'content-type': 'application/json'}
      requests.post(url, data=json.dumps(data), headers=headers)


    def update_item(self, package_id, item):
      url = "http://4000.grc580e8.qf85jobv.17f4cc.grapps.cn/app-server/markets/b85ca319b29347748ffea620ce1cee6e/helm/app"
      data = {
        'package_id': item['package_id'],
        'version': item['version'],
        'name': item['name'],
        'description': item['description'],
        'readme': item['readme'],
        'logo_image_id': item['logo_image_id'],
      }
      headers = {'content-type': 'application/json'}
      requests.put(url, data=json.dumps(data), headers=headers)

      # if response.status_code == 200:
      # else:




