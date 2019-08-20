#Top HN Tweet Bot Project
import tweepy
import json
import requests
import time
from os import environ

#authorize the bot to use the Twitter API
CONSUMER_KEY = environ['CONSUMER_KEY']
CONSUMER_SECRET = environ['CONSUMER_SECRET']
ACCESS_KEY = environ['ACCESS_KEY']
ACCESS_SECRET = environ['ACCESS_SECRET']

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)

#API object whose methods invoke Twitter API's endpoints for things like tweeting, liking, etc.
api = tweepy.API(auth)

try:
    api.verify_credentials()
    print("Authentication OK")
    
except:
    print("Error during authentication")

#current top story id on HN
top_hn_id = None

#set of top story ids used later on
id_set = set()

#timeout interval of 10 minutes to test
INTERVAL = 60*10

#HN Firebase API URL 
HN_API_BASE = "https://hacker-news.firebaseio.com/v0/"

#HN Website Base URL
HN_BASE = "https://news.ycombinator.com/"

#loop that will run every 10 minutes
while True:
    response = requests.get(HN_API_BASE + "topstories.json")
    #first time running
    if(top_hn_id == None):
        top_hn_ids = response.text.replace('[', '').replace(']', '').split(sep=',')

        #first story in list of 500 top stories
        top_hn_id = int(top_hn_ids[0])
        
        #add story id to set, disqualifying it from appearing again
        id_set.add(top_hn_id)

        #actual JSON content of story associated with ID
        response = requests.get(HN_API_BASE + "/item/{}.json".format(top_hn_id))
        top_story = json.loads(response.text)
        
        #tweet about top story
        status = "Poster: {}\nTitle: {}\nURL: {}".format(top_story['by'], top_story['title'], HN_BASE + "item?id=" + str(top_story['id']))
        try:
            api.update_status(status)
            print("Top HN ID: {} Post: {}".format(str(top_hn_id), status))
        except tweepy.TweepError:
            print("Tweet was a duplicate and was not posted")
    else:
        current_hn_ids = response.text.replace('[', '').replace(']', '').split(sep=',')

        #first story in list of 500 top stories
        current_hn_id = int(current_hn_ids[0])

        #tweet with updated top post
        if(current_hn_id not in id_set):

            id_set.add(current_hn_id)
            response = requests.get(HN_API_BASE + "/item/{}.json".format(current_hn_id))
            current_story = json.loads(response.text)

            #tweet here
            status = "New top story!\nPoster: {}\nTitle: {}\nURL: {}".format(current_story['by'], current_story['title'], HN_BASE + "item?id=" + str(current_story['id']))
            try:
                api.update_status(status)
                print("Top HN ID: {} Current HN ID: {} Post: {}".format(str(top_hn_id), str(current_hn_id), status))
            except tweepy.TweepError:
                print("Tweet was a duplicate and was not posted")
        else:
            print("Previous top story is still ranked #1! Top HN ID: {} Current HN ID: {}".format(str(top_hn_id), str(current_hn_id)))
    time.sleep(INTERVAL)