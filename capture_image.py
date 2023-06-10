import cv2
import os
import datetime
import schedule
import time
import subprocess
import env
import mysql.connector
import shutil
import re

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
    deteleOldDetection()
    analyzeImage(fileName, mySQLTimeStamp)

    return fileName

def analyzeImage(fileName, mySQLTimeStamp):
    script_path = "yolov7/detect.py"
    source_path = fileName
    weights_path = "yolov7/runs/train/PKLot.v2-640.yolov7pytorch-tiny/weights/best.pt"
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

    # Save the detections to the database
    saveToDatabase(fileName, freeSpace, mySQLTimeStamp)
    
def saveToDatabase(fileName, freeSpace, mySQLTimeStamp):
    print(mySQLTimeStamp)
    mycursor = mydb.cursor()

    sql = "INSERT INTO free_slot (file_name, free_slot, timestamp) VALUES (%s, %s, %s)"
    val = (fileName, freeSpace, mySQLTimeStamp)
    mycursor.execute(sql, val)

    mydb.commit()

    print(mycursor.rowcount, "record inserted.")

def deteleOldDetection():
    folder_path = "runs/detect/exp"
    if os.path.exists(folder_path):
        try:
            # Use the shutil module's "rmtree" function to delete the folder and its contents
            shutil.rmtree(folder_path)
            print("Folder and its contents deleted successfully.")
        except OSError as e:
            print("Error: %s : %s" % (folder_path, e.strerror))
    else:
        print("Error: %s does not exist." % folder_path)

# captureImage()

schedule.every(1).minutes.do(captureImage)

while True:
    schedule.run_pending()
    time.sleep(1)
