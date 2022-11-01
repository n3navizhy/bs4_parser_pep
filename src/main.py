from urllib.parse import urljoin
import requests_cache
import re
from bs4 import BeautifulSoup
from tqdm import tqdm
import logging
from utils import get_response
from constants import BaseDIR, MAIN_DOC_URL
from configs import configure_argument_parser, configure_logging
from outputs import control_output
import csv


def whats_new(session):
    wn_url = urljoin(MAIN_DOC_URL, 'whatsnew/')

    response = get_response(session, wn_url)
    if response is None:
        # Если основная страница не загрузится, программа закончит работу.
        return
    soup = BeautifulSoup(response.text, 'lxml')

    first_s = soup.find_all('div', class_='toctree-wrapper compound')
    sec_s = first_s[0].find_all('li', class_="toctree-l2")
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for i in tqdm(sec_s):
        res = i.find('a')
        version_link = urljoin(wn_url, res['href'])
        response = get_response(session, version_link)
        if response is None:
            return
        soup = BeautifulSoup(response.text, 'lxml')
        h1 = soup.find('h1').text
        d1 = soup.find('dl')
        d1_text = d1.text.replace('\n', ' ')
        results.append((res['href'], h1, d1_text))
    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    sidebar = soup.find('div', class_='sphinxsidebar')

    ui_tags = sidebar.find_all('ul')

    for ul in ui_tags:

        if "All versions" in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise Exception('Ничего не нашлось')

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
    d_url = urljoin(MAIN_DOC_URL, 'download.html')
    downloadDIR = BaseDIR/'downloads'
    response = get_response(session, d_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')

    table = soup.find('table', class_='docutils')

    pdf = table.find('a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    link = urljoin(d_url, pdf['href'])
    file_name = link.split('/')[-1]
    downloadDIR.mkdir(exist_ok=True)
    archive_path = downloadDIR/file_name

    response = session.get(link)

    with open(archive_path, 'wb') as file:
        file.write(response.content)
    print(archive_path)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    pep_list = []
    EXPECTED_STATUS = {
        'A': ('Active', 'Accepted'),
        'D': ('Deferred',),
        'F': ('Final',),
        'P': ('Provisional',),
        'R': ('Rejected',),
        'S': ('Superseded',),
        'W': ('Withdrawn',),
        '': ('Draft', 'Active'),
    }
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
    peps_url = "https://peps.python.org/"
    response = get_response(session, peps_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    section = soup.find('section', id='index-by-category')
    section = section.find_all('section')

    for sec in tqdm(section):

        table = sec.find('table')
        if table is not None:
            pep_list = table.find_all('tr')
            for pep in pep_list:
                t = pep.find('td')
                if t is not None:
                    t_status = t.text[1:]
                if pep.find('a', class_='pep reference internal') is not None:
                    link = pep.find('a', class_='pep reference internal')
                    link = link['href']
                    ab_link = 'https://peps.python.org/'+link
                    response = session.get(ab_link)
                    soup = BeautifulSoup(response.text, 'lxml')

                    content = soup.find(id="pep-content").find('dl')
                    p_info = content.find_all('dt')
                    for dt in p_info:
                        if dt.text == "Status:":
                            p_status = dt.find_next_sibling().text
                            break
                    if p_status in EXPECTED_STATUS[t_status]:
                        counter[t_status] += 1
                    else:
                        logging.info(f'''Несовпадающие статусы: {link}
                        Статус в карточке: {p_status}
                        Ожидаемые статусы: {EXPECTED_STATUS[t_status]}''')

    file_path = BaseDIR/'results'/'pep_result.csv'
    with open(file_path, 'w', encoding='utf-8') as file:
        w = csv.DictWriter(file, counter.keys())
        w.writeheader()
        w.writerow(counter)

    logging.info(f'Файл с результатами был сохранён: {file_path}')


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info("Rabotaet")
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


if __name__ == '__main__':
    main()
