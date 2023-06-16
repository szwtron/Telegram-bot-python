import time
import telebot
import mysql.connector
import os
import env
import datetime
import cv2
import subprocess
import shutil
import re

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
      pattern = r"/(.*?)\|"
      now = datetime.datetime.now()

      location = re.search(pattern, latestData[0]).group(1)
      latestDataFreeSlot = latestData[1]
      latestDataTimeStamp = latestData[2]
      diff = round((now - latestDataTimeStamp).total_seconds()/60)
      if diff > 5:
        bot.reply_to(message, "Technical error, please try again later.")
      else:
        bot.reply_to(message, "There are " + str(latestDataFreeSlot) + " available slot at " + str(location))
    
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
            pattern = r"/(.*?)\|"
            now = datetime.datetime.now()
            
            location = re.search(pattern, latestData[0]).group(1)
            latestDataFreeSlot = latestData[1]
            latestDataTimeStamp = latestData[2]
            diff = round((now - latestDataTimeStamp).total_seconds()/60)
            if diff > 5:
                bot.send_message(chat_id, "Technical error, please try again later.")
                subscriptions[chat_id] = False
            else:
                bot.send_message(chat_id, "There are " + str(latestDataFreeSlot) + " available slot at " + str(location))
        
        mydb.commit()
        time.sleep(180)  # Sleep for 3 minutes

# Global flag variables
stop_playback = False
pause_playback = False

# Provide the path to your video file
video_path = "yolov7/inference/footage_skripsi.mp4"
video_paused = False
current_frame = None

@bot.message_handler(commands=['start_video'])
def start_video(message):
    global video_path, video_paused, current_frame

    # Open the video file
    video = cv2.VideoCapture(video_path)

    while True:
        # Read a frame from the video
        ret, frame = video.read()

        # If the frame was not successfully read, exit the loop
        if not ret:
            break
        else:
            # Store the current frame for analysis
            current_frame = frame

        # Display the frame in a window called "Video"
        cv2.imshow('Video', frame)

        # Check if the video is paused
        if video_paused:
            while video_paused:
                pass

        # Wait for 25 milliseconds and check if the user pressed the 'q' key
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

    # Release the video object and close the window
    video.release()

    cv2.destroyAllWindows()

@bot.message_handler(commands=['pause_video'])
def pause_video(message):
    global video_paused
    video_paused = True

@bot.message_handler(commands=['resume_video'])
def resume_video(message):
    global video_paused
    video_paused = False

@bot.message_handler(commands=['demo_check'])
def demo_check(message):
    global current_frame
    
    # Check if there is a frame available for analysis
    if current_frame is not None:
        # Perform analysis on the current frame
        save_frame(current_frame)
        free_space = analyzeFrame()
    else:
        print("No frame available for analysis.")

    with open("images/demo/frame.jpg", "rb") as img:
        bot.send_photo(message.chat.id, img)
    bot.reply_to(message, "There are " + str(free_space) + " available slot.")
    if os.path.exists(output_path):
        # Delete the file
        os.remove(output_path)
        print("Image deleted:", output_path)
    else:
        print("Image not found:", output_path)

def save_frame(frame):
    global output_path
    cv2.imwrite(output_path, frame)
    print("Frame saved as", output_path)

def analyzeFrame():
    global output_path
    script_path = "yolov7/detect.py"
    source_path = output_path
    weights_path = "yolov7/runs/train/yolov7-yolov7-PKLOTv2.v1-v2.yolov7pytorch2/weights/best.pt"
    python_path = "E:/Anaconda/envs/yolov7-gpu/python.exe"
    img_size = 640

    # Construct the command to run
    command = f"{python_path} {script_path} --source {source_path} --weights {weights_path} --img-size {img_size}"

    # Run the command and capture the output
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Parse the detections from the output
    output_lines = result.stdout.decode().strip().split("\n")
    print(result.stderr.decode() + '\n')
    print(result.stdout.decode().strip().split("\n"))

    # Get the number of detections
    pattern = r'(\d+)\s+Free'
    numberofDetected = len(output_lines)
    detections = output_lines[numberofDetected - 1]
    matches = re.findall(pattern, detections) if detections else []

    freeSpace = 0
    for match in matches:
        freeSpace = int(match)

    return freeSpace

# Provide the output path for saving the frame as an image
output_path = f'images/demo/frame.jpg'

print("Hey, I am up....")
bot.polling()