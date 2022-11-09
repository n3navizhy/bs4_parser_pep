from pathlib import Path
from urllib.parse import urljoin
MAIN_DOC_URL = 'https://docs.python.org/3/'
PEPS_URL = "https://peps.python.org/"
DOWNLOAD_URL = urljoin(MAIN_DOC_URL, 'download.html')
WHATSNEW_URL = urljoin(MAIN_DOC_URL, 'whatsnew/')
BASE_DIR = Path(__file__).parent
FILE_PATH = BASE_DIR/'results'/'pep_result.csv'
DOWNLOAD_DIR = BASE_DIR/'downloads'
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
FILE_MODE = 'file'
PRETTY_MODE = 'pretty'
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
