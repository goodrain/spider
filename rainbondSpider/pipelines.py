from io import BytesIO
import pymysql
from scrapy import Request
from scrapy.pipelines.files import FilesPipeline
from scrapy.pipelines.images import ImagesPipeline
import requests
import json

from scrapy.utils.misc import md5sum

class PostDbPipelin():
  def __init__(self):
    self.conn = None
    self.cursor = None

  def open_spider(self, spider):
    self.conn = pymysql.connect(
      host="localhost",
      port=3306,
      user='root',
      password='gr123465!',
      database='helmDetail',
      charset="utf8mb4"
    )
    self.cursor = self.conn.cursor()

  def close_spider(self, spider):
    self.conn.commit()
    self.conn.close()

  def process_item(self, item, spider):
    package_id = item.get("package_id", 0)
    version = item.get("version", '')
    version_exists = self.check_version_exists(package_id, version)
    name = item.get("name", '')
    if version in version_exists:
      # 版本已存在，执行更新操作
      self.update_item(item)
    else:
      # 版本不存在，执行新增操作

      self.insert_item(item)
    return item

  def check_version_exists(self, package_id, version):

    # 查询 package_id 对应的所有版本号

    self.cursor.execute('SELECT version FROM chartDetail WHERE package_id = %s', (package_id,))
    versions = [v[0] for v in self.cursor.fetchall()]
    return versions

  def insert_item(self, item):

    # 执行新增操作

    # 参数设置

    url = "https://hub.grapps.cn/app-server/markets/859a51f9bb3b48b5bfd222e3bef56425/helm/app"
    data = {
      'package_id': item['package_id'],
      'version': item['version'],
      'name': item['name'],
      'description': item['description'],
      'readme': item['readme'],
      'logo_image_id': item['logo_image_id'],
      'category': item['category'],
    }
    headers = {'content-type': 'application/json'}
    res = requests.post(url, data=json.dumps(data), headers=headers)

  def update_item(self, item):

    # 参数设置

    url = "https://hub.grapps.cn/app-server/markets/859a51f9bb3b48b5bfd222e3bef56425/helm/app"
    data = {
      'package_id': item['package_id'],
      'version': item['version'],
      'name': item['name'],
      'description': item['description'],
      'readme': item['readme'],
      'logo_image_id': item['logo_image_id'],
      'category': item['category'],
    }
    headers = {'content-type': 'application/json'}
    res = requests.put(url, data=json.dumps(data), headers=headers)

# 写入数据库操作

class DbPipelin():
  def __init__(self):
    self.conn = None
    self.cursor = None

  def open_spider(self, spider):
    self.conn = pymysql.connect(
      host="localhost",
      port=3306,
      user='root',
      password='gr123465!',
      database='helmDetail',
      charset="utf8mb4"
    )
    self.cursor = self.conn.cursor()

  def close_spider(self, spider):
    self.conn.commit()
    self.conn.close()

  def process_item(self, item, spider):
    package_id = item.get("package_id", '')
    name = item.get("name", '')
    version = item.get("version", '')
    description = item.get("description", '')
    readme = item.get("readme", '')
    logo_image_id = item.get("logo_image_id", '')
    category = item.get('category', 0),
    if not self.check_package_exists(package_id):

      # package_id 不存在，执行插入操作

      query = 'INSERT INTO chartDetail (package_id, name, version, description, readme, logo_image_id, category) VALUES (%s, %s, %s, %s, %s, %s, %s)'
      self.cursor.execute(query, (package_id, name, version, description, readme, logo_image_id, category))
    else:

      # 获取相同 package_id 下的所有 version

      versions = self.get_versions_by_package_id(package_id)
      if version not in versions:

        # 版本号不在相同 package_id 下的所有 version 中，执行插入操作

        query = 'INSERT INTO chartDetail (package_id, name, version, description, readme, logo_image_id, category) VALUES (%s, %s, %s, %s, %s, %s, %s)'
        self.cursor.execute(query, (package_id, name, version, description, readme, logo_image_id, category))
      else:

        # 版本号在相同 package_id 下的所有 version 中，执行更新操作

        query = 'UPDATE chartDetail SET description = %s, readme = %s, logo_image_id = %s, category = %s WHERE package_id = %s and version = %s'
        self.cursor.execute(query, (description, readme, logo_image_id, category, package_id, version))

    return item

  def check_package_exists(self, package_id):

    # 查询 package_id 是否存在

    query = 'SELECT package_id FROM chartDetail WHERE package_id = %s'
    self.cursor.execute(query, (package_id,))
    result = self.cursor.fetchone()
    return bool(result)

  def get_versions_by_package_id(self, package_id):

    # 获取相同 package_id 下的所有 version

    query = 'SELECT version FROM chartDetail WHERE package_id = %s'
    self.cursor.execute(query, (package_id,))
    versions = [v[0] for v in self.cursor.fetchall()]
    return versions

#
# class FileDownloadPipeline(FilesPipeline):
#   def file_path(self, request, response=None, info=None):
#     tgz = request.meta["tgz"]
#     file_name = tgz
#     return r'/rainchart/%s' % (file_name)
#   def get_media_requests(self, item, info):
#     if item["file_urls"]:
#       for url in item["file_urls"]:
#         tgz = url.split("/")[-1]
#         name = tgz.split("-")[0]
#         temp_version = tgz.split("-")[1]
#         version = temp_version.rstrip(".tgz")
#         mete = {
#           "tgz": tgz,
#           "name": name,
#           "version": version,
#         }
#         yield Request(url, meta=mete)

# class ImagesDownloadPipeline(ImagesPipeline):
#   def get_media_requests(self, item, info):
#       if item["image_urls"]:
#         for url in item["image_urls"]:
#           mete = {
#             "name": item["name"],
#           }
#           yield Request(url, meta=mete)
#   def file_path(self, request, response=None, info=None):
#     name = request.meta["name"]
#     image_guid = name
#     return f'/rainchart/{image_guid}.jpg'

class ImagesDownloadPipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
      for image_url in item['image_urls']:
        yield Request(image_url)

    def image_downloaded(self, response, request, info, *, item=None):
      checksum = None
      for path, image, buf in self.get_images(response, request, info, item=item):
        if checksum is None:
          buf.seek(0)
          checksum = md5sum(buf)
          file_name = item["name"]
          market_id = "859a51f9bb3b48b5bfd222e3bef56425"
          url = "https://hub.grapps.cn/app-server/markets/{}/helm/{}/icon".format(market_id, file_name)
          headers = {'Content-Type': 'image/jpeg'}
          resp = requests.post(url, data=buf.getvalue(), headers=headers)
      return checksum

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
      buf = BytesIO(response.body)
      checksum = md5sum(buf)
      buf.seek(0)
      url = "https://charts.grapps.cn/api/charts"
      headers = {"Content-Type": "application/octet-stream"}
      chart_resp = requests.post(url, headers=headers, data=buf).json()
      return checksum
