Streaming Japanese Music on Google AIY Voice Kit
=====
The main objective of this project is to listen to Japanese music on Raspberry Pi 3 at home and while driving my car. The motivation behind this project is both Google Home and Amazon Alexa have *very* limited options when it comes to Japanese music subscription services outside Japan, but I wanted my kids to have exposure to Japanese music on a regular basis.

I used Google Speech API for ASR/speech-to-text, and a custom scikit-learn gradient boosting model for capturing intent. Open JTalk is used for text-to-speech. Actual music streaming pieces are dependent on other people's hard work (e.g. Radiko script, youtube-dl, etc). :)


Requirements
----

**Hardware**

* Raspberry Pi 3
* [Google AIY Voice Kit] (https://aiyprojects.withgoogle.com/voice)
* Micro USB charger (1.5A)
* Micro SD card

(I spent about $40 at Micro Center)

**Software**

* Raspbian
* Python >3.4
* [Google AIY] (https://github.com/google/aiyprojects-raspbian)
* Google Cloud Platform subscription for Google Speech API
* Open JTalk


Instructions
----

**Set up Google AIY Voice Kit**

1. Follow this [tutorial] (https://aiyprojects.withgoogle.com/voice) to assemble hardware and set up Google Speech API.
2. Clone Google AIY repo on home directory.  
`git clone https://github.com/google/aiyprojects-raspbian.git`
3. Replace aiyprojects-raspbian/src/aiy/i18n.py to enable Japanese language for Google Speech API.
4. Overwrite aiyprojects-raspbian/src with the content of *raspbian_aiy_smart_speaker* on this repo.
5. Enable service:  
`sudo mv my_cloudspeech.service /lib/systemd/system/`  
`sudo systemctl enable my_cloudspeech.service`

![1](https://user-images.githubusercontent.com/35077214/34582028-27682d56-f158-11e7-9ac9-9a44eba1d272.JPG)	

**Configure Open JTalk**

1. Install Open JTalk:  
`sudo apt-get update`  
`sudo apt-get install open-jtalk open-jtalk-mecab-naist-jdic hts-voice-nitech-jp-atr503-m001`
2. Download different voice:  
`wget https://sourceforge.net/projects/mmdagent/files/MMDAgent_Example/MMDAgent_Example-1.6/MMDAgent_Example-1.6.zip/download -O MMDAgent_Example-1.6.zip`  
`unzip MMDAgent_Example-1.6.zip MMDAgent_Example-1.6/Voice/*`  
`sudo cp -r MMDAgent_Example-1.6/Voice/mei/ /usr/share/hts-voice`  

**Set up Radiko script and YouTube add-on**

1. Install dependencies for Radiko:  
`sudo apt-get install rtmpdump swftools libxml2-utils libav-tools`
2. Install mplayer for Radiko playback:  
`sudo apt-get install mplayer`
3. Install YouTube add-on:  
`sudo pip3 install mps-youtube youtube-dl`
4. Install vlc for YouTube playback:  
`sudo apt-get install vlc`
5. Set vlc as the default player for mps-youtube:  
`mpsyt set player vlc, set playerargs, exit`

**Deploy machine learning model**

1. Install dependencies for scikit-learn:  
`source env/bin/activate`  
`sudo apt-get install liblapack-dev`  
`sudo apt-get install build-essential python-dev python-setuptools python-numpy python-scipy libatlas-dev libatlas3gf-base`  
`sudo pip3 install --user --install-option="--prefix=" -U scipy scikit-learn`  
`sudo pip3 install pandas janome`  
2. Run gbt.py to build a model (alternatively, use 32-bit machine for model training)

***DONE!***

![2](https://user-images.githubusercontent.com/35077214/34582044-3937fe76-f158-11e7-937e-9beca15ec4e3.JPG)

Machine learning model comparison
----

For capturing intent, I used Gradient Boosting (scikit-learn), XGBoost, and LSTM (keras/tensorflow). While LSTM with word embedding (trained on Japanese Wikipedia) had slightly higher accuracy, the model size was too big to deploy to a Raspberry Pi 3. After trial and error, I ended up using the Gradient Boosting model due to simpler deployment.


