## Project Title:
Twitter scraper

## Project Description:
The Twitter scraper project is divided into four stages for extracting tweets:
- In the first stage, we open the user's page and read the tweets from the Twitter API, and add them to the queue table in the database.
- In the second stage, we iterate over the queue and read each tweet and its level 0 replies, and add them to the tweets table in the database. Whenever a tweet with replies is added to the tweets table, we add it to the queue table as well.
Note: The first item of each tweet is the original tweet. From the second index onward, they are the replies to that tweet.
- In the third stage, we iterate over the queue again and extract nested replies and add them to the tweets table.
- In the fourth stage, we read each reply from the tweets table and calculate the sentiment analysis on each tweet.

## Requirements:
### Install the following libraries:
```
textblob
selenium
selenium-wire
pymysql
urllib.parse
```

## How to use
To use the software, you need to install the MySQL database on your system.
Import the project's database file into MySQL.
Enter the database connection information in the config section of each file, for example:
```
host = "localhost"
user = "xxxxx"
password = "xxxxx"
database = "xxxxx "
```

To extract tweets, open the 1-get_tweets.py file and enter the "Twitter username" in the username variable.

After that, you can run the first stage of the program.
```
Python 1-get_tweets.py
```

After completing the first stage, you can extract level 0 replies.
```
Python 2-scrape_replies.py
```

After completing the second stage, you can extract n-level replies.
```
Python 3-scrape_recursive_replies.py
```

Then you can perform sentiment analysis.
```
Python 4-sentiment_analysis.py
```

Note: Due to the limited access of the Twitter API, you can run the second stage multiple times and then proceed to the third stage.
