#!/usr/bin/env python3

__author__ = "Po-E Li, B10, LANL"
__copyright__ = "LANL 2020"
__license__ = "GPL"
__version__ = "21.05.10"
__email__ = "po-e@lanl.gov"

import os
import time
import sys
import argparse as ap
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M',
)

def parse_params():
    p = ap.ArgumentParser(prog='gisaid_EpiCoV_downloader.py',
                          description="""Download EpiCoV sequences from GISAID. WARNING: By using this software you agree GISAID's Terms of Use and reaffirm your understanding of these terms.""")

    p.add_argument('-u', '--username',
                   metavar='[STR]', nargs=1, type=str, required=False,
                   help="GISAID username")

    p.add_argument('-p', '--password',
                   metavar='[STR]', nargs=1, type=str, required=False,
                   help="GISAID password")

    p.add_argument('-o', '--outdir',
                   metavar='[STR]', type=str, required=True, default='downloads/',
                   help="Output directory")

    p.add_argument('-l', '--location',
                   metavar='[STR]', type=str, required=False, default=None,
                   help="sample location")

    p.add_argument('-ht', '--host',
                   metavar='[STR]', type=str, required=False, default='Human',
                   help="Specify a host of the sample. Default is human.")

    p.add_argument('-cs', '--colstart',
                   metavar='[YYYY-MM-DD]', type=str, required=False, default=None,
                   help="collection starts date")

    p.add_argument('-ce', '--colend',
                   metavar='[YYYY-MM-DD]', type=str, required=False, default=None,
                   help="collection ends date")

    p.add_argument('-ss', '--substart',
                   metavar='[YYYY-MM-DD]', type=str, required=False, default=None,
                   help="submissions start date")

    p.add_argument('-se', '--subend',
                   metavar='[YYYY-MM-DD]', type=str, required=False, default=None,
                   help="submitssions end date")
    
    p.add_argument('-voc', '--variant',
                metavar='[STR]', type=str, required=False, default='',
                help="Specify a variant of concern. Default is empty (all).")

    p.add_argument('-cg', '--complete',
                   action='store_true', help='complete genome only')

    p.add_argument('-hc', '--highcoverage',
                   action='store_true', help='high coverage only')

    p.add_argument('-le', '--lowcoverageExcl',
                   action='store_true', help='low coverage excluding')

    p.add_argument('-t', '--timeout',
                   metavar='[INT]', type=int, required=False, default=90,
                   help="set action timeout seconds. Default is 90 secs.")

    p.add_argument('-r', '--retry',
                   metavar='[INT]', type=int, required=False, default=5,
                   help="retry how many times when the action fails. Default is 5 times.")

    p.add_argument('-i', '--interval',
                   metavar='[INT]', type=int, required=False, default=3,
                   help="time interval between retries in second(s). Default is 3 seconds.")

    p.add_argument('-nnd', '--nonextstraindata',
                   action='store_true', help='Do not download nextstrain data')

    p.add_argument('--normal',
                   action='store_true', help='run firefox in normal mode.')

    p.add_argument('--ffbin',
                   metavar='[STR]', type=str, required=False,
                   help="Specify the path of firefox binary.")

    p.add_argument('--version',
                   action='store_true', help='print version number.')

    args_parsed = p.parse_args()
    if not os.path.exists(args_parsed.outdir):
        os.makedirs(args_parsed.outdir)
    return args_parsed


