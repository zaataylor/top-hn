import json
import os

import tweepy
import requests
import psycopg2


# Authorize bot to use the Twitter API
CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
ACCESS_KEY = os.getenv("ACCESS_KEY")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

try:
    if api.verify_credentials():
        print("Authentication OK")
    else:
        print("Authentication failed. Exiting now.")
        exit(1)
except tweepy.TweepError as e:
    print("Tweepy error during authentication: \n\tReason:{}" + 
        "\n\tResponse:{}\n\tAPI Code: {}".format(e.reason, e.response, e.api_code))
    exit(1)

# DB Connection Setup
DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL, sslmode="require")

# HN-related Details 
HN_API_BASE = "https://hacker-news.firebaseio.com/v0/"
HN_SITE_BASE = "https://news.ycombinator.com/"

top_post_ids = requests.get(HN_API_BASE + "topstories.json")
top_post_id = top_post_ids.json()[0]
        
# DB logic checks the ID against existing IDs
new_story = False
with conn.cursor() as curs:
    SQL = "SELECT * FROM hnposts WHERE postid = %s;"
    data = (top_post_id, )
    curs.execute(SQL, data)
    result = curs.fetchone()
    if result is None:
        new_story = True
    else:
        new_story = False

if new_story:
    # Content of story associated with ID
    story_raw = requests.get(HN_API_BASE + "/item/{}.json".format(top_post_id))
    story = json.loads(story_raw.text)
    user_id = story["by"]
    title = story["title"]

    # Insert new post information, then close connection
    with conn.cursor() as curs:
        SQL = "INSERT INTO hnposts (postid, userid, title) VALUES (%s, %s, %s);"
        data = (top_post_id, user_id, title)
        curs.execute(SQL, data)
        conn.commit()
        conn.close()
    
    # Tweet top story
    status = "New top story!\nPoster: {}\nTitle: {}\nURL: {}".format(user_id,
                                                                    title,
                                                                    HN_SITE_BASE + "item?id=" + str(top_post_id))
    try:
        api.update_status(status)
        print("HN ID: {} Post: {}".format(str(top_hn_id), status))
    except tweepy.TweepError as e:
        print("Tweepy error when tweeting: \n\tReason:{}" + 
            "\n\tResponse:{}\n\tAPI Code: {}".format(e.reason, e.response, e.api_code))
else:
    pass
