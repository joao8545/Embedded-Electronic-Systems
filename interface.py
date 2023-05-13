import tkinter as tk
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import time
from datetime import datetime
#from sense_hat import SenseHat

MOCK=True
class DataFrame:
    def __init__(self,acel=None,gyro=None,orientation=None,pressure=None,mag=None,timestamp=None) -> None:
        self.acel:tuple[float,float,float]=acel
        self.gyro:tuple[float,float,float]=gyro
        self.orientation:tuple[float,float,float]=orientation
        self.pressure:tuple[float,]=pressure,
        self.mag:tuple[float,float,float]=mag
        self.timestamp:datetime=timestamp


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
        
        self.index=0
        self.baseline={
            "gyro":[0,0,0],
            "orientation":[0,0,0],
            "mag":[0,0,0],
            "acel":[0,0,0],
            "pressure":[0,]
        }
        self.calibration_running=False
        self.last_update=None
        self.vel=[0,0,0]
        self.pos=[0,0,0]
        self.acc=[0,0,0]
        self.plot_data.append(self.pos)
        self.acc_data.append(self.acc)
        self.vel_data.append(self.vel)
        self.readings:list[DataFrame]=[]
        self.start=None
        #self.sense = SenseHat()
    
    def calibrate_sensor(self,samples=50):
        def list_sum(l1,l2):
            return [sum(x) for x in zip(l1, l2)]
        i=0
        self.baseline={
            "gyro":[0,0,0],
            "orientation":[0,0,0],
            "mag":[0,0,0],
            "acel":[0,0,0],
            "pressure":[0]
        }
        while True:
            if i>=samples:
                break
            df=self.get_sensor_data()
            
            self.baseline["gyro"]=list_sum(self.baseline["gyro"],df.gyro)
            self.baseline["orientation"]=list_sum(self.baseline["orientation"],df.orientation)
            self.baseline["mag"]=list_sum(self.baseline["mag"],df.mag)
            self.baseline["acel"]=list_sum(self.baseline["acel"],df.acel)
            self.baseline["pressure"]=list_sum(self.baseline["pressure"],df.pressure)
            
            
            i+=1
        for key in self.baseline.keys():
            for index in range(len(self.baseline[key])):
                self.baseline[key][index]/=i
        self.status_label.set("calibration is done")
        print("calibration is done")
        pass
    
    def get_sensor_data(self):
        if MOCK:
            self.index+=1
            return self.mock_sensor("data\Fall-2023-05-09 15_57_58.164932.csv",self.index)
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
            a=(float(line[10]),float(line[11]),float(line[12]))
            g=(float(line[13]),float(line[14]),float(line[15]))
            o=(float(line[4]),float(line[5]),float(line[6]))
            p=(float(line[3]))
            m=(float(line[7]),float(line[8]),float(line[9]))
            t=datetime.strptime(line[0],'%Y-%m-%d %H:%M:%S.%f')
            data_frame=DataFrame(a,g,o,p,m,t)
        return data_frame
        pass
    
    def update_map(self):
        self.map.plot(*zip(*self.plot_data))
        self.map_fig.canvas.draw_idle()
        #print(self.acc_data)
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
    
    
    def calculate_orientation(self):
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
        def list_sub(a,b):
            return [a_i - b_i for a_i, b_i in zip(a, b)]
        def list_sum(l1,l2):
            return [sum(x) for x in zip(l1, l2)]
        #print(self.pos)
        threshold=0.005
        
        for i in range(len(self.readings)):
            df=self.readings[i]
            if i==0:
                delta_t=0
            else:
                delta_t=(self.readings[i].timestamp-self.readings[i-1].timestamp).total_seconds()
            acc=list_sub(df.acel,self.baseline["acel"])
            if abs(acc[0])<threshold:
                acc[0]=0
            if abs(acc[1])<threshold:
                acc[1]=0
            if abs(acc[2])<threshold:
                acc[2]=0
            acc=[x* 9.80665 for x in acc]
            self.acc=acc
            vel=list_sum(self.vel,[x*delta_t for x in acc])
            self.vel=vel
            pos=list_sum(self.pos,[x*delta_t for x in vel])
            self.pos=pos
            self.plot_data.append(self.pos)
            self.vel_data.append(self.vel)
            self.acc_data.append(self.acc)
            #print(f"acc: {acc},vel: {vel},pos {pos}")
        self.update_map()
        pass
        

def main():
    app = BaseApp()
    app.mainloop()


if __name__ == "__main__":
    main()
