import tkinter as tk
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import time
#from sense_hat import SenseHat

MOCK=True
class DataFrame:
    def __init__(self,acel=None,gyro=None,orientation=None,pressure=None,mag=None) -> None:
        self.acel:tuple[float,float,float]=acel
        self.gyro:tuple[float,float,float]=gyro
        self.orientation:tuple[float,float,float]=orientation
        self.pressure:tuple[float,]=pressure,
        self.mag:tuple[float,float,float]=mag

class Reading:
    pass

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

        fig = Figure((1, 1), 100)
        canvas = FigureCanvasTkAgg(fig, self)
        canvas.draw()

        toolbar = NavigationToolbar2Tk(canvas, self)
        canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        toolbar.update()

        ax = fig.add_subplot(111, projection="3d") 
        self.map=ax
        t = np.arange(0, 3, 0.01)
        #ax.plot(t, 2 * np.sin(2 * np.pi * t), 2 * np.cos(3 * np.pi * t))
        info_frame=tk.Frame(self)
        info_frame.pack(side=tk.RIGHT,fill=tk.BOTH,expand=1)
        
        tk.Label(info_frame,text="Acceleration").grid(row=0,column=0,columnspan=2)
        tk.Label(info_frame,text="(x,y,z) m/s2").grid(row=1,column=0,columnspan=2) 
        tk.Label(info_frame,text="Speed").grid(row=2,column=0,columnspan=2)
        tk.Label(info_frame,text="(x,y,z)m/s").grid(row=3,column=0,columnspan=2)
        tk.Label(info_frame,text="Displacement").grid(row=4,column=0,columnspan=2)
        tk.Label(info_frame,text="(x,y,z)m/").grid(row=5,column=0,columnspan=2)
        compass_fig = Figure((1, 1), 100)
        
        compass_fig.gca().get_xaxis().set_visible(False)
        compass_fig.gca().get_yaxis().set_visible(False)
        compass = FigureCanvasTkAgg(compass_fig, info_frame)
        compass.get_tk_widget().grid(row=6,column=0,rowspan=2,columnspan=2)
        compass.draw()
        ax1 = compass_fig.add_subplot(111) 
        ax1.axis('off')
        ax1.arrow(0, 0.5, 0, 0.5, head_width=0.05, head_length=0.5)
        tk.Button(info_frame,text="Calibrate",command=self.calibrate_sensor).grid(row=8,column=0,)
        tk.Button(info_frame,text="Record", command=self.process).grid(row=8,column=1,)
        tk.Button(info_frame,text="Plot", command=self.update_map).grid(row=9,column=0,)
        self.init_tracking()
    
    def init_tracking(self):
        self.plot_data=[]
        
        self.index=0
        self.baseline={
            "gyro":[0,0,0],
            "orientation":[0,0,0],
            "mag":[0,0,0],
            "acel":[0,0,0],
            "pressure":[0,]
        }
        self.last_update=None
        self.vel=[0,0,0]
        self.pos=[0,0,0]
        self.plot_data.append(self.pos)
        #self.sense = SenseHat()
    
    def calibrate_sensor(self):
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
            if i>50:
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
        yaw,pitch,roll = self.sense.get_orientation().values()
        mag_x,mag_y,mag_z = self.sense.get_compass_raw().values()
        x,y,z = self.sense.get_accelerometer_raw().values()
        gyro_x,gyro_y,gyro_z = self.sense.get_gyroscope_raw().values()
        return DataFrame([x,y,z],[gyro_x,gyro_y,gyro_z],[yaw,pitch,roll],[p],[mag_x,mag_y,mag_z])
        pass
    
    def mock_sensor(self,file_path,index)->DataFrame:
        with open(file_path,"r") as fp:
            line=fp.readlines()[index].split(",")
            a=(float(line[10]),float(line[11]),float(line[12]))
            g=(float(line[13]),float(line[14]),float(line[15]))
            o=(float(line[4]),float(line[5]),float(line[6]))
            p=(float(line[3]))
            m=(float(line[7]),float(line[8]),float(line[9]))
            data_frame=DataFrame(a,g,o,p,m)
        return data_frame
        pass
    
    def update_map(self):
        self.map.plot(*zip(*self.plot_data))
        pass
    
    def update_compass(self):
        pass
    
    def calculate_orientation(self):
        pass
    
    def update_values(self):
        self.update_map()
        self.update_compass()
        pass
    
    def process(self):
        def list_sub(a,b):
            return [a_i - b_i for a_i, b_i in zip(a, b)]
        def list_sum(l1,l2):
            return [sum(x) for x in zip(l1, l2)]
        print(self.pos)
        if self.last_update is None:
            self.last_update=time.perf_counter()
            return
        
        delta_t=self.last_update-time.perf_counter()
        self.last_update=time.perf_counter()
        df=self.get_sensor_data()
        acc=list_sub(df.acel,self.baseline["acel"])
        vel=list_sum(self.vel,[x*delta_t for x in acc])
        self.vel=vel
        pos=list_sum(self.pos,[x*delta_t for x in vel])
        self.pos=pos
        self.plot_data.append(self.pos)
        print(f"acc: {acc},vel: {vel},pos {pos}")
        self.after(100,self.process)
        pass
        

def main():
    app = BaseApp()
    app.mainloop()


if __name__ == "__main__":
    main()
