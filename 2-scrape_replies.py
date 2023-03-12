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
import time
import json
import pymysql
import pprint
from datetime import datetime
from random import randrange
from urllib.request import urlopen, HTTPError, URLError

# db config
host = "####"
user = "####"
password = "####"
database = "####"

needLogin = True
timeToOpenWebsite = 8
timeToLoadReply = 4
timeToLogin = 5

# mysql connection
conn = pymysql.connect(host=host, port=3306, user=user, password=password, database=database)

# mysql cursor
cursor = conn.cursor()

userColumns = [
    'id_str',
    'name',
    'screen_name',
    'description',
    'is_blue_verified',
    'normal_followers_count',
    'followers_count',
    'media_count',
    'friends_count',
    'verified',
    'want_retweets',
    'profile_banner_url',
    'profile_image_url_https',
    'url',
    'location',
    'created_at',
]

tweetColumns = [
    'id_str',
    'user_id',
    'user_id_str',
    'conversation_id_str',
    'full_text',
    'in_reply_to_screen_name',
    'in_reply_to_status_id_str',
    'in_reply_to_user_id_str',
    'quote_count',
    'reply_count',
    'retweet_count',
    'favorite_count',
    'retweeted',
    'lang',
    'created_at',
    'level',
]

queueColumns = [
    'conversation_id',
    'date',
    'parent_conversation',
]

userTweetColumns = [
    'tweet_id',
    'user_id',
    'count',
]

# db queries
sqlInsertQueue = f"INSERT INTO queue ({','.join(queueColumns)}) VALUES (%s, %s, %s)"
sqlExistsQueue = f"Select id from queue where conversation_id = '%s'"
sqlQueue = f"Select conversation_id from queue where done!='1' and parent_conversation is null limit 1"

sqlInsertUser = f"INSERT INTO twitter_users ({','.join(userColumns)}) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
sqlExistsUser = f"Select * from twitter_users where id_str ='%s'"

sqlInsertTweet = f"INSERT INTO tweets ({','.join(tweetColumns)}) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
sqlExistsTweet = f"Select id_str from tweets where id_str ='%s'"

sqlExistsUserTweet = f"Select * from tweet_user where user_id = '%s' and tweet_id = '%s'"
sqlInsertUserTweet = f"INSERT INTO tweet_user ({','.join(userTweetColumns)}) VALUES (%s, %s, %s)"
sqlUpdateUserTweet = f"Update tweet_user set count='%s' where tweet_id = '%s' and user_id = '%s'"

# load wiredriver
options = wiredriver.ChromeOptions()
options.add_argument("user-data-dir=C:\\Users\\HR-Dev\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 1") #Path to your chrome profile
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('desired_capabilities=capabilities')
# options.add_argument("--headless")


# read jsons in file
# save unique users and unique tweets to db
def extractAndSave(level):
    with open('responses.json', 'r', encoding="utf-8") as file:
        for index, jsonObj in enumerate(file):
            dict = json.loads(jsonObj)

            instructions = dict["threaded_conversation_with_injections_v2"]["instructions"]
            for instruction in instructions:
                if instruction['type'] == "TimelineAddEntries":
                    items = instruction["entries"]

                    # items = dict["threaded_conversation_with_injections_v2"]["instructions"][0]["entries"]
                    for item in items:
                        item = item['content']
                        if item['entryType'] == "TimelineTimelineItem":

                            itemContent = item['itemContent']

                            if itemContent['itemType'] == "TimelineTweet":

                                #reference user.json
                                result = itemContent['tweet_results']['result']

                                if not result['__typename'] == 'Tweet':
                                    continue

                                user = result['core']['user_results']['result']

                                # reference tweet.json
                                tweet = result['legacy']

                                saveToDb(user, tweet, 0)
                            # else
                            # item['entryType'] = 'TimelineTimelineCursor'

                        elif item['entryType']=="TimelineTimelineModule":
                            for moduleItems in item["items"]:
                                moduleItems = moduleItems["item"]
                                itemContent = moduleItems["itemContent"]

                                if itemContent['itemType'] == "TimelineTweet":
                                    #reference user.json
                                    result = itemContent['tweet_results']['result']

                                    if not result['__typename'] == 'Tweet':
                                        continue

                                    user = result['core']['user_results']['result']

                                    #reference tweet.json
                                    tweet = result['legacy']

                                    saveToDb(user, tweet, level)

                                    if tweet['reply_count'] > 0:
                                        # has reply
                                        # add to queue

                                        # has replies, then add items to queue list
                                        cursor.execute(sqlExistsQueue % conn.escape_string(str(tweet['id_str'])))
                                        resultQueue = cursor.fetchone()
                                        if not resultQueue:
                                            datetime_object = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S %z %Y')
                                            values = (str(tweet['id_str']), str(datetime_object), str(tweet['conversation_id_str']))
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



