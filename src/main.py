import logging
import re
import requests_cache

from exceptions import ParserFindTagException
from requests import RequestException
from tqdm import tqdm
from urllib.parse import urljoin

from constants import BASE_DIR, MAIN_DOC_URL, EXPECTED_STATUS
from constants import DOWNLOAD_URL, PEPS_URL, WHATSNEW_URL
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_soup, find_tag, logging_print

LOGIING_ARCHIVE = 'Архив был загружен и сохранён:{path}'
LOGIING_FILE = 'Файл с результатами был сохранён: {path}'
LOGIING_PEP = 'Несовпадающие статусы: {link} \nСтатус в карточке: {p_status} '
'\nОжидаемые статусы:{status} '
LOGIING_SOUP = 'не удалось получить данные из {link}'


def whats_new(session):
    logging_pull = []
    soup = get_soup(session, WHATSNEW_URL)
    div_list = soup.find('div', class_='toctree-wrapper compound')
    li_list = div_list.find_all('li', class_="toctree-l2")
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор'), ]
    for li in tqdm(li_list):
        li_tag = find_tag(li, 'a')
        version_link = urljoin(WHATSNEW_URL, li_tag['href'])
        try:
            soup = get_soup(session, version_link)
        except RequestException:
            logging_pull.append(LOGIING_SOUP.format(version_link))
            continue
        h1 = soup.find('h1').text
        d1 = soup.find('dl')
        d1_text = d1.text.replace('\n', ' ')
        results.append((li_tag['href'], h1, d1_text))
    logging_print(logging_pull)
    return results


def latest_versions(session):
    sidebar = find_tag(get_soup(session, MAIN_DOC_URL), 'div',
                       attrs={'class': 'sphinxsidebar'})
    ui_tags = sidebar.find_all('ul')

    for ul in ui_tags:
        if "All versions" in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            error_message = 'Ничего не нашлось'
            raise ParserFindTagException(error_message)

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'

    for a_tag in a_tags:
        match = re.search(pattern, a_tag.text)
        link = a_tag['href']
        if match is not None:
            version = match.group(1)
            status = match.group(2)
        else:
            version = a_tag.text
            status = ""
        results.append((link, version, status))

    return results


def download(session):
    DOWNLOAD_DIR = BASE_DIR / 'downloads'
    table = find_tag(get_soup(session, DOWNLOAD_URL), 'table',
                     attrs={'class': 'docutils'})
    pdf = find_tag(table, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    link = urljoin(DOWNLOAD_URL, pdf['href'])
    file_name = link.split('/')[-1]
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    archive_path = DOWNLOAD_DIR / file_name
    print(type(archive_path))
    response = session.get(link)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(LOGIING_ARCHIVE.format(path=archive_path))


def pep(session):
    logging_pull = []
    counter = {
        'A': 0,
        'D': 0,
        'F': 0,
        'P': 0,
        'R': 0,
        'S': 0,
        'W': 0,
        '': 0,
    }

    soup = get_soup(session, PEPS_URL)
    section = soup.find('section', id='index-by-category')
    sections = section.find_all('section')

    for sec in tqdm(sections):
        table = sec.find('table')
        if table is None:
            continue
        pep_list = table.find_all('tr')
        for pep in pep_list[1:]:
            tag = find_tag(pep, 'td')
            link = find_tag(tag.find_next_sibling(), 'a')['href']
            tag = tag.text[1:]
            ab_link = urljoin(PEPS_URL, link)
            try:
                soup = get_soup(session, ab_link)
            except RequestException:
                logging_pull.append(LOGIING_SOUP.format(link=ab_link))
                continue
            content = find_tag(soup, 'section',
                               attrs={'id': "pep-content"})

            content = content.find('dl')
            p_info = content.find_all('dt')
            for dt in p_info:
                if dt.text == "Status:":
                    p_status = dt.find_next_sibling().text
                    break
            if p_status in EXPECTED_STATUS[tag]:
                counter[tag] += 1
            else:
                logging_pull.append(LOGIING_PEP.format(link=link,
                                                       p_status=p_status,
                                                       status=EXPECTED_STATUS[
                                                           tag]))
    logging_print(logging_pull)
    results = [("Статус", "Количество")]
    for key, value in counter.items():
        results.append((key, value))
    results.append(("Total ", sum(counter.values())))
    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}

MAIN_ERROR_MESSAGE = 'Возникла ошибка: {error_message}'


def main():
    try:
        configure_logging()
        logging.info("Парсер начал работу")
        arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
        args = arg_parser.parse_args()
        session = requests_cache.CachedSession()
        if args.clear_cache:
            session.cache.clear()
        parser_mode = args.mode
        results = MODE_TO_FUNCTION[parser_mode](session)
        if results is not None:
            control_output(results, args)
        logging.info('Парсер завершил работу.')
    except Exception as error:
        logging.exception(MAIN_ERROR_MESSAGE.format(error_message=error),
                          stack_info=True)


if __name__ == '__main__':
    main()
