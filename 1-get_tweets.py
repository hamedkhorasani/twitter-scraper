from urllib.parse import unquote
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire import webdriver as wiredriver
from seleniumwire.utils import decode as sw_decode
from datetime import datetime
import time
import json
import pytz
import pymysql
from datetime import datetime
from random import randrange
import pprint

# db config
# host = "localhost"
# user = "root"
# password = ""
# database = "challenge"
host = "####"
user = "####"
password = "####"
database = "####"

needLogin = True
timeToOpenWebsite = 8
timeToLoadReply = 8
timeToLogin = 5

username = "elonmusk"
startDate = "2023-02-01"
endDate = "2023-03-01"

startDate = datetime.fromisoformat(startDate)
endDate = datetime.fromisoformat(endDate)
utc = pytz.UTC
startDate = utc.localize(startDate)
endDate = utc.localize(endDate)

# mysql connection
conn = pymysql.connect(host=host, port=3306, user=user, password=password, database=database)

# mysql cursor
cursor = conn.cursor()

queueColumns = [
    'conversation_id',
    'date',
    'parent_conversation',
]

# db queries
sqlInsertQueue = f"INSERT INTO queue ({','.join(queueColumns)}) VALUES (%s, %s, NULL)"
sqlExistsQueue = f"Select id from queue where conversation_id = '%s'"
sqlQueue = f"Select conversation_id from queue where done!='1' and parent_conversation is null limit 1"

# load wiredriver
options = wiredriver.ChromeOptions()
options.add_argument("user-data-dir=C:\\Users\\HR-Dev\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 1") #Path to your chrome profile
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('desired_capabilities=capabilities')
# options.add_argument("--headless")

# read jsons in file
# save unique users and unique tweets to db
def saveDataToDb(startDate, endDate):
    with open('responses.json', 'r', encoding="utf-8") as file:
        for index, jsonObj in enumerate(file):
            dict = json.loads(jsonObj)
            instructions = dict["user"]["result"]["timeline_v2"]["timeline"]["instructions"]
            for instruction in instructions:
                if instruction['type'] == "TimelineAddEntries":
                    items = instruction["entries"]

                    for item in items:
                        item = item['content']
                        if item['entryType'] == "TimelineTimelineItem":

                            itemContent = item['itemContent']

                            if itemContent['itemType'] == "TimelineTweet":

                                #refrence user.json
                                user = itemContent['tweet_results']['result']['core']['user_results']['result']

                                #refrence tweet.json
                                tweet = itemContent['tweet_results']['result']['legacy']


                                if user["legacy"]["screen_name"] == username and tweet.get("retweeted_status_result", "empty44") == "empty44":
                                    # if user["legacy"]["screen_name"] == username:

                                    datetime_object = tweet['created_at']
                                    datetime_object = datetime.strptime(str(datetime_object), '%a %b %d %H:%M:%S %z %Y')

                                    # if str(tweet['id_str']) == "1625936009841213440":
                                    #     print(datetime_object)
                                    #     print(str(datetime_object.replace(tzinfo=None)))
                                    # print(datetime_object)
                                    # print(startDate <= datetime_object < endDate)
                                    # raise Exception("sss")

                                    if startDate <= datetime_object < endDate:
                                        # add to db:queue
                                        # if not exists then save it
                                        cursor.execute(sqlExistsQueue % conn.escape_string(str(tweet['id_str'])))
                                        resultQueue = cursor.fetchone()
                                        if not resultQueue:
                                            datetime_object = datetime_object.replace(tzinfo=None)
                                            values = (str(tweet['id_str']), str(datetime_object))
                                            cursor.execute(sqlInsertQueue, values)

                            # else
                            # item['entryType'] = 'TimelineTimelineCursor'

                        elif item['entryType']=="TimelineTimelineModule":
                            for moduleItems in item["items"]:
                                moduleItems = moduleItems["item"]
                                itemContent = moduleItems["itemContent"]

                                if itemContent['itemType'] == "TimelineTweet":
                                    #refrence user.json
                                    user = itemContent['tweet_results']['result']['core']['user_results']['result']

                                    #refrence tweet.json
                                    tweet = itemContent['tweet_results']['result']['legacy']

                                    if user["legacy"]["screen_name"] == username and tweet.get("retweeted_status_result", "empty44") == "empty44":
                                    # if user["legacy"]["screen_name"] == username:

                                        datetime_object = tweet['created_at']
                                        datetime_object = datetime.strptime(str(datetime_object),'%a %b %d %H:%M:%S %z %Y')

                                        # if str(tweet['id_str']) == "1625936009841213440":
                                        #     print(datetime_object)
                                        #     print(str(datetime_object))

                                        if startDate <= datetime_object < endDate:
                                            cursor.execute(sqlExistsQueue % conn.escape_string(str(tweet['id_str'])))
                                            resultQueue = cursor.fetchone()
                                            if not resultQueue:
                                                datetime_object = datetime_object.replace(tzinfo=None)
                                                values = (str(tweet['id_str']), str(datetime_object))
                                                cursor.execute(sqlInsertQueue, values)


                                #else:
                                    #itemContent['itemType'] = "TimelineTimelineCursor"

