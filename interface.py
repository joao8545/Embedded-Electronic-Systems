import tkinter as tk
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import time
from datetime import datetime
from scipy.ndimage import uniform_filter1d
from collections import namedtuple

FILEPATH="data\/up-down after 200.csv"
MOCK=True
#MOCK=False
if not MOCK:
    from sense_hat import SenseHat

def euler_angles_to_rotation_matrix(roll, pitch, yaw):
    R_x = np.array([[1, 0, 0],
                    [0, np.cos(roll), -np.sin(roll)],
                    [0, np.sin(roll), np.cos(roll)]])
                    
    R_y = np.array([[np.cos(pitch), 0, np.sin(pitch)],
                    [0, 1, 0],
                    [-np.sin(pitch), 0, np.cos(pitch)]])
                    
    R_z = np.array([[np.cos(yaw), -np.sin(yaw), 0],
                    [np.sin(yaw), np.cos(yaw), 0],
                    [0, 0, 1]])
                    
    # Combine the three rotation matrices to get the final rotation matrix
    R = np.dot(R_z, np.dot(R_y, R_x))
    return R


def local_to_global_direction(rotation_matrix, local_movement):
    # Multiply the rotation matrix by the local movement vector
    global_direction = np.dot(rotation_matrix, local_movement)
    return global_direction


class DataFrame:
    def __init__(self, acel=None, gyro=None, orientation=None, pressure=None, mag=None, timestamp=None,index=None) -> None:
        self.acel: np.ndarray = np.array(acel) if acel is not None else None
        self.gyro: np.ndarray = np.deg2rad(np.array(gyro)) if gyro is not None else None
        self.orientation: np.ndarray = np.array(orientation) if orientation is not None else None
        self.pressure: np.ndarray = np.array(pressure) if pressure is not None else None
        self.mag: np.ndarray = np.array(mag) if mag is not None else None
        self.timestamp: datetime = timestamp
        self.index=index

def movmean(A,k):
        return uniform_filter1d(A,k)
    

def filter_readings(readings,k=5):
    concatenated_arrays = {}
    
    # Iterate over each DataFrame in readings
    for df in readings:
        # Iterate over each attribute in the DataFrame
        for attr_name, attr_value in df.__dict__.items():
            # Skip the 'timestamp' attribute
            if not isinstance(attr_value, np.ndarray):
                continue
            if attr_name == 'timestamp' :
                print("should not get here")
                continue
            if attr_name=="pressure":
                continue
            # Check if the attribute is None or an empty array
            if attr_value is None or len(attr_value) == 0:
                continue
            
            # Concatenate the column array to the existing array for the attribute
            if attr_name in concatenated_arrays:
                concatenated_arrays[attr_name].append( attr_value)
            else:
                concatenated_arrays[attr_name] = [attr_value]
    # Initialize an empty list to store the filtered DataFrames
    filtered_list = []
    filtered_arrays={}

    # Iterate over the keys and arrays in concatenated_arrays
    for key, array in concatenated_arrays.items():
        # Apply movmean to the array
        #need working
        filtered_array = np.transpose(np.array([movmean(el, 2) for el in np.transpose(array)]))
        filtered_arrays[key]=filtered_array
    
    TupleClass = namedtuple('TupleClass', filtered_arrays.keys())
    object_list = [TupleClass(*values) for values in zip(*filtered_arrays.values())]
    
    for obj in object_list:
        filtered_list.append(DataFrame(**obj._asdict()))
    
    return filtered_list

