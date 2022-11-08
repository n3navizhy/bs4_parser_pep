import csv
import logging
import re
import requests_cache


from exceptions import ParserFindTagException
from tqdm import tqdm
from urllib.parse import urljoin


from constants import BASE_DIR, MAIN_DOC_URL, PEP_link, EXPECTED_STATUS
from constants import FILE_PATH, D_URL, PEPS_URL, WN_URL
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_soup, find_tag, logging_print


LOGIING_ARCHIVE = 'Архив был загружен и сохранён:{path}'
LOGIING_FILE = 'Файл с результатами был сохранён: {path}'
LOGIING_PEP = 'Несовпадающие статусы: {link} \nСтатус в карточке: {p_status} '
'\nОжидаемые статусы:{status} '
LOGIING_SOUP = 'не удалось получить данные из {link}'


def whats_new(session):
    LOGGING_PULL = []
    soup = get_soup(session, WN_URL)
    div_list = soup.find_all('div', class_='toctree-wrapper compound')
    li_list = div_list[0].find_all('li', class_="toctree-l2")
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор'), ]
    for li in tqdm(li_list):
        li_tag = find_tag(li, 'a')
        version_link = urljoin(WN_URL, li_tag['href'])
        try:
            soup = get_soup(session, version_link)
        except:
            LOGGING_PULL.append(LOGIING_SOUP.format(version_link))
            continue
        h1 = soup.find('h1').text
        d1 = soup.find('dl')
        d1_text = d1.text.replace('\n', ' ')
        results.append((li_tag['href'], h1, d1_text))
    logging_print(LOGGING_PULL)
    return results


def latest_versions(session):
    soup = get_soup(session, MAIN_DOC_URL)
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebar'})
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
    soup = get_soup(session, D_URL)
    table = find_tag(soup, 'table', attrs={'class': 'docutils'})
    pdf = find_tag(table, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    link = urljoin(D_URL, pdf['href'])
    file_name = link.split('/')[-1]
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    archive_path = DOWNLOAD_DIR / file_name
    print(type(archive_path))
    response = session.get(link)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(LOGIING_ARCHIVE.format(path=archive_path))


def pep(session):
    LOGGING_PULL = []
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
    section = section.find_all('section')

    for sec in tqdm(section):
        table = sec.find('table')
        if table is None:
            continue
        pep_list = table.find_all('tr')
        for pep in pep_list[1:]:
            tag = find_tag(pep, 'td')
            link = find_tag(tag.find_next_sibling(), 'a')['href']
            tag = tag.text[1:]
            ab_link = urljoin(PEP_link, link)
            try:
                soup = get_soup(session, ab_link)
            except:
                LOGGING_PULL.append(LOGIING_SOUP.format(link=ab_link))
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
                LOGGING_PULL.append(LOGIING_PEP.format(link=link,
                                                       p_status=p_status,
                                                status=EXPECTED_STATUS[tag]))
    with open(FILE_PATH, 'w', encoding='utf-8') as file:
        writer = csv.DictWriter(file, counter.keys())
        writer.writeheader()
        writer.writerow(counter)
        writer = csv.writer(file, delimiter=' ')
        writer.writerow(["Total: " + str(sum(counter.values()))])
    logging_print(LOGGING_PULL)
    logging.info(LOGIING_FILE.format(path=FILE_PATH))


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


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
    except Exception:
        logging.exception('Возникла ошибка', stack_info=True)


if __name__ == '__main__':
    main()
