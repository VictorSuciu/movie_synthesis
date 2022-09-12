import scrapy
import json
import re
from bs4 import BeautifulSoup


class MovieScript(scrapy.Item):
    title = scrapy.Field()
    date = scrapy.Field()
    writers = scrapy.Field()
    raw_script = scrapy.Field()


class ImsdbScraper(scrapy.Spider):
    name = 'imsdb'
   
    # each of imsdb's alphabetical categories from 'A' to 'Z' and an extra one for '#' (denoted in the url as '0')
    letters = ['0'] + [chr(i + 65) for i in range(26)]
    
    start_urls = [f'https://imsdb.com/alphabetical/{letter}' for letter in letters]

    def parse(self, response):
        script_info_html = response.text.split('\n')[-1]
        script_all_info = re.findall(r'<p>.+?</p>', script_info_html)

        script_titles = [re.search(r'title=".+?"', line) for line in script_all_info]
        script_titles = [match.group(0) [7:-8] for match in script_titles]

        script_dates = [re.search(r'</a>.+?<br>', line) for line in script_all_info]
        script_dates = [match.group(0)[6:-11] for match in script_dates]

        script_writers = [re.search(r'<i>Written by.+?</i>', line) for line in script_all_info]
        script_writers = [match.group(0)[14:-4] for match in script_writers]
        
        count = 0
        for title, date, writers in zip(script_titles, script_dates, script_writers):
            raw_script_url = 'https://imsdb.com/scripts/' + title.replace(' ', '-') + '.html'
            print(raw_script_url)

            yield scrapy.Request(
                raw_script_url,
                callback=self.parse_script_page,
                meta={'title': title, 'date': date, 'writers': writers}
            )

            count += 1
        
        print(count)
    

    def parse_script_page(self, response):
        raw_text = BeautifulSoup(response.text, 'html.parser').get_text()

        script_item = MovieScript()
        script_item['title'] = response.meta['title']
        script_item['date'] = response.meta['date']
        script_item['writers'] = response.meta['writers'].split(',')
        script_item['raw_script'] = raw_text

        return script_item

    
    # def parse_script_metadata(self, response):
        

    #     # print('META RESPONSE')
    #     # print(response.text)
    #     # print('\n\n\n')
        
    #     return script_item


    
