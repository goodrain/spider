import copy
import os
import scrapy
import datetime
from rainbondSpider.items import PackageItem
import re
class HelmchartSpider(scrapy.Spider):
  name = "helmchart"
  allowed_domains = ["artifacthub.io"]
  def start_requests(self):
    for num in range(0, 15):
      yield scrapy.Request(
        url=f"https://artifacthub.io/api/v1/packages/search?facets=true&sort=relevance&limit=60&offset={num * 60}"
      )

  #获取列表
  def parse(self, response, **kwargs):
    data = response.json()
    packages_lists = data['packages']
    for packages_list in packages_lists:
      repository = packages_list.get('repository', {})
      if repository.get('kind', '') == 0:
        package_item = PackageItem()
        package_item['kind'] = repository.get('kind', '')
        package_item['repository_name'] = repository.get('name', '')
        # 获取应用的 id、名称、版本、作者名称、简介
        package_item['name'] = packages_list.get('name', '')
        package_item['normalized_name'] = packages_list.get('normalized_name', '')
        # 判断更新时间
        time = packages_list.get('ts', '')
        datetime_obj = datetime.datetime.fromtimestamp(time)
        current_date = datetime.datetime.now()
        time_difference = current_date - datetime_obj
        months_difference = time_difference.days // 30
        time_control = False
        if months_difference <= 3:
          time_control = True
        # 获取应用详情链接
        if 'demo' not in package_item['name'] and 'Demo' not in package_item['name'] and time_control == True:
          packages_list_url = f"https://artifacthub.io/api/v1/packages/helm/{package_item['repository_name'].lower()}/{package_item['normalized_name'].lower()}"
          yield scrapy.Request(
            url=packages_list_url,
            callback=self.parse_versions,
            headers={'Content-Type': 'application/yaml'},
            cb_kwargs={"item": copy.deepcopy(package_item)},
            dont_filter=True
          )
  #获取应用values文件内容
  def parse_versions(self, response, **kwargs):
    package_item = kwargs['item']
    data = response.json()
    versions = data.get('available_versions', [])
    grouped_versions = {}
    for version in versions:
      major, _, _ = self.get_version_parts(version)
      if major not in grouped_versions:
        grouped_versions[major] = []
      grouped_versions[major].append(version['version'])
    # 获取每个大版本的最后一个中版本和最后一个大版本中每个中版本的最后一个小版本
    merged_array = []
    for values in grouped_versions.values():
      merged_array.extend(values)
    # 保存主要版本号对应的最新小版本，通常情况下认为 6.20.3 中，6.20 是主要版本号。例如 6.20 对应的最新小版本是 6.20.3
    ver_rels = {}
    # 大版本最多保留3个，大版本号则是第一位版本数字，如 6，5，4如果大版本下面的小版本超过3个，只保留最新的3个，如 6.20, 6.19, 6.18, 5.13, 4.12
    major_versions = set()
    # 遍历版本列表，获取主要版本号，然后根据主要版本号获取最新的小版本号

    for version in merged_array:
      if len(version.split('.')) < 3:
        continue
      # 记录主要版本号
      main_version = version.split('.')[0] + '.' + version.split('.')[1]
      # 记录大版本号
      major_versions.add(version.split('.')[0])
      # 如果主要版本号不存在，则记录主要版本号对应的最新小版本号
      if not ver_rels.get(main_version):
        ver_rels[main_version] = version
      # 如果主要版本号存在，则比较当前版本号和已存在的版本号，如果当前版本号大于已存在的版本号，则替换
      elif ver_rels[main_version] < version:
        ver_rels[main_version] = version
    # 打印主要版本号对应的最新小版本号

    filtered_list = []
    # 用来控制选择的大版本号的个数
    i = 3
    # 对 major_versions 进行倒序排序
    int_major_versions = [int(major_version) for major_version in major_versions]
    major_versions = sorted(int_major_versions, reverse=True)
    for major_version in major_versions:
      if i == 0:
        break
      versions = []
      for version in merged_array:
        main_version = version.split('.')[0] + '.' + version.split('.')[1]
        # 如果版本号以该大版本号开头，并且不在已经获取的版本列表中，则添加到版本列表中
        if version.startswith(str(major_version) + '.') and (main_version not in versions):
          versions.append(main_version)
      # 排序
      versions.sort(reverse=True,
                    key=lambda x: list(map(int, x.split('.'))))
      # 保留主要版本（6.19, 6.18, 5.13, 4.12）的个数
      filtered_list.extend(versions[:3])
      i -= 1

    # 打印最终的版本列表
    results = [ver_rels[version] for version in filtered_list]
    for version in results:
      url = f"https://artifacthub.io/api/v1/packages/helm/{package_item['repository_name'].lower()}/{package_item['normalized_name'].lower()}/{version}"
      yield scrapy.Request(
        url=url,
        callback=self.parse_detail,
        cb_kwargs={"item":  copy.deepcopy(package_item)},
        dont_filter=True
      )
  # 获取应用详情
  def parse_detail(self, response, **kwargs):
    package_item = kwargs['item']
    data = response.json()
    repository = data.get('repository')
    # 获取应用介绍、logo地址
    html_content = data.get('readme', '')
    # 替换 readme 内容
    chart_url = os.getenv("CHARTURL")
    new_repo_url = f"{chart_url}/"
    new_repo_name=f" appstore/{package_item['name']}"
    pattern = r'helm (repo add|install) ([^\s]+) ([^\s]+)'
    result = re.search(pattern, html_content)
    if result:
      repo_name = result.group(2)
      repo_url = result.group(3)
      if repo_url :
        old_url = repo_url
        html_content = html_content.replace(old_url, new_repo_url)
      if repo_name :
        old_name = f" {repo_name} "
        old_repo_name = f" {repo_name}/{package_item['name']}"
        html_content = html_content.replace(old_repo_name, new_repo_name)
        html_content = html_content.replace(old_name, " appstore ")
    logo = data.get('logo_image_id', '')
    category = data.get('category', '')
    if logo == "":
      logo = 'https://artifacthub.io/static/media/placeholder_pkg_helm.png'
    else:
      logo = f"https://artifacthub.io/image/{logo}@2x"
    # 下载地址请求
    downloadUrl = data.get('content_url', '')
    # if "github.com" in downloadUrl:
    #   downloadUrl = "https://ghproxy.com/" + downloadUrl
    package_item['logo_image_id'] = logo
    package_item["readme"] = html_content
    package_item["file_urls"] = [downloadUrl]
    package_item["category"] = category
    package_item['version'] = data.get('version', '')
    package_item['image_urls'] = [logo]
    package_item['repository_name'] = repository.get('name', '')
    # 获取应用的 id、名称、版本、作者名称、简介
    package_item['package_id'] = data.get('package_id', '')
    package_item['name'] = data.get('name', '')
    package_item['normalized_name'] = data.get('normalized_name', '')
    package_item['display_name'] = repository.get('display_name', 'null')
    package_item['description'] = data.get('description', '')
    if data.get('readme', '') and package_item["category"]:
      yield package_item

  # 获取版本号的主版本、中版本和小版本
  def get_version_parts(self, version):
    v = version
    if type(v) == dict:
      v = version["version"]
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", v)
    if match:
      major = int(match.group(1))
      minor = int(match.group(2))
      patch = int(match.group(3))
      return major, minor, patch
    else:
      return None, None, None


