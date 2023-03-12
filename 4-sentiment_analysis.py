from textblob import TextBlob
import pymysql
from googletrans import Translator

# db config
host = "162.55.1.104"
user = "domatk_challenge"
password = "rdyrH2Li"
database = "domatk_challenge"

# mysql connection
conn = pymysql.connect(host=host, port=3306, user=user, password=password, database=database)

# mysql cursor
cursor = conn.cursor()

sqlTweets = f"-- Select id, full_text, sentiment from tweets where sentiment is null"
sqlTweets = f"Select id, full_text, sentiment from tweets"
sqlUpdateTweet = f"update tweets set sentiment=%s where id=%s"

sqlUsers = f"Select * from twitter_users where id_str ='%s'"
translator = Translator()

cursor.execute(sqlTweets)
resultTweets = cursor.fetchall()

if resultTweets:
    for item in resultTweets:
        # todo must check
        id = item[0]
        comment = item[1]

        comment = translator.translate(str(comment), dest='en').text

        blob = TextBlob(comment)
        polarity = blob.sentiment.polarity

        # update tweet
        values = (str(polarity), str(id))
        print(values)
        cursor.execute(sqlUpdateTweet, values)