def download_gisaid_EpiCoV(
        uname,     # username
        upass,     # password
        normal,    # normal mode (quite)
        wd,        # output dir
        loc,       # location
        host,      # host
        cs,        # collection start date
        ce,        # collection end date
        ss,        # submission start date
        se,        # submission end date
        voc,       # variant of concern
        cg,        # complete genome only
        hc,        # high coverage only
        le,        # low coverage excluding
        to,        # timeout in sec
        rt,        # num of retry
        iv,        # interval in sec
        nnd,       # do not download nextstrain data
        ffbin      # firefox binary path
    ):
    """Download sequences and metadata from EpiCoV GISAID"""

    # when user doesn't download nextstrain data, it's essential to enter time range/location
    if not (cs or ce or ss or se or loc) and nnd:
        logging.error("No time range or location entered.")
        sys.exit(1)

    # output directory
    if not os.path.exists(wd):
        os.makedirs(wd, exist_ok=True)

    wd = os.path.abspath(wd)
    GISAID_DTL_JASON = f'{wd}/gisaid_detail_metadata.json'
    metadata = []

    # MIME types
    mime_types = "application/octet-stream"
    mime_types += ",application/excel,application/vnd.ms-excel"
    mime_types += ",application/pdf,application/x-pdf"
    mime_types += ",application/x-bzip2"
    mime_types += ",application/x-gzip,application/gzip"

    # start fresh
    try:
        os.remove(GISAID_DTL_JASON)
    except OSError:
        pass

    logging.info("Opening browser...")

    options=Options()
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", wd)
    options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk", mime_types)
    options.set_preference(
        "plugin.disable_full_page_plugin_for_types", mime_types)
    options.set_preference("pdfjs.disabled", True)

    if not normal:
        options.add_argument('-headless')

    service = Service(r'./geckodriver')
    # Download geckodriver from https://github.com/mozilla/geckodriver/releases and put it in the same directory as this script
    driver = webdriver.Firefox(service=service, options=options, firefox_binary=ffbin)

    # driverwait
    driver.implicitly_wait(30)
    wait = WebDriverWait(driver, to)

    # open GISAID
    logging.info("Opening website GISAID...")
    driver.get('https://www.epicov.org/epi3/frontend')
    waiting_sys_timer(wait)
    logging.info(driver.title)
    assert 'GISAID' in driver.title

    # login
    logging.info("Loggining into GISAID...")
    username = driver.find_element(By.NAME, 'login')
    username.send_keys(uname)
    password = driver.find_element(By.NAME, 'password')
    password.send_keys(upass)
    driver.execute_script("return doLogin();")

    waiting_sys_timer(wait)

    # navigate to EpiCoV
    logging.info("Navigating to EpiCoV...")
    epicov_tab = driver.find_element(By.XPATH, "//div[@id='main_nav']//li[3]/a")
    epicov_tab.click()

    waiting_sys_timer(wait)

    # download nextstrain data
    if not nnd:
        # download from downloads section
        logging.info("Clicking downloads...")
        pd_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='sys-actionbar-bar']//div[3]")))
        pd_button.click()

        waiting_sys_timer(wait)

        # have to click the first row twice to start the iframe
        iframe_dl = waiting_for_iframe(wait, driver, rt, iv)

        logging.info("Downloading metadata...")
        driver.switch_to.frame(iframe_dl)
        waiting_sys_timer(wait)
        dl_button = driver.find_element(By.XPATH, '//div[contains(text(), "metadata")]')
        dl_button.click()
        waiting_sys_timer(wait)
        # waiting for REMINDER
        iframe = waiting_for_iframe(wait, driver, rt, iv)
        driver.switch_to.frame(iframe)
        waiting_sys_timer(wait)
        # agree terms and conditions
        logging.info(" -- agreeing terms and conditions")
        checkbox = driver.find_element(By.XPATH, '//input[@class="sys-event-hook"]')
        checkbox.click()
        waiting_sys_timer(wait)
        # click download button
        dl_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//button[contains(text(), "Download")]')))
        dl_button.click()
        waiting_sys_timer(wait)
        logging.info(" -- downloading")
        # Opening Firefox downloading window
        driver.switch_to.default_content()
        fn = wait_downloaded_filename(wait, driver, 600)
        logging.info(f" -- downloaded to {fn}")
        
        waiting_sys_timer(wait)

        logging.info("Downloading FASTA...")
        driver.switch_to.frame(iframe_dl)
        waiting_sys_timer(wait)
        # click nextfasta button
        dl_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[text()="FASTA"]')))
        dl_button.click()
        waiting_sys_timer(wait)
        # waiting for REMINDER
        iframe = waiting_for_iframe(wait, driver, rt, iv)
        driver.switch_to.frame(iframe)
        waiting_sys_timer(wait)
        # agree terms and conditions
        logging.info(" -- agreeing terms and conditions")
        checkbox = driver.find_element(By.XPATH, '//input[@class="sys-event-hook"]')
        checkbox.click()
        waiting_sys_timer(wait)
        # click download button
        dl_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//button[contains(text(), "Download")]')))
        dl_button.click()
        waiting_sys_timer(wait)
        logging.info(" -- downloading")
        # Opening Firefox downloading window
        driver.switch_to.default_content()
        fn = wait_downloaded_filename(wait, driver, 600)
        logging.info(f" -- downloaded to {fn}.")

        waiting_sys_timer(wait)

        logging.info("Downloading MSA full...")
        driver.switch_to.frame(iframe_dl)
        waiting_sys_timer(wait)
        # click MSA full button
        dl_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(text(), "MSA full")]')))
        dl_button.click()
        waiting_sys_timer(wait)
        # waiting for REMINDER
        iframe = waiting_for_iframe(wait, driver, rt, iv)
        driver.switch_to.frame(iframe)
        waiting_sys_timer(wait)
        # agree terms and conditions
        logging.info(" -- agreeing terms and conditions")
        checkbox = driver.find_element(By.XPATH, '//input[@class="sys-event-hook"]')
        checkbox.click()
        waiting_sys_timer(wait)
        # click download button
        dl_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//button[contains(text(), "Download")]')))
        dl_button.click()
        waiting_sys_timer(wait)
        logging.info(" -- downloading")
        # Opening Firefox downloading window
        driver.switch_to.default_content()
        fn = wait_downloaded_filename(wait, driver, 600)
        logging.info(f" -- downloaded to {fn}.")


        waiting_sys_timer(wait)

        logging.info("Downloading MSA unmasked...")
        driver.switch_to.frame(iframe_dl)
        waiting_sys_timer(wait)
        # click MSA unmasked button
        dl_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(text(), "MSA unmasked")]')))
        dl_button.click()
        waiting_sys_timer(wait)
        # waiting for REMINDER
        iframe = waiting_for_iframe(wait, driver, rt, iv)
        driver.switch_to.frame(iframe)
        waiting_sys_timer(wait)
        # agree terms and conditions
        logging.info(" -- agreeing terms and conditions")
        checkbox = driver.find_element(By.XPATH, '//input[@class="sys-event-hook"]')
        checkbox.click()
        waiting_sys_timer(wait)
        # click download button
        dl_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//button[contains(text(), "Download")]')))
        dl_button.click()
        waiting_sys_timer(wait)
        logging.info(" -- downloading")
        # Opening Firefox downloading window
        driver.switch_to.default_content()
        fn = wait_downloaded_filename(wait, driver, 600)
        logging.info(f" -- downloaded to {fn}.")


        waiting_sys_timer(wait)

        logging.info("Downloading MSA masked...")
        driver.switch_to.frame(iframe_dl)
        waiting_sys_timer(wait)
        # click MSA masked button
        dl_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[contains(text(), "MSA masked")]')))
        dl_button.click()
        waiting_sys_timer(wait)
        # waiting for REMINDER
        iframe = waiting_for_iframe(wait, driver, rt, iv)
        driver.switch_to.frame(iframe)
        waiting_sys_timer(wait)
        # agree terms and conditions
        logging.info(" -- agreeing terms and conditions")
        checkbox = driver.find_element(By.XPATH, '//input[@class="sys-event-hook"]')
        checkbox.click()
        waiting_sys_timer(wait)
        # click download button
        dl_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//button[contains(text(), "Download")]')))
        dl_button.click()
        waiting_sys_timer(wait)
        logging.info(" -- downloading")
        # Opening Firefox downloading window
        driver.switch_to.default_content()
        fn = wait_downloaded_filename(wait, driver, 600)
        logging.info(f" -- downloaded to {fn}.")


        waiting_sys_timer(wait)

        # go back to main frame
        driver.switch_to.frame(iframe_dl)
        back_button = driver.find_element(By.XPATH, '//button[contains(text(), "Back")]')
        back_button.click()

        driver.switch_to.default_content()
        waiting_sys_timer(wait)

    if cs or ce or ss or se or loc:
        logging.info("Searching in EpiCoV...")
        browse_tab = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[contains(text(), "Search")]')))
        browse_tab.click()
        waiting_sys_timer(wait)
        waiting_table_to_get_ready(wait)
        num_genomes = driver.find_element(By.CSS_SELECTOR, "div.sys-datatable-info-left span")
        logging.info("{}...".format(num_genomes.text))

        # set location
        if loc:
            logging.info("Setting location...")
            loc_input = driver.find_element(By.XPATH, '//div[text()="Location"]/../following-sibling::td//input')
            loc_input.send_keys(loc)
            waiting_sys_timer(wait, 5)
            num_genomes = driver.find_element(By.CSS_SELECTOR, "div.sys-datatable-info-left span")
            logging.info("{}...".format(num_genomes.text))

        # set host
        if host:
            logging.info("Setting host...")
            host_input = driver.find_element(By.XPATH, '//div[text()="Host"]/../following-sibling::td//input')
            host_input.send_keys(host)
            waiting_sys_timer(wait, 5)
            num_genomes = driver.find_element(By.CSS_SELECTOR, "div.sys-datatable-info-left span")
            logging.info("{}...".format(num_genomes.text))

        # set dates
        if ss or se:
            date_inputs = driver.find_elements(By.CSS_SELECTOR, "div.sys-form-fi-date input")
        if ss:
            logging.info("Setting submissions start date...")
            ss_input = date_inputs[2] # 2nd input is the submission start date
            ss_input.send_keys(ss)
            waiting_sys_timer(wait, 5)
            # Find an element that is not part of the datepicker and click on it to close the datepicker
            banner_element = driver.find_element(By.XPATH, "//img[@id='the_banner']")
            banner_element.click()
            num_genomes = driver.find_element(By.CSS_SELECTOR, "div.sys-datatable-info-left span")
            logging.info("{}...".format(num_genomes.text))

        if se:
            logging.info("Setting submissions end date...")
            se_input = date_inputs[3] # 3rd input is the submission end date
            se_input.send_keys(se)
            waiting_sys_timer(wait, 5)
            # Find an element that is not part of the datepicker and click on it to close the datepicker
            banner_element = driver.find_element(By.XPATH, "//img[@id='the_banner']")
            banner_element.click()
            num_genomes = driver.find_element(By.CSS_SELECTOR, "div.sys-datatable-info-left span")
            logging.info("{}...".format(num_genomes.text))

        # set variant
        if voc:
            logging.info("Setting variant...")
            voc_input = driver.find_element(By.XPATH, '//div[text()="Variant"]/./following-sibling::div//select')
            voc_select = Select(voc_input)
            options = voc_select.options
            for option in options:
                if option.get_attribute('value') == voc:
                    option.click()
                    logging.info("Selected {}...".format(option.text))
                    break
            waiting_sys_timer(wait, 5)
            num_genomes = driver.find_element(By.CSS_SELECTOR, "div.sys-datatable-info-left span")
            logging.info("{}...".format(num_genomes.text))

        # complete genome only
        if cg:
            logging.info("Complete genome only...")
            checkbox = driver.find_element(By.XPATH, '//input[@value="complete"]')
            checkbox.click()
            waiting_sys_timer(wait)
            num_genomes = driver.find_element(By.CSS_SELECTOR, "div.sys-datatable-info-left span")
            logging.info("{}...".format(num_genomes.text))

        # high coverage only
        if hc:
            logging.info("High coverage only...")
            checkbox = driver.find_element(By.XPATH, '//input[@value="highq"]')
            checkbox.click()
            waiting_sys_timer(wait)
            num_genomes = driver.find_element(By.CSS_SELECTOR, "div.sys-datatable-info-left span")
            logging.info("{}...".format(num_genomes.text))

        # excluding low coverage
        if le:
            logging.info("Low coverage excluding...")
            checkbox = driver.find_element(By.XPATH, '//input[@value="lowco"]')
            checkbox.click()
            waiting_sys_timer(wait)
            num_genomes = driver.find_element(By.CSS_SELECTOR, "div.sys-datatable-info-left span")
            logging.info("{}...".format(num_genomes.text))

        # check if any genomes pass filters
        warning_message = None
        try:
            warning_message = driver.find_element(By.XPATH, "//div[contains(text(), 'No data found.')]")
        except:
            pass
        if warning_message:
            logging.info("No data found.")
            sys.exit(1)

        # select all genomes
        select_all_checkbox = driver.find_element(By.CSS_SELECTOR, "span.yui-dt-label input")
        select_all_checkbox.click()
        waiting_sys_timer(wait)

        try:
            logging.info("Downloading sequences for selected genomes...")
            button = driver.find_element(By.XPATH, "//button[contains(text(), 'Download')]")
            button.click()
            waiting_sys_timer(wait)

            # switch to iframe
            logging.info("Switching to data selection iframe...")
            iframe = waiting_for_iframe(wait, driver, rt, iv)
            driver.switch_to.frame(iframe)
            waiting_sys_timer(wait)

            # selecting options
            # labels = driver.find_elements(By.XPATH, "//label")
            # num_download_options = len(labels)
            # labels[current_option].click()
            # current_option += 1

            logging.info("Selecting FASTA files...")
            select_fasta = driver.find_element(By.XPATH, "//label[contains(text(),'Nucleotide Sequences (FASTA)')]/../input")
            select_fasta.click()
            waiting_sys_timer(wait)

            logging.info("Clicking download button...")
            download_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Download')]")
            download_btn.click()
            waiting_sys_timer(wait)

            # switch back to default page and then to agreement iframe
            logging.info("Switching back to default page...")
            driver.switch_to.default_content()
            logging.info("Switching to agreement iframe...")
            iframe = waiting_for_iframe(wait, driver, rt, iv)
            driver.switch_to.frame(iframe)
            waiting_sys_timer(wait)

            logging.info("Accepting terms of use...")
            agree_checkbox = driver.find_element(By.XPATH, "//span[contains(text(),'I agree to the terms and conditions')]/../input")
            agree_checkbox.click()
            waiting_sys_timer(wait)

            logging.info("Clicking download button again...")
            download_btn_2 = driver.find_element(By.XPATH, "//button[contains(text(), 'Download')]")
            download_btn_2.click()
            waiting_sys_timer(wait)

            logging.info("Switching back to default page...")
            driver.switch_to.default_content()

            fn = wait_downloaded_filename(wait, driver, 1800)
            logging.info(f"Downloaded to {fn}.")
        except:
            logging.error("Unexpected error:", sys.exc_info())
            sys.exit(1)

    # close driver
    driver.quit()


