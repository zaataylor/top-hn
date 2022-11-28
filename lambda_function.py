# Top HN Tweet Bot Project
import tweepy
import requests
import boto3

from os import environ

# HN Firebase API URL 
HN_API_BASE = "https://hacker-news.firebaseio.com/v0/"

# HN Website Base URL
HN_BASE = "https://news.ycombinator.com/"

# Authorize bot to use the Twitter API
CONSUMER_KEY = environ['CONSUMER_KEY']
CONSUMER_SECRET = environ['CONSUMER_SECRET']
ACCESS_KEY = environ['ACCESS_KEY']
ACCESS_SECRET = environ['ACCESS_SECRET']

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)

# API object to invoke Twitter API's endpoints
api = tweepy.API(auth)

try:
    api.verify_credentials()
    print("Authentication OK") 
except Exception as e:
    print(f"Error during authentication: {e}")
    exit(1)


#### Runs every 30 minutes ####
def lambda_handler(event, context):
    print("Inside lambda handler")
    # Instantiate DynamoDB Client
    client = boto3.client(
        "dynamodb", 
        region_name="us-east-1",
        aws_session_token=environ['AWS_SESSION_TOKEN']
    )
    print("instantiated dynamodb client")
    DYNAMO_DB_TABLE="top-hn"
    print(f"Event: {event}")
    print(f"Environ: {environ}")
    print(f"client object: {client}")
    
    # Get ID of top post
    top_posts_response = requests.get(HN_API_BASE + "topstories.json")
    top_hn_id = top_posts_response.json()[0]

    # Check DB to see if post is already present
    response = client.get_item(
        TableName=DYNAMO_DB_TABLE,
        Key={
            "hn_id": {
                "N": f"{top_hn_id}"
            }
        }
    )

    # If present, exit early
    if response.get('Item', None) != None:
        return

    # Else, tweet
    # Get JSON of post associated with ID
    top_post_response = requests.get(HN_API_BASE + f"/item/{top_hn_id}.json")
    top_post_json = top_post_response.json()
    poster, title, url = top_post_json['by'], top_post_json['title'], HN_BASE + f"item?id={top_hn_id}"

    status = f"New top story!\nPoster: {poster}\nTitle: {title}\nURL: {url}"
    tweet_id = None
    try:
        # Tweet
        status_response = api.update_status(status)
        tweet_id = status_response['id']
        print(f"Tweeted status:\n{status}")
    except Exception as e:
        print(f"Error posting tweet! Error was: {e}")
        exit(1)

    # Add the HN ID-Tweet ID key-value pair 
    # as an item to the DynamoDB table
    item = {
                "hn_id": {"N": f"{top_hn_id}"},
                "tweet_id": {"N": f"{tweet_id}"}
            }
    try:
        client.put_item(
            TableName=DYNAMO_DB_TABLE,
            Item = item
        )
    except Exception as e:
        print(f"Error adding Item {item}. Error was: {e}")
        exit(1)

    return