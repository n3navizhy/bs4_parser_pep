import logging

from exceptions import ParserFindTagException, ParserResopnseExceprion
from bs4 import BeautifulSoup
from requests import RequestException

find_message = 'Не найден тег {tag} {attrs}'
response_message = 'Возникла ошибка при загрузке страницы.'


def get_response(session, url):
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        raise ParserResopnseExceprion(response_message)


def get_soup(session, url):
    return BeautifulSoup(get_response(session, url).text, 'lxml')


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        raise ParserFindTagException(find_message.format(attrs=attrs, tag=tag))
    return searched_tag


def logging_print(pull):
    for log in pull:
        logging.info(log)
