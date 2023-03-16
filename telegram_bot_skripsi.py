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

## Parking Slot Capacity
parkingSlotCapacity = 10

## Connect to Telegram
API_KEY = "6011272127:AAH9jxZEECcwQfP67yGthwc8Hvrt0OUO5hM"

bot = telebot.TeleBot(API_KEY)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Hello, I am a Telegram bot. Use /help to see what I can do.")

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, "I support the following commands: \n /start \n /info \n /help \n /status")

@bot.message_handler(commands=['info'])
def info(message):
    bot.reply_to(message, "I am a simple Telegram bot created using the python-telegram-bot library.")

@bot.message_handler(commands=['status'])
def status(message):
    bot.reply_to(message, "I am up and running.")
    
@bot.message_handler(commands=['check'])
def status(message):
    mycursor.execute("SELECT * FROM used_slot order by timestamp desc")
    latestData = mycursor.fetchone()

    bot.reply_to(message, "Checking parking slot availability...")

    # check if latest data is exist
    if latestData is None:
        bot.reply_to(message, "No data available, please try again later.")
    else:
      now = datetime.datetime.now()
      latestDataUsedSlot = latestData[1]
      latestDataTimeStamp = latestData[2]
      diff = round((now - latestDataTimeStamp).total_seconds()/60)
      if diff > 5:
          bot.reply_to(message, "Technical error, please try again later.")
      else:
          if latestDataUsedSlot == 0:
              bot.reply_to(message, "Parking slot is empty.")
          else:
              availableSlot = parkingSlotCapacity - latestDataUsedSlot
              bot.reply_to(message, "There are " + str(availableSlot) + " available slot.")

print("Hey, I am up....")
bot.polling()