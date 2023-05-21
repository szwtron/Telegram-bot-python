import time
import telebot
import mysql.connector
import os
import env
import datetime

## Connect to MySQL
mydb = mysql.connector.connect(
  host=os.getenv('DB_HOST'),
  user=os.getenv('DB_USER'),
  database=os.getenv('DB_NAME'),
  password=os.getenv('DB_PASSWORD')
)

mycursor = mydb.cursor()

## Dev Check Counter
devCheckCounter = 1

subscriptions = {}

## Connect to Telegram
API_KEY = os.getenv('API_KEY')

bot = telebot.TeleBot(API_KEY)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message, 
        "Hello👋, I am a Telegram bot to give you information about available parking slot in my designated area 😎. " +
        "Use /help to see what I can do."
    )

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, "I support the following commands: \n /start \n /info \n /help \n /check \n /subscribe \n /unsubscribe")

@bot.message_handler(commands=['info'])
def info(message):
    bot.reply_to(
        message, 
        "I am a Telegram bot to give you information about available parking slot in my designated area. " + 
        "I am created using the python-telegram-bot library and I use YOLOv7 for my detection model."
    )
    
@bot.message_handler(commands=['check'])
def check(message):
    mycursor.execute("SELECT * FROM free_slot order by timestamp desc limit 1")
    latestData = mycursor.fetchone()

    bot.reply_to(message, "Checking parking slot availability...")

    # check if latest data is exist
    if latestData is None:
        bot.reply_to(message, "No data available, please try again later.")
    else:
      now = datetime.datetime.now()
      latestDataFreeSlot = latestData[1]
      latestDataTimeStamp = latestData[2]
      diff = round((now - latestDataTimeStamp).total_seconds()/60)
      if diff > 5:
        bot.reply_to(message, "Technical error, please try again later.")
      else:
        bot.reply_to(message, "There are " + str(latestDataFreeSlot) + " available slot.")
    
    mydb.commit()

@bot.message_handler(commands=['dev_check'])
def devCheck(message):
    global devCheckCounter

    mycursor.execute("SELECT * FROM free_slot_dev WHERE file_name = %s", ("img" + str(devCheckCounter) + ".jpg",) )
    Data = mycursor.fetchone()

    if devCheckCounter > 5:
        devCheckCounter = 1
    else:
        with open("dev_images/img" + str(devCheckCounter) + ".jpg", "rb") as img:
            bot.send_photo(message.chat.id, img)
        bot.reply_to(message, "There are " + str(Data[1]) + " available slots.")
        devCheckCounter = devCheckCounter + 1
    
    mydb.commit()

@bot.message_handler(commands=['subscribe'])
def handle_subscribe(message):
    chat_id = message.chat.id
    subscriptions[chat_id] = True
    bot.reply_to(message, "You have subscribed to receive messages.")
    start_sending_messages(chat_id)

@bot.message_handler(commands=['unsubscribe'])
def handle_unsubscribe(message):
    chat_id = message.chat.id
    subscriptions[chat_id] = False
    bot.reply_to(message, "You have unsubscribed. Messages will stop being sent.")

def start_sending_messages(chat_id):
    while subscriptions.get(chat_id):
        mycursor.execute("SELECT * FROM free_slot order by timestamp desc limit 1")
        latestData = mycursor.fetchone()

        # check if latest data is exist
        if latestData is None:
            bot.send_message(chat_id, "No data available, please try again later.")
        else:
            now = datetime.datetime.now()
            latestDataFreeSlot = latestData[1]
            latestDataTimeStamp = latestData[2]
            diff = round((now - latestDataTimeStamp).total_seconds()/60)
            if diff > 5:
                bot.send_message(chat_id, "Technical error, please try again later.")
            else:
                bot.send_message(chat_id, "There are " + str(latestDataFreeSlot) + " available slot.")
        
        mydb.commit()
        time.sleep(180)  # Sleep for 3 minutes

print("Hey, I am up....")
bot.polling()