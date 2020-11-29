from gtts import gTTS
import random
import time
import playsound
import speech_recognition as sr

def listen_command():
    # obtain audio from the microphone
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Скажите вашу команду: ")
        audio = r.listen(source)

        # recognize speech using Google Speech Recognition
    try:
        our_speech = r.recognize_google(audio, language="en")
        print("Вы сказали: "+our_speech)
        return our_speech
    except sr.UnknownValueError:
      return "ошибка"
    except sr.RequestError:
      return "ошибка"

    #return input("Скажите вашу команду: ")

def do_this_command(message):
    message = message.lower()
    if "hello" in message:
        say_message("hello my friend")
    elif "bye" in message:
          say_message("goodbye")
          exit()
    else:
        say_message("повторите пожалуйста")



def say_message(message):
    voice = gTTS(message, lang="en")
    file_voice_name = "_audio_"+str(time.time())+"_"+str(random.randint(0,100000))+".mp3"
    voice.save(file_voice_name)
    playsound.playsound(file_voice_name)
    print("Голосовой ассистент: "+message)

if __name__ == '__main__':
    while True:
        command = listen_command()
        do_this_command(command)
