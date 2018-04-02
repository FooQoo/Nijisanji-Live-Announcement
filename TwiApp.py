from requests_oauthlib import OAuth1Session
import json
from collections import defaultdict
from dateutil import parser
from pytz import timezone,utc
from datetime import datetime,timedelta
from time import sleep
import re
from dotenv import load_dotenv
from os.path import join,dirname
import os

class TwiApp:

    def __init__(self,screen_name,api_key,api_secret,access_token,access_secret):
        self.screen_name   = screen_name
        self.api_key       = api_key
        self.api_secret    = api_secret
        self.access_token  = access_token
        self.access_secret = access_secret
        self.friends = []

    def get_friends(self):
        api = 'https://api.twitter.com/1.1/friends/list.json'

        twitter = OAuth1Session(self.api_key, self.api_secret, self.access_token, self.access_secret)

        params = {'screen_name':self.screen_name, 'count':'200', 'include_user_entities':'false'}
        res = twitter.get(api, params = params)

        friends = json.loads(res.text)

        for friend in friends['users']:
            self.friends.append(friend['id_str'])

    def stream(self):

        url = "https://stream.twitter.com/1.1/statuses/filter.json"

        twitter = OAuth1Session(self.api_key, self.api_secret, self.access_token, self.access_secret)

        r = twitter.post(url, stream=True, data={'follow':self.friends})

        for i,line in enumerate(r.iter_lines()):

            if r.status_code == 200:
                twiobj = json.loads(line.decode())
                yield {'status' : 200, 'id' : twiobj['id_str'], 'text' : twiobj['text']}

            else:
                break

        yield {'status' : r.status_code}

    def getUsertweets(self,t):

        url = "https://api.twitter.com/1.1/statuses/home_timeline.json"

        twitter = OAuth1Session(self.api_key, self.api_secret, self.access_token, self.access_secret)
        tweets = []

        params ={'count' : '200','exclude_replies' : 'True', 'include_rts' : 'false'}

        is_looping = True

        while is_looping:

            req = twitter.get(url, params = params)

            if req.status_code == 200:
                timeline = json.loads(req.text)

                for tweet in timeline:

                    params['max_id'] = str(tweet['id']-1)

                    if parser.parse(tweet['created_at']).astimezone(JST) < t:
                        is_looping = False
                        break

                    tweets.append({'Tweet':tweet['text'],'ID':tweet['id']})

            else:
                print("ERROR: %d" % req.status_code)

            sleep(3)

        return tweets

    def Retweets(self,TID):

        url = "https://api.twitter.com/1.1/statuses/retweet/%s.json" % TID

        twitter = OAuth1Session(self.api_key, self.api_secret, self.access_token, self.access_secret)

        req = twitter.post(url)

    def Unretweets(self,TID):

        url = "https://api.twitter.com/1.1/statuses/unretweet/%s.json" % TID

        twitter = OAuth1Session(self.api_key, self.api_secret, self.access_token, self.access_secret)

        req = twitter.post(url)

def isSchedule(txt):

    p_time = re.compile(r"[0-9]+時[^間]|[0-9]+:[0-9]+")
    p_nico = re.compile(r"#sm")

    return p_time.search(txt) and p_nico.search(txt) == None

if __name__ == '__main__':

    dotenv_path = join(dirname(__file__),'.env')
    load_dotenv(dotenv_path)

    api_key      = os.environ.get('api_key')
    api_secret   = os.environ.get('api_secret')
    access_token = os.environ.get('access_token')
    access_secret= os.environ.get('access_secret')
    screen_name  = os.environ.get('screen_name')

    JST = timezone('Asia/Tokyo')

    now = datetime.now(utc) - timedelta(minutes=5)
    now = now.astimezone(JST)
    now = now.replace(minute=(now.minute // 15) * 15)

    twiApp = TwiApp(screen_name, api_key, api_secret, access_token, access_secret)

    # get Nijisanji member's IDs.
    twiApp.get_friends()

    # get their tweets.
    tweets = twiApp.getUsertweets(now)

    # RT tweets related their schedule.
    for tweet in tweets:

        if isSchedule(tweet['Tweet']):
            twiApp.Retweets(tweet['ID'])