def loginToTwitter(driver, loggedIn = False):

    if needLogin:
        cookies = driver.get_cookies()
        cookies = ''.join(str(cookies))
        if cookies.find("auth_token") == -1:
            loggedIn = True
            # wait for login
            if 'login' not in driver.current_url:
                driver.get('https://twitter.com/login')

            time.sleep(timeToLogin)
            return loginToTwitter(driver)

        if loggedIn:
            return True
        else:
            return False

    return False

def page_has_loaded(driver):
    try:
        driver.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
        return True
    except NoSuchElementException:
        return False

def openWebsite(driver, url, count = 0):
    try:
        # if count == 0:
           # if not internet_on():
           #     raise Exception('Err 1: Check internet connection, maybe vpn not working')
        if count == 0:
            driver.get(url)

        time.sleep(timeToOpenWebsite)

        if count > 3:
            raise Exception('Err 2: Check internet connection, maybe vpn not working')

        # not work if browser cached website
        if not page_has_loaded(driver):
            print('page loaded but not ready')
            count = count + 1
            openWebsite(driver, url, count)

    except TimeoutException:
        print('timeout')
        count = count + 1
        openWebsite(driver, url, count)
    #
    # except Exception as ex:
    #     print(ex)
    #     return False

def button_show(driver):

    try:
        show_element = driver.find_element(By.XPATH, '//span[text()="Show"]')

        if show_element:
            # Clicking the "Show" element

            # show_element.click()
            # wait = WebDriverWait(driver, 10)
            # wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="Show"]')))
            driver.execute_script('var aTags = document.getElementsByTagName("span");var searchText = "Show";var found;for (var i = 0; i < aTags.length; i++) { if (aTags[i].textContent == searchText) {found = aTags[i];found.click();break;}}')

            time.sleep(timeToLoadReply)
            button_show(driver)

    except NoSuchElementException:
        print("Show not found")

    try:
        show_more_element = driver.find_element(By.XPATH, '//span[text()="Show more replies"]')
        if show_more_element:
            print("shor more reply found")
            # Clicking the "Show" element
            driver.execute_script('var aTags1 = document.getElementsByTagName("span");var searchText1 = "Show more replies";var found1;for (var i = 0; i < aTags1.length; i++) { if (aTags1[i].textContent == searchText1) {found1 = aTags1[i];found1.click();break;}}')
            # wait = WebDriverWait(driver, 10)
            # wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="Show more replies"]')).click())

            time.sleep(timeToLoadReply)
            button_show(driver)

    except NoSuchElementException:
        print("Show not found")

# open tweet and repeat scroll to bottom until scroll end
# then read general API response
# save json data in file
def scrapeFromWebsite():

    driver = wiredriver.Chrome(options=options)

    openWebsite(driver, 'https://twitter.com/' + str(username))

    if loginToTwitter(driver):
        print('logged in, please re-run me')
        return False

    i = 0
    # scroll to bottom until end loading
    while True:
        # scroll to next page
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

        # click if page had "show" and "show_more" button
        button_show(driver)

        # click if page had "show more reply" button
        # button_show_more_replies(driver)

        # wait 15-20 second then re scroll
        time.sleep(randrange(10, 15))

        # print(driver.execute_script('return window.innerHeight + window.pageYOffset'))
        # print(driver.execute_script('return document.body.scrollHeight'))
        # print('\n \n')
        i = i + 1
        if i > 10:
            break

        # check is end of page or not
        if driver.execute_script('return window.innerHeight + window.pageYOffset') >= driver.execute_script('return document.body.scrollHeight'):
            break


    # access to requests send to server
    # read self API result
    # save result in the file
    with open('responses.json', 'w', encoding="utf-8") as f:
        for request in driver.requests:
            if request.response:
                if 'UserTweets' in request.path:
                    data = sw_decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
                    data = data.decode("utf8")
                    data = json.loads(data)
                    f.write(str(json.dumps(data["data"])) + '\n')

    driver.quit()


scrapeFromWebsite()
saveDataToDb(startDate, endDate)

# commit and close db
conn.commit()
conn.close()