# def button_show_more_replies(driver, clicked = False):
#
#     try:
#         show_element = driver.find_element(By.XPATH, '//span[text()="Show more replies"]')
#         if show_element:
#             # Clicking the "Show" element
#             if not clicked:
#                 driver.execute_script('var aTags = document.getElementsByTagName("span");var searchText = "Show more replies";var found;for (var i = 0; i < aTags.length; i++) { if (aTags[i].textContent == searchText) {found = aTags[i];found.click();break;}}')
#                 # wait = WebDriverWait(driver, 10)
#                 # wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="Show more replies"]')).click())
#                 clicked = True
#             time.sleep(timeToLoadReply)
#             button_show_more_replies(driver, clicked)
#
#     except NoSuchElementException:
#         print("Show reply not exists")

def page_has_loaded(driver):

    try:
        driver.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
        return True
    except NoSuchElementException:
        return False


# def internet_on():
#     try:
#         urlopen("https://www.twitter.com/")
#     except HTTPError as e:
#         print('HTTP Error code: ', e.code)
#         return False
#     except URLError as e:
#         print('URL Error: ', e.reason)
#         return False
#     else:
#         return True

def openWebsite(driver, url, count = 0):
    try:
        # if count == 0:
           # if not internet_on():
           #     raise Exception('Err 1: Check internet connection, maybe vpn not working')
        if count == 0:
            driver.get(url)

        time.sleep(timeToOpenWebsite)

        if count > 5:
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



# open tweet and repeat scroll to bottom until scroll end
# then read general API response
# save json data in file
def scrapeFromWebsite(results):

    driver = wiredriver.Chrome(options=options)


    for index, item in enumerate(results):

        conversationId = item[0]

        openWebsite(driver, 'https://twitter.com/p/status/'+str(conversationId))

        if loginToTwitter(driver):
            print('logged in')
            break

        # scroll to bottom every 15 second
        # for i in range(2):
        #    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        #    time.sleep(15)

        # scroll to bottom until end loading
        while True:
            # scroll to next page
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

            # click if page had "show" and "show_more" button
            button_show(driver)

            # click if page had "show more reply" button
            # button_show_more_replies(driver)

            # wait 15-20 second then re scroll
            time.sleep(randrange(10,15))

            # print(driver.execute_script('return window.innerHeight + window.pageYOffset'))
            # print(driver.execute_script('return document.body.scrollHeight'))
            # print('\n \n')

            # check is end of page or not
            if (driver.execute_script('return window.innerHeight + window.pageYOffset') + 80) >= driver.execute_script('return document.body.scrollHeight'):
                break

        # access to requests send to server
        # read self API result
        # save result in the file
        with open('responses.json', 'w', encoding="utf-8") as f:
            for request in driver.requests:
                if request.response:
                    if 'TweetDetail' in request.path:
                        data = sw_decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
                        data = data.decode("utf8")
                        data = json.loads(data)
                        f.write(str(json.dumps(data["data"])) + '\n')

        # update queue item as done
        sqlUpdateQueue = f"update queue set done=1 where conversation_id=%s"
        values = (str(conversationId))
        cursor.execute(sqlUpdateQueue, values)

        driver.quit()

