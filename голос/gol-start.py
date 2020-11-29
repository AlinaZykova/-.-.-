from PyQt5 import QtCore , QtGui
from PyQt5.QtWidgets import QLabel,QApplication,QMainWindow,QSizePolicy
from PyQt5.QtWebEngineWidgets import *
import subprocess, re, os, bs4, requests, sys
import threading
import speech_recognition as sr
import signal
import pyttsx3
import apiai, json

# Инициализируем SAPI5
engine = pyttsx3.init()
# Получаем список голосов
voices = engine.getProperty('voices')
# Устанавливаем русский язык
engine.setProperty('voice', 'en')
# Ищем голос Elena от RHVoice
# Его нужно заранее скачать тут, пролистав вниз до раздела SAPI 5:
# https://github.com/Olga-Yakovleva/RHVoice/wiki/Latest-version-%28Russian%29
for voice in voices:
    if voice.name == 'Elena':
        engine.setProperty('voice', voice.id)
# Скорость чтения
engine.setProperty('rate', 110)

# Получаем html шаблон для сообщений в окне чата
htmlcode='<div class="robot">How can i help?</div>';
f=open('index.html','r',encoding='UTF-8')
htmltemplate=f.read()
f.close()


def AiMessage(s):

    request = apiai.ApiAI('7f01246612e64e3f89264a85a965ddd3').text_request()
    # На каком языке будет послан запрос
    request.lang = 'en'

    request.session_id = '3301megabot'
    # Посылаем запрос к ИИ с сообщением от юзера
    request.query = s 
    responseJson = json.loads(request.getresponse().read().decode('utf-8'))

    response=''
    response = responseJson['result']['fulfillment']['speech'] 
    # Если есть ответ от бота - выдаём его,
    # если нет - бот его не понял
    if response:
        return response
    else:
        return 'i do not understand'

otvet=''
listen=''
vopros=''
dontlisten=''
ispeak=''

# Объявляем распознавалку речи от Google
r = sr.Recognizer()

# Отдельный поток 
def thread(my_func):
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=my_func, args=args, kwargs=kwargs)
        my_thread.start()
    return wrapper

# Функции для сигналов между потоками
def signal_handler(signal, frame):
    global interrupted
    interrupted = True    
def interrupt_callback():
    global interrupted
    return interrupted

# Функция активизирует Google Speech Recognition для распознавания команд
@thread
def listencommand():
    global listen
    global vopros
    global dontlisten
    # Следим за состоянием ассистента - слушает она или говорит
    listen.emit([1])
    # Слушаем микрофон
    with sr.Microphone() as source:
        #r.adjust_for_ambient_noise(source, duration=1)
        audio = r.listen(source)
    try:
        # Отправляем запись с микрофона гуглу, получаем распознанную фразу
        f=r.recognize_google(audio, language="ru-en").lower()
        # Меняем состояние ассистента со слушания на ответ
        listen.emit([2])
        # Отправляем распознанную фразу на обработку в функцию myvopros
        vopros.emit([f])
    # В случае ошибки меняем состояние ассистента на "не расслышал"
    except sr.UnknownValueError:
        print("The  robot did not hear")
        dontlisten.emit(['00'])
    except sr.RequestError as e:
        print("Ошибка сервиса; {0}".format(e))
signal.signal(signal.SIGINT, signal_handler)