class BaseApp(tk.Tk):
    def __init__(
        self,
        screenName: str | None = None,
        baseName: str | None = None,
        className: str = "Tk",
        useTk: bool = True,
        sync: bool = False,
        use: str | None = None,
    ) -> None:
        super().__init__(screenName, baseName, className, useTk, sync, use)
        self.title("Position tracker")

        self.map_fig = Figure((1, 1), 100)
        canvas = FigureCanvasTkAgg(self.map_fig, self)
        canvas.draw()
        ax = self.map_fig.add_subplot(111, projection="3d") 
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("z")
        self.map=ax
        

        toolbar = NavigationToolbar2Tk(canvas, self)
        canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        toolbar.update()

        #ax.plot(t, 2 * np.sin(2 * np.pi * t), 2 * np.cos(3 * np.pi * t))
        info_frame=tk.Frame(self)
        info_frame.pack(side=tk.RIGHT,fill=tk.BOTH,expand=1)
        self.graphs=[]
        
        for i in range(3):
            self.graphs.append([])
            for j in range(3):
                f = Figure((1, 1), 100)
                canvas=FigureCanvasTkAgg(f,info_frame)
                canvas.draw()
                ax=f.add_subplot(111)
                self.graphs[i].append((f,ax))
                canvas.get_tk_widget().grid(column=i+1,row=j+1,padx=1,pady=1)
        l=["x","y","z"]
        for i in range(len(l)):
            tk.Label(info_frame,text=l[i]).grid(row=0,column=i+1)
        l=["Acceleration","Speed","Displacement"]
        for i in range(len(l)):
            tk.Label(info_frame,text=l[i]).grid(row=i+1,column=0)
            
    
        tk.Button(info_frame,text="Calibrate",command=self.calibrate_sensor).grid(row=8,column=0,)
        tk.Button(info_frame,text="Record", command=self.record).grid(row=8,column=1,)
        tk.Button(info_frame,text="Plot", command=self.process).grid(row=8,column=2)
        self.status_label=tk.StringVar(info_frame,"status")
        tk.Label(info_frame,textvariable=self.status_label).grid(column=0,row=9,columnspan=5)
        self.init_tracking()
    
    def init_tracking(self):
        self.plot_data=[]
        self.acc_data=[]
        self.vel_data=[]
        self.plot_orientation=[]
        
        self.index=0
        self.baseline={
            "gyro":np.array([0,0,0]),
            "orientation":np.array([0,0,0]),
            "mag":np.array([0,0,0]),
            "acel":np.array([0,0,0]),
            "pressure":np.array([0])
        }
        self.calibration_running=False
        self.last_update=None
        self.vel=np.array([0,0,0])
        self.pos=np.array([0,0,0])
        self.acc=np.array([0,0,0])
        self.plot_data.append(self.pos)
        self.plot_orientation.append(np.array([0,0,0]))
        self.acc_data.append(self.acc)
        self.vel_data.append(self.vel)
        self.readings:list[DataFrame]=[]
        self.start=None
        if not MOCK:
            self.sense = SenseHat()
    
    def calibrate_sensor(self, samples=200):
        if not self.calibration_running:
            self.status_label.set("calibration is starting")
            print("calibration is starting")
            self.calibration_running = True
            self.i = 0
            self.baseline = {
                "gyro": np.zeros(3),
                "orientation": np.zeros(3),
                "mag": np.zeros(3),
                "acel": np.zeros(3),
                "pressure": np.zeros(1)
            }
            self.continue_calibration(samples)
        else:
            self.calibration_running = False

    def continue_calibration(self,samples=50):
        if (self.i >= samples and MOCK) or not self.calibration_running :
            for key in self.baseline.keys():
                self.baseline[key] /= self.i
            self.status_label.set(f"calibration is done with {self.i} samples")
            print(f"calibration is done with {self.i} samples")
            
            return

        df = self.get_sensor_data()

        self.baseline["gyro"] += np.array(df.gyro)
        self.baseline["orientation"] += np.array(df.orientation)
        self.baseline["mag"] += np.array(df.mag)
        self.baseline["acel"] += np.array(df.acel)
        self.baseline["pressure"] += np.array(df.pressure)

        self.i += 1
        self.after(1,self.continue_calibration,samples)
       
    def get_sensor_data(self):
        if MOCK:
            self.index+=1
            return self.mock_sensor(FILEPATH,self.index)
        return self.read_sensor()
        pass
    
    def read_sensor(self)->DataFrame:
        
        p=self.sense.get_pressure()
        yaw,pitch,roll = self.sense.get_orientation().values()#The values are Floats representing the angle of the axis in degrees.
        mag_x,mag_y,mag_z = self.sense.get_compass_raw().values()#The values are Floats representing the magnetic intensity of the axis in microteslas
        x,y,z = self.sense.get_accelerometer_raw().values()#The values are Floats representing the acceleration intensity of the axis in Gs
        gyro_x,gyro_y,gyro_z = self.sense.get_gyroscope_raw().values()#The values are Floats representing the rotational intensity of the axis in radians per second
        return DataFrame([x,y,z],[gyro_x,gyro_y,gyro_z],[yaw,pitch,roll],[p],[mag_x,mag_y,mag_z],datetime.now())
        pass
    
    def mock_sensor(self,file_path,index)->DataFrame:
        with open(file_path,"r") as fp:
            line=fp.readlines()[index].split(",")
            if len(line)==16:
                a=(float(line[10]),float(line[11]),float(line[12]))
                g=(float(line[13]),float(line[14]),float(line[15]))
                o=(float(line[4]),float(line[5]),float(line[6]))
                p=(float(line[3]))
                m=(float(line[7]),float(line[8]),float(line[9]))
                t=datetime.strptime(line[0],'%Y-%m-%d %H:%M:%S.%f')
                i=None
            elif len(line)==17:
                a=(float(line[11]),float(line[12]),float(line[13]))
                g=(float(line[14]),float(line[15]),float(line[16]))
                o=(float(line[5]),float(line[6]),float(line[7]))
                p=(float(line[4]))
                m=(float(line[8]),float(line[9]),float(line[10]))
                t=datetime.strptime(line[1],'%Y-%m-%d %H:%M:%S.%f')
                i=int(line[0])
            data_frame=DataFrame(a,g,o,p,m,t,i)
        return data_frame
        pass
    
    def update_map(self):
        self.map.cla()
        #self.map.plot(*zip(*self.plot_data))
        self.map.quiver(*zip(*self.plot_data),*zip(*self.plot_orientation),normalize=True,pivot="middle",length=10)
        self.map_fig.canvas.draw_idle()
        #print(self.acc_data)
        for i in range(3):
            for j in range(3):
                self.graphs[i][j][1].cla()
        for i in range(3):
        
            self.graphs[i][0][1].plot([t[i] for t in self.acc_data])
            self.graphs[i][1][1].plot([t[i] for t in self.vel_data])
            self.graphs[i][2][1].plot([t[i] for t in self.plot_data])
        for i in range(3):
            for j in range(3):
                self.graphs[i][j][0].canvas.draw_idle()
        self.status_label.set("plotting is done")
        print("plotting is done")   
        pass
    
    def record(self):
        if self.start is None:
            self.status_label.set("recording starting")
            print("recording starting")
            self.start=datetime.now()
        df=self.get_sensor_data()
        self.readings.append(df)
        if (datetime.now()-self.start).total_seconds()>=15:
            self.start=None
            self.status_label.set("recording is done")
            print("recording is done")
            return
        self.after(100,self.record)
        pass
    
    def process(self):
        self.status_label.set("plotting starting")
        print("plotting starting")
        # reseting readings
        self.vel=np.array([0,0,0])
        self.pos=np.array([0,0,0])
        self.acc=np.array([0,0,0])
        self.acc_data=[]
        self.vel_data=[]
        self.plot_data=[]
        self.plot_orientation=[]
        self.plot_data.append(self.pos)
        self.plot_orientation.append(np.array([0,0,0]))
        
        threshold = 0.005
        readings=filter_readings(self.readings)
        #readings=self.readings
        for i in range(1,len(readings)):
            df = readings[i]
            
            if i == 0:
                delta_t = 0
            else:
                delta_t = (self.readings[i].timestamp - self.readings[i - 1].timestamp).total_seconds()
            
            acc = df.acel- self.baseline["acel"]
            
            acc[abs(acc) < threshold] = 0
            acc *= 9.80665
            
            #fix for orientation
            rotation_matrix=euler_angles_to_rotation_matrix(df.orientation[2],df.orientation[1],df.orientation[0])
            corrected_acc=local_to_global_direction(rotation_matrix,acc.reshape((3,1)))
            
            acc=corrected_acc.reshape((1,3))[0]
            
            #velocityx[1] = velocityx[0] + accelerationx[0] + ((accelerationx[1] - accelerationx[0])>>1)
            vel = self.vel +self.acc + ((acc-self.acc)/2) * delta_t
            
            pos = self.pos +self.vel + ((vel-self.vel)/2) * delta_t
            
            self.acc = acc
            self.vel = vel
            self.pos = pos
            
            u = np.cos(df.orientation[0]) * np.cos(df.orientation[1])
            v = (np.cos(df.orientation[2]) * np.sin(df.orientation[1]) + np.sin(df.orientation[2]) * np.sin(df.orientation[0]) * np.cos(df.orientation[1]))
            w = (-1*np.sin(df.orientation[2]) * np.sin(df.orientation[1]) + np.cos(df.orientation[2]) * np.sin(df.orientation[0]) * np.cos(df.orientation[1]))
            
            self.plot_orientation.append([u,v,w])
            #self.plot_orientation.append([df.orientation[2],df.orientation[1],df.orientation[0]])
            self.plot_data.append(self.pos)
            self.vel_data.append(self.vel)
            self.acc_data.append(self.acc)
        print(len(self.plot_data),len(self.vel_data),len(self.acc_data))
        self.readings=[]
        self.update_map()
        

def main():
    app = BaseApp()
    app.mainloop()


if __name__ == "__main__":
    main()