def insertTweet(values):
    cursor.execute(sqlInsertTweet, values)
    tweetId = cursor.lastrowid
    return tweetId

def insertUser(values):
    cursor.execute(sqlInsertUser, values)
    userId = cursor.lastrowid
    userIdStr = str(values[0])
    return {
        'userId': userId,
        'userIdStr': userIdStr,
    }

def addUserTweetCount(values):
    print(values)
    userId = values['userId']
    tweetId = values['tweetId']

    cursor.execute(sqlExistsUserTweet % (conn.escape_string(userId), conn.escape_string(tweetId)))
    resultTweetUser = cursor.fetchone()

    if resultTweetUser:
        # should add count then update
        count = resultTweetUser[2]
        count = count + 1

        cursor.execute(sqlUpdateUserTweet % (str(count), str(tweetId), str(userId)))
    else:
        # should insert record
        cursor.execute(sqlInsertUserTweet % (str(tweetId), str(userId), '1'))

def userExists(userId):
    # check user exists, if not exists then create user
    cursor.execute(sqlExistsUser % conn.escape_string(userId))
    resultUser = cursor.fetchone()
    return resultUser


def saveToDb(user, tweet, level):

    tweetId = 0

    resultUser = userExists(user['rest_id'])

    if resultUser:
        userId = resultUser[0]
        userIdStr = resultUser[1]
    else:
        legacy = user['legacy']
        datetime_object = datetime.strptime(str(legacy.get('created_at', '')), '%a %b %d %H:%M:%S %z %Y')
        values = (
            str(user['rest_id']),
            str(legacy.get('name', '')),
            str(legacy.get('screen_name', '')),
            str(legacy.get('description', '')),
            str(legacy.get('is_blue_verified', 0)),
            str(legacy.get('normal_followers_count', 0)),
            str(legacy.get('followers_count', 0)),
            str(legacy.get('media_count', 0)),
            str(legacy.get('friends_count', 0)),
            str(legacy.get('verified', 0)),
            str(legacy.get('want_retweets', 0)),
            str(legacy.get('profile_banner_url', '')),
            str(legacy.get('profile_image_url_https', '')),
            str(legacy.get('url', '')),
            str(legacy.get('location', '')),
            str(datetime_object),
        )
        inserted = insertUser(values)
        userId = inserted['userId']
        userIdStr = user['rest_id']

    cursor.execute(sqlExistsTweet % conn.escape_string(str(tweet['id_str'])))
    resulTweet = cursor.fetchone()
    if not resulTweet:
        datetime_object = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S %z %Y')

        values = (
            str(tweet['id_str']),
            str(userId),
            str(userIdStr),
            str(tweet['conversation_id_str']),
            str(tweet['full_text']),
            str(tweet.get('in_reply_to_screen_name', '')),
            str(tweet.get('in_reply_to_status_id_str', '')),
            str(tweet.get('in_reply_to_user_id_str', '')),
            str(tweet.get('quote_count', 0)),
            str(tweet.get('reply_count', 0)),
            str(tweet.get('retweet_count', 0)),
            str(tweet.get('favorite_count', 0)),
            str(tweet.get('retweeted', 0)),
            str(tweet.get('lang', '')),
            str(datetime_object),
            str(level),
        )

        # insert tweet
        tweetId = insertTweet(values)

        # updateOrCreate user
        values = dict(
            userId = str(userId),
            tweetId = str(tweetId),
        )
        addUserTweetCount(values)


    return {
        'userId': userId,
        'tweetId': tweetId
    }


# new file
# open('responses.json', 'w').close()
level = 0
# todo 0

while True:
    cursor.execute(sqlQueue)
    resultQueue = cursor.fetchall()
    if not resultQueue:
        print('Finished fetch')
        break

    # todo shoud remove condition
    # if level > 0:
    scrapeFromWebsite(resultQueue)

    extractAndSave(level)
    level = level + 1

    # sqlQueue = f"Select conversation_id from queue where done!='1' and parent_conversation IS NOT NULL limit 1"

# commit and close db
conn.commit()
conn.close()
