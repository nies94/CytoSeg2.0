from tkinter import *
from tkinter import Tk, Label, Button
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import sys
import numpy as np
import scipy as sp
import skimage
from skimage import feature
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from packaging.version import Version

def skeletonize_graph(gaussianImage, mask, sigma, block, small, factr):
    gaussianImage -= gaussianImage[mask].min()
    gaussianImage *= 255.0 / gaussianImage.max()
    tubeImage = tube_filter(gaussianImage, sigma)
    threshold = skimage.filters.threshold_local(tubeImage, block)
    binaryImage = tubeImage > threshold
    skeletonImage = skimage.morphology.skeletonize_3d(binaryImage > 0)
    ones = np.ones((3, 3))
    cleanedImage = skimage.morphology.remove_small_objects(skeletonImage, small, connectivity=2) > 0
    cleanedImage = cleanedImage * mask
    cleanedImage = cleanedImage > 0
    labeledImage, labels = sp.ndimage.label(cleanedImage, structure=ones)
    mean = gaussianImage[cleanedImage].mean()
    means = [np.mean(gaussianImage[labeledImage == n]) for n in range(1, labels + 1)]
    intensityImage = 1.0 * cleanedImage.copy()
    for n in range(1, labels + 1):
        if(means[n-1] < mean * factr):
            intensityImage[labeledImage == n] = 0
    finalImage = skimage.morphology.remove_small_objects(intensityImage > 0, 2, connectivity=8)
    return(finalImage)

def tube_filter(gaussianImage, sigma):
    if Version(skimage.__version__) < Version('0.15'):
        hessianImage = skimage.feature.hessian_matrix(gaussianImage, sigma=sigma, mode='reflect')
        eigvalsImage = skimage.feature.hessian_matrix_eigvals(hessianImage[0], hessianImage[1], hessianImage[2])
    else:
        hessianImage = skimage.feature.hessian_matrix(gaussianImage, sigma=sigma, mode='reflect', order='xy')
        eigvalsImage = skimage.feature.hessian_matrix_eigvals(hessianImage)
    negativeImage = -1.0 * eigvalsImage[1]
    finalImage = 255.0 * (negativeImage - negativeImage.min()) / (negativeImage.max() - negativeImage.min())
    return(finalImage)

# set randw, randn and depth from parameter list
pathToPlugin = sys.argv[0]
filename = sys.argv[1]
osSystem = int(sys.argv[2])
if osSystem == 1:
    pathToPlugin = '\\'.join(pathToPlugin.split('\\')[:-1])
else:
    pathToPlugin = '/'.join(pathToPlugin.split('/')[:-1])
roll = 50
randw = 1
randn = 1
depth = 7.75