# Графический интерфейс PyQt 
class W(QMainWindow):
    # Объявляем сигналы, которые приходят от асинхронных функций
    my_signal = QtCore.pyqtSignal(list, name='my_signal')
    my_listen = QtCore.pyqtSignal(list, name='my_listen')
    my_vopros = QtCore.pyqtSignal(list, name='my_vopros')
    my_dontlisten = QtCore.pyqtSignal(list, name='my_dontlisten')
    def __init__(self, *args):
        super().__init__()
        self.setAnimated(False)
        self.flag = True
        self.centralwidget = QMainWindow()
        self.centralwidget.setObjectName("centralwidget")
        self.setCentralWidget(self.centralwidget)
       self.label = QLabel(self.centralwidget)
        self.label.installEventFilter(self)
        self.label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
       
        self.label.setGeometry(QtCore.QRect(2, 2, 400, 300))

        self.browser = QWebEngineView(self.centralwidget)
        
        self.browser.setGeometry(QtCore.QRect(405, 2, 500, 300))
        # Загружаем в QWebEngineView html документ с чатом
        global htmltemplate
        global htmlcode
        htmlresult=htmltemplate.replace('%code%',htmlcode)
        self.browser.setHtml(htmlresult, QtCore.QUrl("file://"));
        self.browser.show()     
        self.label.setText("<center><img src='file:///"+os.getcwd()+"/img/1.jpg'></center>")
        global otvet
        otvet=self.my_signal
        global listen
        listen=self.my_listen
        global dontlisten
        dontlisten=self.my_dontlisten
        global vopros
        vopros=self.my_vopros
        self.my_listen.connect(self.mylisten, QtCore.Qt.QueuedConnection)
        self.my_vopros.connect(self.myvopros, QtCore.Qt.QueuedConnection)
        self.my_dontlisten.connect(self.mydontlisten, QtCore.Qt.QueuedConnection)

   
    def eventFilter(self,obj,e):
        if e.type() == 2:
            btn = e.button()
            if btn == 1:
                listencommand()
            elif btn == 2: self.label.setText("<center><img src='file:///"+os.getcwd()+"/img/1.jpg'></center>")
        return super(QMainWindow,self).eventFilter(obj,e)
    
    # Смена картинки девушки в зависимости от того слушает она или говорит
    def mylisten(self, data):
        if(data[0]==1):
            self.label.setText("<center><img src='file:///"+os.getcwd()+"/img/2.jpg'></center>")
        if(data[0]==2):
             self.label.setText("<center><img src='file:///"+os.getcwd()+"/img/1.jpg'></center>")


    def addrobotphrasetohtml(self, phrase):
        global htmltemplate
        global htmlcode
        htmlcode='<div class="robot">'+phrase+'</div>'+htmlcode
        htmlresult=htmltemplate.replace('%code%',htmlcode)
        self.browser.setHtml(htmlresult, QtCore.QUrl("file://"));
        self.browser.show()
    def addyouphrasetohtml(self, phrase):
        global htmltemplate
        global htmlcode
        htmlcode='<div class="you">'+phrase+'</div>'+htmlcode
        htmlresult=htmltemplate.replace('%code%',htmlcode)
        self.browser.setHtml(htmlresult, QtCore.QUrl("file://"));
        self.browser.show()
    def speakphrase(self, phrase):
        global engine
        engine.say(phrase)
        engine.runAndWait()
        engine.stop()    
    def myvopros(self, data):
        vp=data[0].lower()
        self.addrobotphrasetohtml(vp)
        ot='i can not hear'
        # Выполняем разные действия в зависимости от наличия ключевых слов фо фразе
        if(vp=='while' or vp=='exit' or vp=='log off' or vp=='bye'):
            ot='see you!'
            self.addyouphrasetohtml(ot)
            self.speakphrase(ot)
            sys.exit(app.exec_())
        elif('joke' in vp):
            ot=self.anekdot()
        else:
            # Если ключевых слов не нашли, используем Dialogflow
            ot=AiMessage(vp)
        # Добавляем ответ в чат
        self.addyouphrasetohtml(ot)
        # Читаем ответ вслух
        self.speakphrase(ot)
        
    # Функция меняет картинку если ассистент тебя не расслышал
    def mydontlisten(self, data): 
        self.label.setText("<center><img src='file:///"+os.getcwd()+"/img/3.jpg'></center>")

    # Функция дающая случайный анекдот
    def anekdot(self):
        s=requests.get('http://anekdotme.ru/random')
        b=bs4.BeautifulSoup(s.text, "html.parser")
        p=b.select('.anekdot_text')
        s=(p[0].getText().strip())
        reg = re.compile('[^a-zA-Zа-яА-я .,!?-]')
        s=reg.sub('', s)
        return(s)

# Запускаем программу на выполнение    
app = QApplication([])
w = W()
# Размер окна
w.resize(910,305)
w.show()
app.exec_()
