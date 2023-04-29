import tkinter as tk
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import (
                                    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure

class BaseApp(tk.Tk):

    def __init__(self, screenName: str | None = None, baseName: str | None = None,
                 className: str = "Tk", useTk: bool = True, sync: bool = False, use: str | None = None) -> None:
        super().__init__(screenName, baseName, className, useTk, sync, use)
        self.title="Position tracker"
        fig=Figure((1,1),100)
        canvas=FigureCanvasTkAgg(fig,self)
        canvas.draw()
        ax=fig.add_subplot(111,projection="3d")
        t = np.arange(0, 3, .01)
        ax.plot(t, 2 * np.sin(2 * np.pi * t),2 * np.cos(2 * np.pi * t))

        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        
    def update_values(self):
        
        pass


def main():
    app=BaseApp()
    app.mainloop()

if __name__=="__main__":
    main()


        

