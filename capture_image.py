import cv2
import os
import datetime
import schedule
import time
# from yolov7 import detect
import subprocess
import json
import env
import mysql.connector

mydb = mysql.connector.connect(
  host=os.getenv('DB_HOST'),
  user=os.getenv('DB_USER'),
  database=os.getenv('DB_NAME'),
  password=os.getenv('DB_PASSWORD')
)

def captureImage():
    # Create a folder to save the images in
    if not os.path.exists('images'):
        os.makedirs('images')

    # Open the default camera
    cap = cv2.VideoCapture(0)

    # Wait for the camera to warm up
    cv2.waitKey(1000)

    # Capture a frame
    ret, frame = cap.read()

    # Release the camera
    cap.release()

    # Generate a filename based on the current timestamp
    timeStamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    mySQLTimeStamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    fileName = f'images/image_{timeStamp}.jpg'

    # Save the frame as an image file with the generated filename
    cv2.imwrite(fileName, frame)
    analyzeImage(fileName, mySQLTimeStamp)
    

    return fileName

def analyzeImage(fileName, mySQLTimeStamp):
    script_path = "yolov7/detect.py"
    source_path = fileName
    weights_path = "yolov7/yolov7.pt"
    python_path = "E:/Anaconda/envs/yolov7-cpu-mode/python.exe"
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
    numberofDetected = len(output_lines)
    detections = output_lines[numberofDetected - 1]
    detections = detections.split()
    detections = detections[0]

    # Do something with the detections, for example print them
    print(detections)

    # Save the detections to the database
    saveToDatabase(fileName, detections, mySQLTimeStamp)
    
def saveToDatabase(fileName, detections, mySQLTimeStamp):
    print(mySQLTimeStamp)
    mycursor = mydb.cursor()

    sql = "INSERT INTO used_slot (file_name, used_slot, timestamp) VALUES (%s, %s, %s)"
    val = (fileName, detections, mySQLTimeStamp)
    mycursor.execute(sql, val)

    mydb.commit()

    print(mycursor.rowcount, "record inserted.")

captureImage()

# schedule.every(1).minutes.do(captureImage)

# while True:
#     schedule.run_pending()
#     time.sleep(1)
