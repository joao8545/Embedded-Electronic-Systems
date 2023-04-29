import tkinter as tk
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


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
        t = np.arange(0, 3, 0.01)
        ax.plot(t, 2 * np.sin(2 * np.pi * t), 2 * np.cos(3 * np.pi * t))
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
        tk.Button(info_frame,text="Calibrate").grid(row=8,column=0,)
        tk.Button(info_frame,text="Record").grid(row=8,column=1,)
        

    def update_values(self):
        self.update_map()
        self.update_compass()
        pass


def main():
    app = BaseApp()
    app.mainloop()


if __name__ == "__main__":
    main()
