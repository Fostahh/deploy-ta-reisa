import tweepy
from datetime import datetime, timedelta, timezone
import mysql.connector
import json
import pickle
import pandas as pd
import re
from cleantext import clean

# model = pickle.load(open(r'model\clf.pkl','rb'))
# tfidf = pickle.load(open(r'model\tfidf1.pkl', 'rb'))
# model = pickle.load(open('/Users/azri-m/Desktop/Deploy TA/model/clf.pkl','rb'))
# tfidf = pickle.load(open('/Users/azri-m/Desktop/Deploy TA/model/tfidf1.pkl', 'rb'))
model = pickle.load(open('/app/model/clf.pkl','rb'))
tfidf = pickle.load(open('/app/model/tfidf1.pkl', 'rb'))


mydb = mysql.connector.connect(
  host="34.124.187.78",
  user="azri",
  passwd="12345",
  database="db_skripsi")

class StreamListener(tweepy.Stream):

    def on_status (self, status):
        if len(self.tweets) == self.limit:
            self.disconnect()
   

    def on_data(self, data):
        all_data = json.loads(data)
        text = all_data['text']
        text = clean(text, no_emoji=True)
        print("Ini text ",text)
        predict = model.predict(tfidf.transform([text]))
        all_data['predicted'] = int(predict)
        predicted = all_data['predicted']
        print("Ini predicted data ", predicted)
        created_at = all_data['created_at']
        id = all_data['id']
        if all_data['place'] == None:
          place = None
          location = None
          bounding_box = None
          coordinates = None
          lon,lat = [None,None]
        else:
          place = all_data['place']
          location = place['full_name']
          bounding_box = place['bounding_box']
          coordinates = bounding_box['coordinates']
          lat,lon = coordinates[0][0]
        username = all_data['user']['screen_name']
        if username == "infoBMKG":
            BT = re.findall(r'(\d+.?\d*) BT', text)
            re_longitude = float(BT[0])
            if "LU" in text:
                LU = re.findall(r'(\d+.?\d*) LU',text)
                re_latitude = float(LU[0])
            elif "LS" in text:
                LS = re.findall(r'(\d+.?\d*) LS',text)
                re_latitude = float(LS[0])*-1
            mycursor = mydb.cursor()
            mycursor.execute("INSERT INTO bmkg (text,username, re_longitude, re_latitude) VALUES (%s, %s, %s, %s)",(text,username,re_longitude,re_latitude))
            mydb.commit()
        if "gempa" in text.lower():
            mycursor = mydb.cursor()
            mycursor.execute("INSERT INTO gempa (id, username, text, created_at, location, predicted, lon, lat) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",(id,username,text,created_at,location,predicted,lon,lat))
            mydb.commit()
        elif "banjir" in text.lower():
            mycursor = mydb.cursor()
            mycursor.execute("INSERT INTO banjir (id, username, text, created_at, location, predicted, lon, lat) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",(id,username,text,created_at,location,predicted,lon,lat))
            mydb.commit()



stream_listener = StreamListener('tSTGheSxnBYdbeAsdgoONHpKO',
        '6olnst42blgg7SieQDZc0JNXrcfPhefgyzt2Thleg2K1qJ86BP',
        '1488430474758598658-ZwqvC9nBE5vw9TXGa0qpvm2VeTMzSo',
        'TsTy0apy2aCzEuXBj7p0W2VRG3ucr0HBXfLmirQGHyioI')
stream_listener.filter(track = ["gempa","banjir"])