def getMetadata(record_elem):
    """parse out metadata from the table"""
    meta = {}
    table = record_elem.find_element(By.TAG_NAME, "table")
    last_attr = ""
    for tr in table.find_elements(By.TAG_NAME, "tr"):
        if tr.get_attribute("colspan") == "2":
            # skip titles
            continue
        else:
            tds = tr.find_elements(By.TAG_NAME, "td")
            if len(tds) == 2:
                attr = tds[0].text.strip(":")
                val = tds[1].text
                if attr == "Address":
                    attr = f"{last_attr} {attr.lower()}"
                    if attr == "Submission Date address":
                        attr = "Submitter address"
                meta[attr] = val
                last_attr = attr
    return meta


def waiting_sys_timer(wait, sec=1):
    """wait for system timer"""
    try:
        wait.until(EC.invisibility_of_element_located(
            (By.XPATH,  "//div[@id='sys_timer']")))
    except:
        pass
    time.sleep(sec)


def waiting_table_to_get_ready(wait, sec=1):
    """wait for the table to be loaded"""
    wait.until(EC.invisibility_of_element_located(
        (By.XPATH,  "//tbody[@class='yui-dt-message']")))
    time.sleep(sec)

def waiting_for_iframe(wait, driver, rt, iv):
    iframe = None
    retry = 1
    while retry <= rt:
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//iframe")))
            iframe = driver.find_element(By.XPATH, "//iframe")
            if iframe:
                return iframe
            else:
                raise
        except:
            logging.info(f"retrying...#{retry} in {iv} sec(s)")
            if retry == rt:
                logging.info("Failed")
                sys.exit(1)
            else:
                time.sleep(iv)
                retry += 1

