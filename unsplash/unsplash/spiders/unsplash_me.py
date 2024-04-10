from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.pipelines.images import ImagesPipeline
import scrapy
import wget, re


class UnsplashSpider(scrapy.Spider):
    name = 'unsplash_me'
    start_urls = ['https://unsplash.com']
    image_limit = 10  # Ограничение на количество изображений(категорий)

    def parse(self, response,**kwargs):
        categories = response.xpath("/html/body/div/div/div[1]/div/div[2]/div/div/div[3]/div/div/ul/li")
        for category in categories:
            category_text = category.xpath(".//a/text()").get()
            category_href = response.urljoin(category.xpath(".//a/@href").get())
            yield scrapy.Request(category_href, callback=self.parse_category, meta={'category': category_text})

    def parse_category(self, response):
        images = response.xpath('//*[contains(@itemprop, "contentUrl") and contains(@href, "/photos/")]/@href')[
                 :self.image_limit]
        for image_href in images:
            image_url = response.urljoin(image_href.get())
            yield scrapy.Request(image_url, callback=self.parse_image, meta={'category': response.meta['category']})

    def parse_image(self, response):
        image_category = response.meta['category']
        image_title = response.xpath('/html/head/title/text()').get()
        image_title = image_title.split(' – ')[0]
        image_src = response.xpath(
            '/html/body/div/div/div[1]/div/div[2]/div/div[1]/div[3]/div/div/button/div/div[2]/img/@src').get()
        if image_src and image_category:
            image_filename = image_src.split('/')[-1].split('?')[0] + '.avif'
            image_dir = 'images'
            image_path = f"{image_dir}/{image_filename}"
            wget.download(image_src, out=image_path)  # возможно из-за формата avif не отрабатывает ImagesPipeline
            yield {
                'category': image_category,
                'title': image_title,
                'image_fnm': image_filename,
                'image_url': image_src
            }
