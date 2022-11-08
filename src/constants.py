from pathlib import Path
from urllib.parse import urljoin
MAIN_DOC_URL = 'https://docs.python.org/3/'
BASE_DIR = Path(__file__).parent
FILE_PATH = BASE_DIR/'results'/'pep_result.csv'
D_URL = urljoin(MAIN_DOC_URL, 'download.html')
WN_URL = urljoin(MAIN_DOC_URL, 'whatsnew/')
PRETTY_MODE = 'pretty'
FILE_MODE = 'file'
DOWNLOAD_DIR = BASE_DIR/'downloads'
PEPS_URL = "https://peps.python.org/"
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
PEP_link = 'https://peps.python.org/'
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