def wait_downloaded_filename(wait, driver, waitTime=180):
    # logging.info(f"Opening Firefox downloading window...")
    driver.execute_script("window.open()")
    wait.until(EC.new_window_is_opened)
    driver.switch_to.window(driver.window_handles[-1])
    driver.get("about:downloads")
    time.sleep(1)

    endTime = time.time()+waitTime
    while True:
        try:
            #progress = driver.execute_script("return document.querySelector('.downloadContainer progress:first-of-type').value")
            fileName = driver.execute_script("return document.querySelector('.downloadContainer description:first-of-type').value")
            dldetail = driver.execute_script("return document.querySelector('.downloadDetailsNormal').value")

            while "time left" in dldetail:
                time.sleep(1)
                dldetail = driver.execute_script("return document.querySelector('.downloadDetailsNormal').value")
                #progress = driver.execute_script("return document.querySelector('.downloadContainer progress:first-of-type').value")

            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(2)
            return fileName
        except:
            pass
        time.sleep(1)
        if time.time() > endTime:
            break


def main():
    argvs = parse_params()

    if argvs.version:
        print(f"v{__version__}")
        exit(0)
    else:
        if not argvs.username or not argvs.password:
            logging.error("error: the following arguments are required: -u/--username, -p/--password")
            exit(1)

    logging.info(f"GISAID EpiCoV Utility v{__version__}")
    download_gisaid_EpiCoV(
        argvs.username,
        argvs.password,
        argvs.normal,
        argvs.outdir,
        argvs.location,
        argvs.host,
        argvs.colstart,
        argvs.colend,
        argvs.substart,
        argvs.subend,
        argvs.variant,
        argvs.complete,
        argvs.highcoverage,
        argvs.lowcoverageExcl,
        argvs.timeout,
        argvs.retry,
        argvs.interval,
        argvs.nonextstraindata,
        argvs.ffbin
    )
    logging.info("Completed.")


if __name__ == "__main__":
    main()
