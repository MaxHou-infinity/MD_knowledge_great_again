import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import html2text
import os

class WebCrawler:
    def __init__(self):
        self.visited_urls = set()
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = False
        self.converter.body_width = 0
        self.converter.protect_links = True
        self.converter.mark_code = True

    def is_valid_url(self, url, base_url):
        # 确保URL属于同一域名
        base_domain = urlparse(base_url).netloc
        url_domain = urlparse(url).netloc
        return base_domain == url_domain

    def extract_urls(self, html, base_url):
        soup = BeautifulSoup(html, 'html.parser')
        urls = set()
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                absolute_url = urljoin(base_url, href)
                if self.is_valid_url(absolute_url, base_url):
                    urls.add(absolute_url)
        return urls

    def html_to_markdown(self, html):
        # 转换HTML到Markdown，保持代码格式
        return self.converter.handle(html)

    def crawl(self, start_url, save_path, headers=None, cookies=None):
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        def crawl_url(url, depth=0):
            if url in self.visited_urls or depth > 5:  # 限制爬取深度
                return

            try:
                response = requests.get(url, headers=headers, cookies=cookies)
                response.raise_for_status()
                self.visited_urls.add(url)

                # 转换内容为Markdown
                markdown_content = self.html_to_markdown(response.text)

                # 保存Markdown文件
                filename = f"{urlparse(url).path.strip('/').replace('/', '_') or 'index'}.md"
                file_path = os.path.join(save_path, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {url}\n\n")
                    f.write(markdown_content)

                # 提取并访问子URL
                urls = self.extract_urls(response.text, url)
                for sub_url in urls:
                    crawl_url(sub_url, depth + 1)

            except Exception as e:
                print(f"Error crawling {url}: {str(e)}")

        crawl_url(start_url)