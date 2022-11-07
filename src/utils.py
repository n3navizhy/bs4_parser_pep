
import logging

from exceptions import ParserFindTagException
from bs4 import BeautifulSoup
from requests import RequestException


def get_response(session, url):
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы {url}',
            stack_info=True
        )

def get_soup(response):
    soup = BeautifulSoup(response.text, 'lxml')
    return soup

def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_message = f'Не найден тег {tag} {attrs}'
        #logging.error(error_message, stack_info=True)
        #raise ParserFindTagException(error_msg)
    return searched_tag
