import telebot
import mysql.connector
import os
import env
import cv2
import time

## Connect to MySQL
mydb = mysql.connector.connect(
  host=os.getenv('DB_HOST'),
  user=os.getenv('DB_USER'),
  database=os.getenv('DB_NAME'),
  password=os.getenv('DB_PASSWORD')
)

mycursor = mydb.cursor()

mycursor.execute("SELECT * FROM test_table")

myresult = mycursor.fetchall()

for x in myresult:
  print(x)

## Run another python script




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
    
print("Hey, I am up....")
bot.polling()