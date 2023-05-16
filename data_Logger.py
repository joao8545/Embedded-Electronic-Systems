from datetime import datetime
import time
from sense_hat import SenseHat
from select import select
from threading import Thread

## Logging Settings
TEMP_H=True
TEMP_P=False
HUMIDITY=True
PRESSURE=True
ORIENTATION=True
ACCELERATION=True
MAG=True
GYRO=True
DELAY = 0
BASENAME = "Fall"
WRITE_FREQUENCY = 1
LOG_AT_START = False


def file_setup(filename):
    header =[]
    header.append("index")
    header.append("timestamp")
    if TEMP_H:
        header.append("temp_h")
    if TEMP_P:
        header.append("temp_p")
    if HUMIDITY:
        header.append("humidity")
    if PRESSURE:
        header.append("pressure")
    if ORIENTATION:
        header.extend(["pitch","roll","yaw"])
    if MAG:
        header.extend(["mag_x","mag_y","mag_z"])
    if ACCELERATION:
        header.extend(["accel_x","accel_y","accel_z"])
    if GYRO:
        header.extend(["gyro_x","gyro_y","gyro_z"])

    with open(filename,"w") as f:
        f.write(",".join(str(value) for value in header)+ "\n")


## Function to collect data from the sense hat and build a string
def get_sense_data(index=0):
    sense_data=[]

    sense_data.append(index)
    sense_data.append(datetime.now())
    if TEMP_H:
        sense_data.append(sense.get_temperature_from_humidity())

    if TEMP_P:
        sense_data.append(sense.get_temperature_from_pressure())

    if HUMIDITY:
        sense_data.append(sense.get_humidity())

    if PRESSURE:
        sense_data.append(sense.get_pressure())

    if ORIENTATION:
        yaw,pitch,roll = sense.get_orientation().values()
        sense_data.extend([pitch,roll,yaw])

    if MAG:
        mag_x,mag_y,mag_z = sense.get_compass_raw().values()
        sense_data.extend([mag_x,mag_y,mag_z])

    if ACCELERATION:
        x,y,z = sense.get_accelerometer_raw().values()
        sense_data.extend([x,y,z])

    if GYRO:
        gyro_x,gyro_y,gyro_z = sense.get_gyroscope_raw().values()
        sense_data.extend([gyro_x,gyro_y,gyro_z])

    print(sense_data)
    return sense_data

def show_state(logging):
    if logging:
        sense.show_letter("!",text_colour=[0,100,0])
    else:
        sense.show_letter("!",text_colour=[100,0,0])


def log_data():
    output_string = ",".join(str(value) for value in sense_data)
    batch_data.append(output_string)

def timed_log():
    while run:
        if logging == True:
            log_data()
        time.sleep(DELAY)


## Main Program
sense = SenseHat()
run=True
logging=LOG_AT_START
show_state(logging)
batch_data= []

if BASENAME == "":
    filename = "SenseLog-"+str(datetime.now())+".csv"
else:
    filename = BASENAME+"-"+str(datetime.now())+".csv"



BASENAME ="200 settling  and multiple measurements"
filename = BASENAME+".csv"

file_setup(filename)

i=1


while run==True:
	
    sense_data = get_sense_data(i)
    i+=1

    log_data()

    if len(batch_data) >= WRITE_FREQUENCY:
        with open(filename,"a") as f:
            for line in batch_data:
                f.write(line + "\n")
            batch_data = []



sense.clear()