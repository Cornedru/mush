import sys, os, yaml, time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)

DOWNLOAD_DIR = os.path.dirname(os.path.abspath(__file__))[:-3] + 'logs/tmp/'

def setup_driver():
    firefox_options = Options()
    firefox_options.add_argument("--headless")
    firefox_options.add_argument("--no-sandbox")
    firefox_options.add_argument("--disable-dev-shm-usage")
    firefox_options.set_preference("browser.download.folderList", 2)  # Use custom path
    firefox_options.set_preference("browser.download.dir", DOWNLOAD_DIR)
    firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
    firefox_options.set_preference("pdfjs.disabled", True)  # Disable built-in PDF viewer
    firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
    firefox_options.set_preference("browser.download.manager.closeWhenDone", True)
    service = Service(GeckoDriverManager().install(), log_output=os.devnull)
    driver = webdriver.Firefox(service=service, options=firefox_options)
    return driver

def intra_driver():
    driver = setup_driver()
    driver.get("https://admin.intra.42.fr/users/auth/keycloak_admin")
    username_field = driver.find_element(By.XPATH, '//*[@id="username"]')
    username_field.send_keys("42mulhouse_tech")
    password_field = driver.find_element(By.XPATH, '//*[@id="password"]')
    password_field.send_keys(config['intra']['pwd_42mulhouse_tech'])
    login_button = driver.find_element(By.XPATH, '//*[@id="kc-login"]')
    login_button.click()

    with open('html', 'w') as f: f.write(driver.page_source)

    if 'View my profile' not in driver.page_source:
        print(f"Selenium webdriver: login to intra.42.fr with 42mulhouse_tech failed", file=sys.stderr, flush=True)
        os.remove('logs/webdriver.busy')
        sys.exit()
    print('webbrowser authenticated to intra.42.fr !')
    return driver

def get_intra_convention(url):
    while os.path.exists('logs/webdriver.busy'): time.sleep(1)
    with open('logs/webdriver.busy', 'w') as f: pass
    print(f'Downloading {url}')
    driver = intra_driver()
    driver.set_page_load_timeout(5)
    try: driver.get(url) #This get stuck so we want timeout
    except: driver.quit()
    os.remove('logs/webdriver.busy')
    os.rename(DOWNLOAD_DIR + url.split('/')[-1], DOWNLOAD_DIR + f"Convention_stage_{url.split('/')[-3]}.pdf")
    return DOWNLOAD_DIR + f"Convention_stage_{url.split('/')[-3]}.pdf"