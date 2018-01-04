#!/usr/bin/env python3
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import aiy.audio
import aiy.cloudspeech
import aiy.voicehat

import subprocess
import RPi.GPIO as gpio
import time

import numpy as np
from sklearn.externals import joblib
from janome.tokenizer import Tokenizer
import re
import sys

playshell = None
track_num = 1
track_name = "ドリカム"

def play_youtube(text, track_num):
    pkill = subprocess.Popen(["/usr/bin/pkill","vlc"],stdin=subprocess.PIPE)

    #aiy.audio.say('ドリカムyoutube再生')
    # アーティストと曲名だけを残す
    track = re.sub(r'(で|を)?再生(.*?)$', "", text)
    track = re.sub(r'(を|が)?聞(か|き|く|け|こ)(.*?)$', "", track)
    track = re.sub(r'(を)?かけて(.*?)$', "", track)
    track = re.sub(r'(の)?動画(.*?)$', "", track)
    track = re.sub(r'(で|を)見(.*?)$', "", track)
    track = re.sub(r'youtube', "", track)
    track = re.sub(r'を(\s*?)$', "", track)

    aiy.audio.say(track + 'をユーチューブで再生します')

    # 最初の曲の場合はアーティストと曲名を変数に保存する
    if track_num == 1:
        global track_name
        track_name = track
   
    global playshell
    if (playshell == None):
        playshell = subprocess.Popen(["/usr/local/bin/mpsyt",""],stdin=subprocess.PIPE ,stdout=subprocess.PIPE)

    playshell.stdin.write(bytes('/' + track + '\n' + str(track_num) + '\n', 'utf-8'))
    playshell.stdin.flush()

    gpio.setmode(gpio.BCM)
    gpio.setup(23, gpio.IN)

    while gpio.input(23):
        time.sleep(1)

    pkill = subprocess.Popen(["/usr/bin/pkill","vlc"],stdin=subprocess.PIPE)


def play_radiko(radio):
    pkill = subprocess.Popen(["/usr/bin/pkill","radiko_loop.sh"],stdin=subprocess.PIPE)

    subprocess.call('nohup /home/pi/aiyprojects-raspbian/src/radiko_loop.sh ' + radio + ' &', shell=True)

    gpio.setmode(gpio.BCM)
    gpio.setup(23, gpio.IN)

    while gpio.input(23):
        time.sleep(1)

    pkill = subprocess.Popen(["/usr/bin/pkill","radiko_loop.sh"],stdin=subprocess.PIPE)
    aiy.audio.say('ラジコを終了しています。少々お待ち下さい')
    time.sleep(15)
    aiy.audio.say('ラジコを終了しました')


j_tokenizer = Tokenizer()

def wakati_reading(text):
    tokens = j_tokenizer.tokenize(text.replace("'", "").lower())
    
    exclude_pos = [u'助動詞']
    
    #分かち書き
    tokens_w_space = ""
    for token in tokens:
        partOfSpeech = token.part_of_speech.split(',')[0]
        
        if partOfSpeech not in exclude_pos:
            tokens_w_space = tokens_w_space + " " + token.surface

    tokens_w_space = tokens_w_space.strip()
    
    #読み方
    tokens_reading = ""
    for token in tokens:
        partOfSpeech = token.part_of_speech.split(',')[0]
 
        if partOfSpeech not in exclude_pos:
            if token.reading != "*":
                tokens_reading = tokens_reading + " " + token.reading
            elif re.match('^[a-z]+$', token.base_form):
                alpha_reading = ""
                alpha_reading = token.base_form.replace("a", "エー ")
                alpha_reading = alpha_reading.replace("b", "ビー ")
                alpha_reading = alpha_reading.replace("c", "シー ")
                alpha_reading = alpha_reading.replace("d", "ディー ")
                alpha_reading = alpha_reading.replace("e", "イー ")
                alpha_reading = alpha_reading.replace("f", "エフ ")
                alpha_reading = alpha_reading.replace("g", "ジー ")
                alpha_reading = alpha_reading.replace("h", "エイチ ")
                alpha_reading = alpha_reading.replace("i", "アイ ")
                alpha_reading = alpha_reading.replace("j", "ジェー ")
                alpha_reading = alpha_reading.replace("k", "ケー ")
                alpha_reading = alpha_reading.replace("l", "エル ")
                alpha_reading = alpha_reading.replace("m", "エム ")
                alpha_reading = alpha_reading.replace("n", "エヌ ")
                alpha_reading = alpha_reading.replace("o", "オー ")
                alpha_reading = alpha_reading.replace("p", "ピー ")
                alpha_reading = alpha_reading.replace("q", "キュー ")
                alpha_reading = alpha_reading.replace("r", "アール ")
                alpha_reading = alpha_reading.replace("s", "エス ")
                alpha_reading = alpha_reading.replace("t", "ティー ")
                alpha_reading = alpha_reading.replace("u", "ユー ")
                alpha_reading = alpha_reading.replace("v", "ブイ ")
                alpha_reading = alpha_reading.replace("w", "ダブリュー ")
                alpha_reading = alpha_reading.replace("x", "エックス ")
                alpha_reading = alpha_reading.replace("y", "ワイ ")
                alpha_reading = alpha_reading.replace("z", "ゼット ")

                tokens_reading = tokens_reading + " " + alpha_reading
            elif re.match('^[0-9]+$', token.base_form):
                numeric_reading = ""
                numeric_reading = token.base_form.replace("0", "ゼロ ")
                numeric_reading = numeric_reading.replace("1", "イチ ")
                numeric_reading = numeric_reading.replace("2", "ニ ")
                numeric_reading = numeric_reading.replace("3", "サン ")
                numeric_reading = numeric_reading.replace("4", "ヨン ")
                numeric_reading = numeric_reading.replace("5", "ゴ ")
                numeric_reading = numeric_reading.replace("6", "ロク ")
                numeric_reading = numeric_reading.replace("7", "ナナ ")
                numeric_reading = numeric_reading.replace("8", "ハチ ")
                numeric_reading = numeric_reading.replace("9", "キュー ")

                tokens_reading = tokens_reading + " " + numeric_reading.strip()

    tokens_reading = tokens_reading.strip()
    
    feature = tokens_w_space + " " + tokens_reading
    
    return feature


