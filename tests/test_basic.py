import unittest
from src.markdown_cleaner import MarkdownCleaner
from src.web_crawler import WebCrawler

class TestBasic(unittest.TestCase):
    def test_markdown_cleaner_init(self):
        cleaner = MarkdownCleaner(api_key="test_key")
        self.assertIsNotNone(cleaner)

    def test_web_crawler_init(self):
        crawler = WebCrawler()
        self.assertIsNotNone(crawler)

if __name__ == "__main__":
    unittest.main()
