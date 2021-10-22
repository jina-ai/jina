#Project jarvis
import speech_recognition as sr 
import datetime
import wikipedia
import pyttsx3
import webbrowser
import random
import os

#Text To Speech

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
#print(voices)
engine.setProperty('voice',voices[0].id)

def speak(audio):  #here audio is var which contain text
    engine.say(audio)
    engine.runAndWait()

def wish():
    hour = int(datetime.datetime.now().hour)
    if hour >= 0 and hour<12:
        speak("good morning sir i am virtual assistent jarvis")
    elif hour>=12 and hour<18:
        speak("good afternoon sir i am virtual assistent jarvis") 
    else:
        speak("good night sir i am virtual assistent jarvis")  

#now convert audio to text
# 
def takecom():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listning....")
        audio = r.listen(source)
    try:
        print("Recognising.") 
        text = r.recognize_google(audio,language='en-in')
        print(text)
    except Exception:                #For Error handling
        speak("error...")
        print("Network connection error") 
        return "none"
    return text

#for main function                               
if __name__ == "__main__":
    wish()
    while True:
        query = takecom().lower()

        if "wikipedia" in query:
            speak("searching details....Wait")
            query.replace("wikipedia","")
            results = wikipedia.summary(query,sentences=2)
            print(results)
            speak(results)
        elif 'open advanced engineering mathematics' in query:
            webbrowser.open("https://drive.google.com/file/d/1jwuZeSeL8OIsZsaKB-NmH3KYZ1i-GT2g/view")
            speak("opening advanced engineering mathematics")
        elif 'open arthur beiser' in query:
            webbrowser.open("https://drive.google.com/file/d/1BpR64NNEe8wzT4ckKEb6M5wK3BEq57IF/view")
            speak("opening arthur beiser")  
        elif 'open basic electrical engineering' in query:
            webbrowser.open("https://drive.google.com/file/d/1U4ezqK-mg5i_5Ndbb8KADq4Ist1IU_8r/view")
            speak("opening basic electrical engineering")      
        elif 'open let us c' in query:
            webbrowser.open("https://drive.google.com/file/d/1T_pg4gj9bHU20NHBB_2mK0nHIpihyv0P/view")
            speak("opening let us c")    
        elif 'open electrical power system' in query:
            webbrowser.open("https://drive.google.com/file/d/1TVsNE6Ql_MHt3XX1vQTrZ8PSfvmFjLmF/view")
            speak("opening electrical power system")
        elif 'good bye' in query:
            speak("good bye")
            exit()
        elif 'shutdown' in query:
            speak("shutting down")
            os.system('shutdown -s')
            