def predict_intent(clean_text):
    data = np.array([clean_text])
    model = joblib.load('/home/pi/aiyprojects-raspbian/src/model/ja_jp_v7.pkl')
    prediction = model.predict(data)

    return int(prediction)


def main():
    volume = 80
    subprocess.call('amixer set Master 80%', shell=True)

    intent_list = ['BAYFM78', 'FMJ', 'FMT', 'HOUSOU-DAIGAKU', 'INT', 'JORF', 'LFR', 'NACK5', 'NEXT', 'QRR', 'RN1', 'RN2', 'STOP', 'TBS', 'VOLUMEDOWN', 'VOLUMEUP', 'YFM', 'YOUTUBE', 'radiru_r1', 'radiru_r2', 'radiru_r3']
    radio_list = [u'ベイエフエム78', u'ジェイウェーブ', u'東京エフエム', u'放送大学', u'インターエフエム897', u'ラジオにっぽん', u'にっぽん放送', u'ナックファイブ', u'NEXT', u'文化放送', u'ラジオ日経第一', u'ラジオ日経第二', u'STOP', u'ティービーエス', u'VOLUMEDOWN', u'VOLUMEUP', u'エフエム横浜', u'YOUTUBE', u'NHK第一', u'NHK第二', u'NHKエフエム']

    recognizer = aiy.cloudspeech.get_recognizer()
    #recognizer.expect_hotword('Google')
    button = aiy.voicehat.get_button()

    aiy.audio.get_recorder().start()

    while True:
        intent = ''
        text = ''

        time.sleep(3) 
        aiy.audio.say('どうしますか？')
        button.wait_for_press()
        print('リスニング中・・・')

        try:
            text = recognizer.recognize()
        except:
            aiy.audio.say('エラーです')
            time.sleep(3)
            sys.exit()


        if text == '':
            aiy.audio.say('聞き取れませんでした')
        else:
            print('音声インプット 「', text, '」')

            clean_text = wakati_reading(text)
            predicted_number = predict_intent(clean_text)
 
            intent = intent_list[predicted_number]
            print(intent)

            with open("/home/pi/aiyprojects-raspbian/src/input_ja_JP.txt", "a") as myfile:
                myfile.write(text + "," + intent + "\n")

            if intent == 'YOUTUBE':
                track_num = 1
                play_youtube(text, track_num)
            elif intent == 'NEXT':
                track_num = track_num + 1
                play_youtube(track_name, track_num)
            elif intent == 'VOLUMEUP':
                if volume + 20 > 100:
                    aiy.audio.say('音量は最大です')
                else:
                    volume = volume + 20
                    aiy.audio.say('音量を' + str(volume) + 'にしました')
                    subprocess.call('amixer set Master ' + str(volume) + '%', shell=True)
            elif intent == 'VOLUMEDOWN':
                if volume - 20 < 0:
                    aiy.audio.say('音量は最小です')
                else:
                    volume = volume - 20
                    aiy.audio.say('音量を' + str(volume) + 'にしました')
                    subprocess.call('amixer set Master ' + str(volume) + '%', shell=True)
            elif intent == 'STOP':
                aiy.audio.say('シャットダウンします。お疲れ様でした。')
                time.sleep(5)
                subprocess.call('sudo shutdown now', shell=True)
            elif intent != '':
                radio = radio_list[predicted_number]
                print('radio')
                aiy.audio.say(radio + 'をラジコで再生します')
                play_radiko(intent)
            else:
                aiy.audio.say('すいません、分かりません') 
            #elif 'turn off the light' in text:
            #    led.set_state(aiy.voicehat.LED.OFF)


if __name__ == '__main__':
    main()
