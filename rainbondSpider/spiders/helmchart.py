import scrapy
import datetime
from rainbondSpider.items import PackageItem

class HelmchartSpider(scrapy.Spider):
  name = "helmchart"
  allowed_domains = ["artifacthub.io"]
  def start_requests(self):
    for num in range(15):
      yield scrapy.Request(
        url=f"https://artifacthub.io/api/v1/packages/search?facets=true&sort=relevance&limit=60&offset={num * 60}"
      )

  #获取列表
  def parse(self, response, **kwargs):
    data = response.json()
    packages_lists = data['packages']
    for packages_list in packages_lists:
      package_item = PackageItem()
      repository = packages_list.get('repository', {})

      if repository.get('kind', '') == 0:
        package_item['kind'] = repository.get('kind', '')
        package_item['repository_name'] = repository.get('name', '')
        # 获取应用的 id、名称、版本、作者名称、简介
        package_item['package_id'] = packages_list.get('package_id', '')
        package_item['name'] = packages_list.get('name', '')
        package_item['version'] = packages_list.get('version', '')
        package_item['display_name'] = repository.get('display_name', '')
        package_item['description'] = packages_list.get('description', '')
        # 下载
        package_item['file_names'] = packages_list.get('name', '')
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
          packages_list_url: str = f"https://artifacthub.io/api/v1/packages/{package_item['package_id']}/{package_item['version']}/values"
          yield scrapy.Request(
            url = packages_list_url,
            callback=self.parse_values,
            headers={'Content-Type': 'application/yaml'},
            cb_kwargs={"item": package_item}
          )
  #获取应用values文件内容
  def parse_values(self, response, **kwargs):
    package_item = kwargs['item']
    content_type = response.headers.get('Content-Type', b'').decode('utf-8')
    if 'application/yaml' in content_type:
      # 响应内容是YAML文件类型
      yaml_data = response.text
      if 'gcr.io' not in yaml_data and 'quay.io' not in yaml_data and 'ghcr.io' not in yaml_data:
        url = f"https://artifacthub.io/api/v1/packages/helm/{package_item['repository_name'].lower()}/{package_item['name'].lower()}"
        yield scrapy.Request(
          url=url,
          callback=self.parse_detail,
          cb_kwargs={"item": package_item}
        )
  # 获取应用详情
  def parse_detail(self, response, **kwargs):
    package_item = kwargs['item']
    data = response.json()
    # 获取应用介绍、logo地址

    # html_content = self.convert_to_markdown(data.get('readme', ''))
    html_content = data.get('readme', '')

    logo = data.get('logo_image_id', '')
    if logo == "":
      logo = 'https://artifacthub.io/static/media/placeholder_pkg_helm.png'
    else:
      logo = f"https://artifacthub.io/image/{logo}@2x"
    # 下载地址请求
    downloadUrl = data.get('content_url', '')
    if "github.com" in downloadUrl :
      downloadUrl = "https://ghproxy.com/" + downloadUrl
    package_item['logo_image_id'] = logo
    package_item["readme"] = html_content
    package_item["file_urls"] = [downloadUrl]
    yield package_item
  def convert_to_markdown(self, text):
    lines = text.split('\n')
    markdown_lines = [line.strip() for line in lines]
    return '  \n'.join(markdown_lines)

