from venv import create
import tweepy
from datetime import datetime, timedelta, timezone
import mysql.connector
import json
import pickle
import pandas as pd
import re
from cleantext import clean

# model = pickle.load(open('/Users/azri-m/Desktop/Deploy TA/model/clf.pkl','rb'))
# tfidf = pickle.load(open('/Users/azri-m/Desktop/Deploy TA/model/tfidf1.pkl', 'rb'))

model_gempa = pickle.load(open('/Users/azri-m/Desktop/Deploy TA/model/clf.pkl','rb'))
tfidf_gempa = pickle.load(open('/Users/azri-m/Desktop/Deploy TA/model/tfidf1.pkl', 'rb'))
model_banjir = pickle.load(open('/Users/azri-m/Desktop/Deploy TA/model/clf_banjir.pkl', 'rb'))
tfidf_banjir = pickle.load(open('/Users/azri-m/Desktop/Deploy TA/model/tfidf1_banjir.pkl', 'rb'))


mydb = mysql.connector.connect(
  host="34.143.177.53",
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
        print(text)
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
          lon,lat = coordinates[0][0]
        username = all_data['user']['screen_name']
        if username == "280622fr":
            if "mag:" in text :
                mag = re.findall(r'mag:(\d+.?\d*)', text)
                mag = float(mag[0])
            elif "magnitudo:" in text:
                mag = re.findall(r'magnitudo: (\d+.?\d*)', text)
                mag = float(mag[0])
            else:
                mag = None
            BT = re.findall(r'(\d+.?\d*) bt', text)
            re_longitude = float(BT[0])
            if "ls" in text:
                LS = re.findall(r'(\d+.?\d*) ls',text)
                re_latitude = float(LS[0])*-1
            elif "lu" in text:
                LU = re.findall(r'(\d+.?\d*) lu',text)
                re_latitude = float(LU[0])
            else:
                re_longitude = None
                re_latitude = None
            mycursor = mydb.cursor()
            mycursor.execute("INSERT INTO bencana_alam (id, filter, username, text, created_at, location, lon, lat, mag) VALUES (%s, 'gempa', %s, %s, %s, %s, %s, %s, %s)", (id, username, text, created_at, location, re_longitude, re_latitude, mag))
            mydb.commit()
        elif "gempa" in text.lower():
            predict = model_gempa.predict(tfidf_gempa.transform([text]))
            all_data['predicted'] = int(predict)
            predicted = all_data['predicted']
            mycursor = mydb.cursor()
            mycursor.execute("INSERT INTO bencana_alam (id, filter, username, text, created_at, location, predicted, lon, lat) VALUES (%s, 'gempa', %s, %s, %s, %s, %s, %s, %s)", (id, username, text, created_at, location, predicted, lon, lat))
            mydb.commit()
        elif "banjir" in text.lower():
            predict = model_banjir.predict(tfidf_banjir.transform([text]))
            all_data['predicted'] = int(predict)
            predicted = all_data['predicted']
            mycursor = mydb.cursor()
            mycursor.execute("INSERT INTO bencana_alam (id, filter, username, text, created_at, location, predicted, lon, lat) VALUES (%s, 'gempa', %s, %s, %s, %s, %s, %s, %s)", (id, username, text, created_at, location, predicted, lon, lat))
            mydb.commit()



stream_listener = StreamListener('tSTGheSxnBYdbeAsdgoONHpKO',
        '6olnst42blgg7SieQDZc0JNXrcfPhefgyzt2Thleg2K1qJ86BP',
        '1488430474758598658-ZwqvC9nBE5vw9TXGa0qpvm2VeTMzSo',
        'TsTy0apy2aCzEuXBj7p0W2VRG3ucr0HBXfLmirQGHyioI')
stream_listener.filter(track = ["gempa","banjir"])