class GaugingGui:

    def __init__(self,root, filename, pathToPlugin, osSystem):
        self.root = root
        if filename == 'None':
            self.filename = ""
        else:
            self.filename = filename
        self.pathToPlugin = pathToPlugin
        self.osSystem = osSystem
        self.past = 0

        self.root.title('CytoSeg 2.0 - Gauging')
        if self.root.winfo_screenheight() > 1000:
            self.height, self.width = 800, 600
        else:
            self.height = int(self.root.winfo_screenheight() * 0.875)
            self.width = int(self.height * 0.75)
        self.root.geometry('%dx%d' % (self.width, self.height))
        self.imageHeight = int(self.height * 0.55)

        # Menu bar buttons
        self.menu = Frame(self.root)
        self.open = Button(self.menu,text="Open Image",command=self.openImage).grid(row=0, column=0)
        self.help = Button(self.menu, text="Help", command=self.helpMessage).grid(row=0, column=1)
        self.back = Button(self.menu, text="Back to Main Menu", command=self.root.quit).grid(row=0, column=2)
        self.menu.pack(side=TOP, anchor=W, padx=10,pady=10)

        # Welcome message
        self.textVar = StringVar(self.root)
        self.LabelWelcome = Label(self.root, textvariable=self.textVar, fg='dark green').pack()
        self.textVar.set("Open image to start parameter gauging.")

        # canvas for the image
        self.canvas = Canvas(self.root, width = self.imageHeight, height = self.imageHeight)
        self.canvas.pack()

        # frame for the scale bars
        self.frame = Frame(self.root)
        self.LabelSigma = Label(self.frame,text="v_width")
        self.sigma = Scale(self.frame, from_=0.4, to=2.2, resolution=0.2, orient=HORIZONTAL,length=self.imageHeight, command=self.showValueSigma, showvalue=0)
        self.sigma.set(2.0)
        self.LabelSigmaValue = Label(self.frame, text="")
        self.sigma.bind("<ButtonRelease-1>", self.displaySkeleton)

        self.LabelBlock = Label(self.frame,text="v_thres")
        self.block = Scale(self.frame, from_=20, to=112, resolution=10.0, orient=HORIZONTAL,length=self.imageHeight, command=self.showValueBlock, showvalue=0)
        self.block.set(101.0)
        self.LabelBlockValue = Label(self.frame, text="")
        self.block.bind("<ButtonRelease-1>", self.displaySkeleton)

        self.LabelSmall = Label(self.frame,text="v_size")
        self.small = Scale(self.frame, from_=2.0, to=47.0, resolution=5.0, orient=HORIZONTAL,length=self.imageHeight, command=self.showValueSmall, showvalue=0)
        self.small.set(27.0)
        self.LabelSmallValue = Label(self.frame, text="")
        self.small.bind("<ButtonRelease-1>", self.displaySkeleton)

        self.LabelFactr = Label(self.frame,text="v_int")
        self.factr = Scale(self.frame, from_=0.1, to=2.0, resolution=0.2, orient=HORIZONTAL,length=self.imageHeight, command=self.showValueFactr, showvalue=0)
        self.factr.set(0.5)
        self.LabelFactrValue = Label(self.frame,text="")
        self.factr.bind("<ButtonRelease-1>", self.displaySkeleton)

        self.LabelSigma.grid(row=0, column=0, sticky=S, pady=10)
        self.sigma.grid(row=0, column=4, pady=10)
        self.LabelSigmaValue.grid(row=0, column=20, sticky=E, pady=10)
        self.LabelBlock.grid(row=1, column=0, sticky=S, pady=10)
        self.block.grid(row=1, column=4, pady=10)
        self.LabelBlockValue.grid(row=1, column=20, sticky=E, pady=10)
        self.LabelSmall.grid(row=2, column=0, sticky=S, pady=10)
        self.small.grid(row=2, column=4, pady=10)
        self.LabelSmallValue.grid(row=2, column=20, sticky=E, pady=10)
        self.LabelFactr.grid(row=3, column=0, sticky=S, pady=10)
        self.factr.grid(row=3,column=4, pady=10)
        self.LabelFactrValue.grid(row=3, column=20, sticky=E, pady=10)

        self.frame.pack(side=TOP,padx=10,pady=5)

        # button to submit parameters
        self.Final = Button(self.root,text='Choose Parameters',command=self.get_parameters).pack(anchor=CENTER)

    # select image and open in canvas
    def openImage(self):
        if self.osSystem == 1:
            self.lastdir = self.pathToPlugin
        else:
            self.lastdir = './'
        if self.filename == "" or self.past == 1:
            self.filename = filedialog.askopenfilename(initialdir = self.lastdir, title ="Select image!",filetypes = (("png images","*.png") , ("tif images","*.tif"), ("jpeg images","*.jpg")) )
        self.img = Image.open(self.filename)
        if self.img.size[0] == self.img.size[1]:
            self.resized = self.img.resize((self.imageHeight, self.imageHeight),Image.ANTIALIAS)
        else:
            self.max, self.argmax = np.max(self.img.size), np.argmax(self.img.size)
            self.min = (np.min(self.img.size)*self.imageHeight)/self.max
            if self.argmax == 0:
                self.resized = self.img.resize((self.imageHeight,int(self.min)),Image.ANTIALIAS)
            else:
                self.resized = self.img.resize((int(self.min),self.imageHeight),Image.ANTIALIAS)
        self.image = ImageTk.PhotoImage(self.resized)
        self.canvas.create_image(0, 0, anchor=NW, image=self.image)
        if self.filename != "":
            self.lastdir = os.path.dirname(self.filename)
        self.textVar.set("Change segmentation by adjusting parameter controllers.")
        self.past = 1

    # message that pops up when clicking Help
    def helpMessage(self):
        messagebox.showinfo("Parameter information","v_width: width of filamentous structures to enhance with a 2D tubeness filter,\n\nv_thres: block size for adaptive median threshold,\n\nv_size: size of small objects to be removed,\n\nv_int: lowest average intensity of a component")


    # have to cheat here, scale bar is not showing the intervals for block, small and factr as it should...
    def showValueSigma(self,ev):
        self.LabelSigmaValue.configure(text=ev)
    def showValueBlock(self,ev):
        number = int(ev)+1
        self.LabelBlockValue.configure(text=number)
    def showValueSmall(self,ev):
        number = int(ev)+2
        self.LabelSmallValue.configure(text=number)
    def showValueFactr(self,ev):
        number = format(float(ev)-0.1,".1f")
        self.LabelFactrValue.configure(text=number)

    # save the selected parameters in a file
    def get_parameters(self):
        params = "" + str(roll) + ","+ str(randw) + "," + str(randn) + "," + str(depth) + "," + str(self.sigma.get()) + "," + str(self.block.get()+1) + "," + str(self.small.get()+2) + "," + str(format(float(self.factr.get())-0.1,".1f"))
        if self.osSystem == 1:
            np.savetxt(self.pathToPlugin+"\\defaultParameter.txt",[params],fmt='%s')
        else:
            np.savetxt(self.pathToPlugin+"/defaultParameter.txt",[params],fmt='%s')

    def displaySkeleton(self,ev):
        self.textVar.set("If you are satisfied with the segmentation, press 'Choose Parameters' to save\n the parameters for the CytoSeg analysis and go back to the main menu.")
        if self.filename!="":
            sigma = self.sigma.get()
            block = self.block.get()+1
            small = self.small.get()+2
            factr = self.factr.get()-0.1

            path = self.filename
            if self.osSystem == 1:
                path = path.replace("/", "\\")
                imageName = path.split('\\')[-1].split('.')[0]
                imageName = imageName.replace("_filter", "")
                imagePath = '\\'.join(path.split('\\')[:-1])
                rawImage = skimage.io.imread(self.filename, plugin='tifffile')
                mask = skimage.io.imread(imagePath+'\\'+imageName+"_mask.tif", plugin='tifffile')>0
            else:
                imageName = path.split('/')[-1].split('.')[0]
                imageName = imageName.replace("_filter", "")
                imagePath = '/'.join(path.split('/')[:-1])
                rawImage = skimage.io.imread(self.filename, plugin='tifffile')
                mask = skimage.io.imread(imagePath+'/'+imageName+"_mask.tif", plugin='tifffile')>0

            shape = rawImage.shape
            if len(shape) == 2: #grayscale single image
                firstImage = rawImage.copy()
            elif len(shape) == 3:
                if shape[2] in [3,4]: #rgb single image
                    grayscaleImage = skimage.color.rgb2gray(rawImage)
                    firstImage = grayscaleImage.copy()
                else: #grayscale image stack
                    firstImage = rawImage[0]
            else: #rgb image stack
                grayscaleImage = skimage.color.rgb2gray(rawImage)
                firstImage = grayscaleImage[0]
            gaussianImage = skimage.filters.gaussian(firstImage, sigma)
            skeletonImage = skeletonize_graph(gaussianImage, mask, sigma, block, small, factr)

            fig = plt.figure()
            plt.imshow(firstImage, cmap='gray_r')
            binarySkeletonImage = np.ma.masked_where(skeletonImage == 0, skeletonImage)
            plt.imshow(binarySkeletonImage, cmap='autumn')
            plt.axis('off')
            if self.osSystem == 1:
                fig.savefig(imagePath+'\\skeletonOnImage.png', bbox_inches='tight', dpi=300)
                self.img = Image.open(imagePath+'\\skeletonOnImage.png')
            else:
                fig.savefig(imagePath+'/skeletonOnImage.png', bbox_inches='tight', dpi=300)
                self.img = Image.open(imagePath+'/skeletonOnImage.png')

            imageHeight = self.height * 0.625
            if self.img.size[0] == self.img.size[1]:
                self.resized = self.img.resize((self.imageHeight, self.imageHeight),Image.ANTIALIAS)
            else:
                self.max, self.argmax = np.max(self.img.size), np.argmax(self.img.size)
                self.min = (np.min(self.img.size)*self.imageHeight)/self.max
                if self.argmax == 0:
                    self.resized = self.img.resize((self.imageHeight,int(self.min)),Image.ANTIALIAS)
                else:
                    self.resized = self.img.resize((int(self.min),self.imageHeight),Image.ANTIALIAS)
            self.image = ImageTk.PhotoImage(self.resized)
            self.canvas.create_image(0, 0, anchor=NW, image=self.image)



master = Tk()
my_gui = GaugingGui(master, filename, pathToPlugin, osSystem)
master.mainloop()
