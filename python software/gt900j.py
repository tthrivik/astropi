#!/usr/bin/python
import os
import struct
import pygame, sys
import datetime
import time
import math
from pygame.locals import *
import pygame.camera
import shutil
import random
import numpy
import subprocess
import RPi.GPIO as GPIO
import signal

#FOR TESTING / simulation ONLY, 1 for normal use
# setting camera_connected = 0 will run in demo mode
camera_connected = 1
# set serial_connected = 0 if you don't have the Arduino Uno etc connected
serial_connected = 0

#==================================================================================================
# if using the RPi camera set use_RPicamera = 1 , if set to 0 the program will use a USB camera.
use_RPiwebcam = 1

# if you find the program won't work with your webcam try testing with use_fswebcam set to 1.
# if using fswebcam ensure you have installed it !! (sudo apt-get install fswebcam).
# it maybe slower than using default of pygame.camera, it's limited to 352 x 288 .
use_fswebcam = 0

#c270_camera - I found my Logitech C270 won't always start with pygame.camera
#starting with fswebcam and then back to pygame.camera fixes it !
#ensure you install fswebcam, with 'sudo apt-get install fswebcam' if you need to use it
c270_camera = 0

#==================================================================================================
# SETTINGS
# max_res - webcam max available resolution, depends on your webcam
# 0 = 352x288, 1 = 640x480, 2 = 800x600, 3 = 960x720, 4 = 1920x1440, 5 = 2592x1944
# Only use > 3 for RPi camera, and will be slow.
max_res = 5

# bits - bits to display in pygame, the lower speeds things up
# best picture = 16, if you can live with 12 or 8 try that
bits = 16

#==================================================================================================
# SET DEFAULT CONFIG
#==================================================================================================
# auto_g - autoguide on = 1, off = 0
auto_g = 0
# nsscale - North/South scaling in milliSecs/pixel, 150 for 400mm focal length guide scope
nscale = 150
sscale = 150
# ewscale - East / West scaling in milliSecs/pixel, 150 for 400mm focal length guide scope
escale = 150
wscale = 150
# ewi - Invert East <> West invert = 1, non-invert = 0
ewi = 0
# nsi - Invert North<>South invert = 1, non-invert = 0
nsi = 0
# crop - Tracking Window size in pixels. ONLY use 32,64,96 or 128
crop = 32
# offset3/4 - Tracking Window offset from centre of screen
offset3 = 0
offset4 = 0
# Intervals - Guiding Interval in seconds (approx)
Intervals = 2
# log - Log commands to .txt file, on = 1, off = 0
log = 0
# frames - RGBW = 1234
frames = 4
# Sens - sensitivity (Threshold)
Sens = 20
# threshold - on = 1,off = 0. Displays detected star pixels
thres = 0
# graph - on = 1, off = 0. shows brightness of star, and threshold value
graph = 0
# noise reduction - on = 1, off =0. averages over 2 frames
nr = 0
# plot - plot movements, on = 1, off = 0
plot = 0
# auto_win - auto size tracking window, on = 1, off = 0
auto_win = 0
# auto_t - auto threshold, on = 1, off = 0
auto_t = 0
#crop_img - set to give cropped image, higher magnification
crop_img = 0

# RPI camera presets
rpico = 90
rpibr = 70
rpiex = 'off'
rpiISO = 0
rpit = 800
rpiev = 0
rpisa =  0
rpiss = 100000

vtime = 0
htime = 0

#===================================================================================
#SETUP GPIO
N_OP = 22
S_OP = 18
E_OP = 24
W_OP = 16
GPIO.setwarnings(False)
GPIO.setmode (GPIO.BOARD)
GPIO.setup(N_OP, GPIO.OUT)
GPIO.output(N_OP,GPIO.LOW)
GPIO.setup(S_OP, GPIO.OUT)
GPIO.output(S_OP,GPIO.LOW)
GPIO.setup(E_OP, GPIO.OUT)
GPIO.output(E_OP,GPIO.LOW)
GPIO.setup(W_OP, GPIO.OUT)
GPIO.output(W_OP,GPIO.LOW)

#==============================================================================
# mincor - Minimum correction (mSecs)
mincor = 90
#a_thr_scale - sets scaling factor for auto_t
global a_thr_scale
a_thr_scale = 2
#a_thr_limit - sets lower limit for auto threshold to work
a_thr_limit = 14
#auto_i - auto-interval
auto_i = 1
#==============================================================================
if serial_connected == 1:
   import serial
   
pygame.init()
imu=""
limg = 0
Interval = Intervals
pimg=""
if use_fswebcam == 1:
   crop_img = 0
if crop_img == 0:
   w = 352
   h = 288
if crop_img == 1:
   w = 640
   h = 480
if crop_img == 2:
   w = 800
   h = 600
if crop_img == 3:
   w = 960
   h = 720
if crop_img == 4:
   w = 1920
   h = 1440
if crop_img == 5:
   w = 2592
   h = 1944
   
mxo=[]
width = 352
height = 288
offset5 = 0
offset6 = 0
track = 0
rgb=['X','R','G','B','W']
fontObj = pygame.font.Font(None,16)
redColor = pygame.Color(255,0,0)
blueColor = pygame.Color(0,0,255)
greenColor = pygame.Color(0,255,0)
greyColor = pygame.Color(128,128,128)
dgryColor = pygame.Color(64,64,64)
lgryColor = pygame.Color(192,192,192)
blackColor = pygame.Color(0,0,0)
whiteColor = pygame.Color(255,255,255)
purpleColor = pygame.Color(255,0,255)
windowSurfaceObj = pygame.display.set_mode((640,height + 192),1,bits)
pygame.display.set_caption('AutoGuider_BETA_90')
if c270_camera == 1:
   path = 'fswebcam -S2 -r352x288 /tmp/test.jpg'
   os.system (path)
if camera_connected == 1 and use_fswebcam == 0 and use_RPiwebcam == 0:
   pygame.camera.init()
   if crop_img == 0:
      cam = pygame.camera.Camera("/dev/video0",(352,288))
   if crop_img == 1 and max_res >= 1:
      cam = pygame.camera.Camera("/dev/video0",(640,480))
   if crop_img == 2 and max_res >= 2:
      cam = pygame.camera.Camera("/dev/video0",(800,600))
   if crop_img == 3 and max_res >= 3:
      cam = pygame.camera.Camera("/dev/video0",(960,720))
   cam.start()

def button (bx1,by1,bx2,by2,height,bColor):
   greyColor = pygame.Color(128,128,128)
   dgryColor = pygame.Color(64,64,64)
   blackColor = pygame.Color(0,0,0)
   whiteColor = pygame.Color(255,255,255)
   pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx1,height+by1,bx2,by2))
   pygame.draw.line(windowSurfaceObj,whiteColor,(bx1,height+by1),(bx1+bx2+1,height+by1))
   pygame.draw.line(windowSurfaceObj,whiteColor,(bx1+1,height+by1+1),(bx1+bx2,height+by1+1))
   pygame.draw.line(windowSurfaceObj, greyColor,(bx1,height+by1),(bx1,height+by1+30))
   pygame.draw.line(windowSurfaceObj, greyColor,(bx1+1,height+by1+1),(bx1+1,height+by1+29))
   return()

if auto_g ==0:
   button (1,33,127,31,height,greyColor)
if auto_g ==1:
   button (1,33,127,31,height,dgryColor)
if auto_win ==0:
   button (1,65,63,31,height,greyColor)
if auto_win ==1:
   button (1,65,63,31,height,dgryColor)
if auto_t ==0:
   button (65,65,63,31,height,greyColor)
if auto_t ==1:
   button (65,65,63,31,height,dgryColor)
if log ==0:
   button (1,97,63,31,height,greyColor)
if log ==1:
   button (1,97,63,31,height,dgryColor)
if nr ==0:
   button (65,97,63,31,height,greyColor)
if nr ==1:
   button (65,97,63,31,height,dgryColor)
if graph ==0:
   button (1,129,63,31,height,greyColor)
if graph ==1:
   button (1,129,63,31,height,dgryColor)
if plot ==0:
   button (65,129,63,31,height,greyColor)
if plot ==1:
   button (65,129,63,31,height,dgryColor)
if thres ==0:
   button (1,161,63,31,height,greyColor)
if thres ==1:
   button (1,161,63,31,height,dgryColor)
button (161,33,63,31,height,greyColor)
button (161,65,63,31,height,greyColor)
button (161,97,63,31,height,greyColor)
button (161,129,63,31,height,greyColor)
button (161,161,63,31,height,greyColor)

button (257,33,63,31,height,greyColor)
button (257,65,63,31,height,greyColor)
button (257,97,63,31,height,greyColor)
button (257,129,63,31,height,greyColor)
button (257,161,63,31,height,greyColor)
button (65,161,31,31,height,greyColor)
button (97,161,31,31,height,greyColor)

if use_RPiwebcam == 1:

   button (385,1,63,31,0,greyColor)
   button (385,33,63,31,0,greyColor)
   button (385,65,63,31,0,greyColor)
   button (385,97,63,31,0,greyColor)
   button (385,129,63,31,0,greyColor)
   button (385,161,63,31,0,greyColor)
   
button (385,65,31,31,height,greyColor)
button (449,65,31,31,height,greyColor)
button (513,65,31,31,height,greyColor)
button (577,65,31,31,height,greyColor)

button (417,33,31,31,height,greyColor)
button (545,33,31,31,height,greyColor)
button (417,97,31,31,height,greyColor)
button (545,97,31,31,height,greyColor)

button (385,161,31,31,height,greyColor)
button (417,161,31,31,height,greyColor)
button (449,161,31,31,height,greyColor)

button (513,161,31,31,height,greyColor)
button (545,161,31,31,height,greyColor)
button (577,161,31,31,height,greyColor)

button (609,0,31,31,height,redColor)
   
def keys(msg,fsize,fcolor,fx,fy,upd):
   fontObj = pygame.font.Font('freesansbold.ttf',fsize)
   msgSurfaceObj = fontObj.render(msg, False, fcolor)
   msgRectobj = msgSurfaceObj.get_rect()
   msgRectobj.topleft =(fx,fy)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             
   windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
   if upd ==1:
      pygame.display.update(pygame.Rect(fx,fy,32,32))
   return()

keys (str(nscale),16,whiteColor,323,height+36,0)
keys (str(sscale),16,whiteColor,322,height+66,0)
keys (str(escale),16,whiteColor,323,height+98,0)
keys (str(wscale),16,whiteColor,322,height+130,0)
keys (str(Sens),16,whiteColor,230,height+98,0)
keys (str(Interval),16,whiteColor,230,height+130,0)
keys (str(crop_img),16,whiteColor,232,height+164,0)

if use_RPiwebcam == 1:
   keys (str(rpibr),14,whiteColor,455,10,0)
   keys (str(rpico),14,whiteColor,455,42,0)
   keys (str(rpiss/1000),14,whiteColor,455,74,0)
   keys ((rpiex),14,whiteColor,455,106,0)
   keys (str(rpiISO),14,whiteColor,455,138,0)
   keys (str(rpiev),14,whiteColor,455,170,0)
   if rpiISO == 0:
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(455,138, 31, 31))
      keys ('off',14,redColor,455,138,0)
   if rpiev == 0:
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(455,170, 31, 31))
      keys ('off',14,redColor,455,170,0)
   
msg = rgb[frames]
if frames == 1:
   keys (msg,16,redColor,230,height+34,0)
if frames == 2:
   keys (msg,16,greenColor,230,height+34,0)
if frames == 3:
   keys (msg,16,blueColor,230,height+34,0)
if frames == 4:
   keys (msg,16,whiteColor,230,height+34,0)
  
keys (str(crop),16,whiteColor,230,height+66,0)
if auto_win == 0:
   keys ("A-Win",16,dgryColor,11,height+71,0)
else:
   keys ("A-Win",16,greenColor,11,height+71,0)
if auto_t == 0:
   keys ("A-Thr",16,dgryColor,76,height+71,0)
else:
   keys ("A-Thr",16,greenColor,76,height+71,0)
if auto_g == 0:
   keys ("AutoGuide",16,dgryColor,22,height+39,0)
else:
   keys ("AutoGuide",16,greenColor,22,height+39,0)
if log == 0:
   keys ("Log",16,dgryColor,15,height+103,0)
else:
   keys ("Log",16,greenColor,15,height+103,0)
if graph == 0:
   keys ("Graph",16,dgryColor,11,height+135,0)
else:
   keys ("Graph",16,greenColor,11,height+135,0)
if plot == 0:
   keys ("Plot",16,dgryColor,81,height+135,0)
else:
   keys ("Plot",16,greenColor,81,height+135,0) 
if thres == 0:
   keys ("Thres",16,dgryColor,11,height+167,0)
else:
   keys ("Thres",16,greenColor,11,height+167,0)
if nsi == 0:
   keys ("NSi",14,dgryColor,68,height+169,0)
else:
   keys ("NSi",14,greenColor,68,height+169,0)
if ewi == 0:
   keys ("EWi",14,dgryColor,100,height+169,0)
else:
   keys ("EWi",14,greenColor,100,height+169,0)
if nr == 0:
   keys ("NR",14,dgryColor,82,height+106,0)
else:
   keys ("NR",14,greenColor,82,height+106,0)


keys ("rgbw",14,whiteColor,175,height+33,0)
keys ("-      +",18,whiteColor,170,height+42,0)
keys ("window",14,whiteColor,166,height+65,0)
keys ("-      +",18,whiteColor,170,height+74,0)
keys ("threshold",14,whiteColor,161,height+97,0)
keys ("-      +",18,whiteColor,170,height+106,0)
keys ("interval",14,whiteColor,165,height+129,0)
keys ("-      +",18,whiteColor,170,height+138,0)
keys ("Zoom",14,whiteColor,174,height+162,0)
keys ("-      +",18,whiteColor,170,height+170,0)
keys ("scale N",14,whiteColor,263,height+32,0)
keys ("-     +",18,whiteColor,270,height+42,0)
keys ("scale S",14,whiteColor,263,height+64,0)
keys ("-     +",18,whiteColor,270,height+74,0)
keys ("scale E",14,whiteColor,263,height+96,0)
keys ("-     +",18,whiteColor,270,height+106,0)
keys ("scale W",14,whiteColor,263,height+128,0)
keys ("-     +",18,whiteColor,270,height+138,0)
keys ("scale all",14,whiteColor,260,height+160,0)
keys ("-     +",18,whiteColor,270,height+170,0)

if use_RPiwebcam == 1:
   keys ("Brightness",12,whiteColor,385,5,0)
   keys ("-     +",18,whiteColor,395,13,0)
   keys ("Contrast",12,whiteColor,392,37,0)
   keys ("-     +",18,whiteColor,395,45,0)
   keys ("Exp Time",12,whiteColor,388,69,0)
   keys ("-  mS +",14,whiteColor,393,80,0)
   keys ("ISO",12,whiteColor,408,133,0)
   keys ("-     +",18,whiteColor,395,141,0)
   keys ("EV",12,whiteColor,408,165,0)
   keys ("-     +",18,whiteColor,395,172,0)
   keys ("Exp Mode",12,whiteColor,388,102,0)
   keys ("<     >",18,whiteColor,395,110,0)

hor = 0
while hor < 130:
   keys ("N",18,whiteColor,427+hor,height+38,0)
   keys ("E",18,whiteColor,460+hor,height+70,0)
   keys ("S",18,whiteColor,427+hor,height+102,0)
   keys ("W",18,whiteColor,393+hor,height+70,0)
   hor +=129
keys ("1",14,whiteColor,398,height+168,0)
keys ("2",14,whiteColor,429,height+168,0)
keys ("3",14,whiteColor,460,height+168,0)
keys ("1",14,whiteColor,398+128,height+168,0)
keys ("2",14,whiteColor,429+128,height+168,0)
keys ("3",14,whiteColor,460+128,height+168,0)
keys ("RELOAD config        SAVE config",14,whiteColor,380,height+142,0)

keys ("TELESCOPE",14,whiteColor,391,height+14,0)
keys (" WINDOW",14,whiteColor,528,height+14,0)
keys ("s",18,greyColor,428,height+68,0)
keys ("c",18,greyColor,557,height+68,0)
keys ("x",18,whiteColor,620,height+5,0)
keys ("pc",14,greyColor,618,height+135,0)
keys ("sc",14,greyColor,618,height+166,0)

def demo(width,height,posx,posy,blankline,wd,hd):

   ad = width
   bd = height
   imu = ""
   height = 1
   line =""
   while height < posy:
      line = line + blankline
      height +=1
   imu = imu + line
   height = posy
   while height < posy + hd:
      byte = blankline[0:((posx-1)*3)]
      imu = imu + byte
      width = posx
      while width < posx + wd :
         cd = (width - posx)
         if cd <= (wd/2):
             fd = (cd )+2
         if cd > wd/2 :
             fd = ((wd - cd))+2
         dd = (height - posy)
         if dd<= (hd/2):
             l = (dd )+2
         if dd > hd/2 :
             l = ((hd - dd))+2
         fe = fd * l
         if fe > 255:
            fe = 255
         byte = chr(fe)+chr(fe)+chr(fe)
         imu = imu + byte
         width +=1
      byte = blankline[0:((ad+1)-width)*3]
      imu = imu + byte
      height +=1
   height = posy + hd
   line = ""
   while height < bd + 1:
      line = line + blankline
      height +=1
   imu = imu + line
   return (imu)
   
def picture (width,height,crop,offset3,offset4,offset5,offset6,frames,Sens,camera_connected,redline,greline,bluline,gryline,blankline,imu,mxo,use_fswebcam,auto_t,arp,crop_img,w,h,rpico,rpibr,rpit,rpiex,rpiISO,rpiss,vtime,htime):
# take picture
   offset1 = ((width/2) - (crop/2))+ offset3
   offset2 = ((height/2) - (crop/2))+ offset4

   if camera_connected == 1 and use_fswebcam == 0 and use_RPiwebcam == 0:
      image = cam.get_image()
      if crop_img == 0:
         offset5 = offset3
         offset6 = offset4
         if offset5 > 0 and offset5 >= (w/2)-(width/2):
            offset5 = (w/2)-(width/2)
         if offset5 < 0 and offset5 <= 0-((w/2)-(width/2)):
            offset5 = 0-((w/2)-(width/2))
         if offset6 > 0 and offset6 >= (h/2)-(height/2):
            offset6 = (h/2)-(height/2)
         if offset6 < 0 and offset6 <= 0-((h/2)-(height/2)):
            offset6 = 0-((h/2)-(height/2))
      if crop_img > 0:
         strim1 = pygame.image.tostring(image,"RGB",1)
         x = ((h/2)-(height/2)) - offset6
         strt = w * 3 * x
         imb = ""
         c = 0
         stas = (((w/2) - (width/2)) + offset5) * 3
         while c < height:
            ima = strim1[strt:strt+(w*3)]
            imd = ima[stas : stas + (width*3)]
            imb = imb + imd
            strt +=(w*3)
            c +=1
         image = pygame.image.fromstring(imb,(width,height),"RGB",1)
      catSurfaceObj = image
      windowSurfaceObj.blit(catSurfaceObj,(0,0))
      strim = pygame.image.tostring(image,"RGB",1)
      t2=time.time()
      if vtime < t2:
         keys ("N",18,whiteColor,427,height+38,1)
         GPIO.output(N_OP,GPIO.LOW)
         keys ("S",18,whiteColor,427,height+102,1)
         GPIO.output(S_OP,GPIO.LOW)
      if htime < t2:
         keys ("W",18,whiteColor,393,height+70,1)
         GPIO.output(E_OP,GPIO.LOW)
         keys ("E",18,whiteColor,460,height+70,1)
         GPIO.output(W_OP,GPIO.LOW)
        
   if camera_connected == 1 and use_fswebcam == 1:
      path = 'fswebcam -S2 -r352x288 /run/shm/test.jpg'
      p=subprocess.Popen(path,shell=True, preexec_fn=os.setsid)
      while os.path.isfile('/run/shm/test.jpg') != True:
         t2=time.time()
         if vtime < t2:
            keys ("N",18,whiteColor,427,height+38,1)
            GPIO.output(N_OP,GPIO.LOW)
            keys ("S",18,whiteColor,427,height+102,1)
            GPIO.output(S_OP,GPIO.LOW)
         if htime < t2:
            keys ("W",18,whiteColor,393,height+70,1)
            GPIO.output(E_OP,GPIO.LOW)
            keys ("E",18,whiteColor,460,height+70,1)
            GPIO.output(W_OP,GPIO.LOW)
            
      image = pygame.image.load('/run/shm/test.jpg')
      os.remove('/run/shm/test.jpg')
      os.killpg(p.pid, signal.SIGTERM)
      catSurfaceObj = image
      windowSurfaceObj.blit(catSurfaceObj,(0,0))
      strim = pygame.image.tostring(catSurfaceObj,"RGB",1)
        
   if camera_connected == 1 and use_RPiwebcam == 1:

      rpistr = "raspistill -o /run/shm/test.jpg -co " + str(rpico) + " -br " + str(rpibr)
      if rpiex != 'off':
         rpistr = rpistr + " -t 800 -ex " + rpiex
      else:
         rpistr = rpistr + " -t 10 -ss " + str(rpiss)
      if rpiISO > 0:
         rpistr = rpistr + " -ISO " + str(rpiISO)
      if rpiev != 0:
         rpistr = rpistr + " -ev " + str(rpiev)
      rpistr = rpistr + " -n -sa " + str(rpisa) 
      
      if crop_img == 0 :
         offset5 = offset3
         offset6 = offset4
         if offset5 > 0 and offset5 >= (w/2)-(width/2):
            offset5 = (w/2)-(width/2)
         if offset5 < 0 and offset5 <= 0-((w/2)-(width/2)):
            offset5 = 0-((w/2)-(width/2))
         if offset6 > 0 and offset6 >= (h/2)-(height/2):
            offset6 = (h/2)-(height/2)
         if offset6 < 0 and offset6 <= 0-((h/2)-(height/2)):
            offset6 = 0-((h/2)-(height/2))
      if crop_img == 0:
         path = rpistr + " -w 352 -h 288"
      if crop_img == 1:
         path = rpistr + " -w 640 -h 480"
      if crop_img == 2:
         path = rpistr + " -w 800 -h 600"
      if crop_img == 3:
         path = rpistr + " -w 960 -h 720"
      if crop_img == 4:
         path = rpistr + " -w 1920 -h 1440"
      if crop_img == 5:
         path = rpistr + " -w 2592 -h 1944"
      p=subprocess.Popen(path,shell=True, preexec_fn=os.setsid)
      #stim = time.time()
      while os.path.isfile('/run/shm/test.jpg') != True:
         t2=time.time()
         if vtime < t2:
            keys ("N",18,whiteColor,427,height+38,1)
            GPIO.output(N_OP,GPIO.LOW)
            keys ("S",18,whiteColor,427,height+102,1)
            GPIO.output(S_OP,GPIO.LOW)
         if htime < t2:
            keys ("W",18,whiteColor,393,height+70,1)
            GPIO.output(E_OP,GPIO.LOW)
            keys ("E",18,whiteColor,460,height+70,1)
            GPIO.output(W_OP,GPIO.LOW)
      #ftim = time.time()
      #print ftim-stim
      image = pygame.image.load('/run/shm/test.jpg')
      os.remove('/run/shm/test.jpg')
      os.killpg(p.pid, signal.SIGTERM)
      if crop_img > 0:
         strim1 = pygame.image.tostring(image,"RGB",1)
         x = ((h/2)-(height/2)) - offset6
         strt = w * 3 * x
         imb = ""
         c = 0
         stas = (((w/2) - (width/2)) + offset5) * 3
         while c < height:
            ima = strim1[strt:strt+(w*3)]
            imd = ima[stas : stas + (width*3)]
            imb = imb + imd
            strt +=(w*3)
            c +=1
         image = pygame.image.fromstring(imb,(width,height),"RGB",1)
      catSurfaceObj = image
      windowSurfaceObj.blit(catSurfaceObj,(0,0))
      strim = pygame.image.tostring(image,"RGB",1)

   if camera_connected == 0:
      image = pygame.image.fromstring(imu,(width,height),"RGB",1) 
      catSurfaceObj = image
      windowSurfaceObj.blit(catSurfaceObj,(0,0))
      strim = imu

# crop picture
   x = (((height/2)-(crop/2)) - offset4)
   strt = width * 3 * x
   imb = ""
   c = 0
   stas = ((((width/2) - (crop/2))+offset3) * 3)
   while c < crop:
      ima = strim[strt:strt+(width*3)]
      imd = ima[stas : stas + (crop*3)]
      imb = imb + imd
      strt +=(width*3)
      c +=1
   
# initialise arrays
   ars = {}
   art = {}
   ars1 = {}
   art1 = {}
   arp = {}
   
# read and store in array arr
   lcounter = 0
   count = 1
   while count <= 258:
      arp[count] = 0
      count +=1
         
   mx = []
   my = []
   if frames < 4:
      xcounter = frames-1
      mz = 3
      while xcounter < (crop*crop*3):
         ima = imb[xcounter:xcounter+1]
         mx.append(ord(ima))
         xcounter += mz
         
   if frames == 4:
      xcounter = 0
      mz = 3
      while xcounter < (crop*crop*3):
         ima = (ord(imb[xcounter:xcounter+1]) + ord(imb[xcounter+1:xcounter+2]) + ord(imb[xcounter+2:xcounter+3]))/3
         mx.append(ima)
         xcounter += mz

   if nr == 0 or (len(mx) != len(mxo)):
      mxo = mx
   if nr == 1 and (len(mx) == len(mxo)):
      ar3 = (numpy.array(mx) + numpy.array(mxo))/2  
      mxo = mx
      mx = ar3

   xcounter = 1
   while xcounter < crop*crop:
      imq = mx[xcounter]
      if imq > 255:
         imq = 255
      arp[imq+1] = arp[imq+1] +1
      xcounter +=1
      
   count = 1
   mintot = 0
   maxtot = 0
   totm = 0
   while count <= 258:
      val = arp[count]
      totm = totm + val                                                                                                                   
      if totm < (crop * crop) * 0.02:
         mintot = count
      if totm < (crop * crop) - 11 :
         maxtot = count
      count +=1
   if auto_t == 0:
      pcont = maxtot - Sens
   if auto_t == 1:
      pcont = maxtot - ((maxtot-mintot)/a_thr_scale)
      Sens = ((maxtot-mintot)/a_thr_scale)
      if Sens <= a_thr_limit:
         Sens = (maxtot -mintot)+1 
         pcont = maxtot - Sens

   if graph == 1:
      pox = 588
      poy = 10
      pov = 50
      pygame.draw.line(windowSurfaceObj, greyColor, (pox-1,poy-1),(pox+pov+1,poy-1))
      pygame.draw.line(windowSurfaceObj, greyColor, (pox+pov+1,poy-1),(pox+pov+1,poy+257))
      pygame.draw.line(windowSurfaceObj, greyColor, (pox+pov+1,poy+257),(pox-1,poy+257))
      pygame.draw.line(windowSurfaceObj, greyColor, (pox-1,poy+257),(pox-1,poy-1))
      count = 0
      img = ""
      while count < 256:
         if count != maxtot and count != mintot and count != pcont:
            val = arp[count+1]
            val2 = int((30 * math.log10(val + 10))-29)
            if val2 > 49:
               val2 = 49
            if val2 < 1:
               val2 = 1
            if val2 <= 1:
               byte = blankline[0:pov*3]
            if val2 > 1:
               if frames == 1:
                  byte = redline[0:(val2)*3]
               if frames == 2:
                  byte = greline[0:(val2)*3]
               if frames == 3:
                  byte = bluline[0:(val2)*3]
               if frames == 4:
                  byte = gryline[0:(val2)*3]
               byte = byte + blankline[0:(pov-val2)*3]
            img = img + byte
         if count == maxtot:
            mcount = 0                                                                                                                                         
            while mcount < pov:
               img = img + " zz"
               mcount +=1
         if count == mintot:
            mcount = 0
            while mcount < pov:
               img = img + " zz"
               mcount +=1
         if count == pcont :
            mcount = 0
            while mcount < pov:
               img = img + "zz "
               mcount +=1
         count +=1
      if len(img) > (pov*256*3):
         img = img[0:(pov*256*3)]
      imageg = pygame.image.fromstring(img,(pov,256),"RGB",1) 
      catSurfaceObj = imageg
      windowSurfaceObj.blit(catSurfaceObj,(pox,poy))

   pic =""   
   counter = 0
   while counter < (crop*crop):
      counter +=1
      loc = (counter-1)
      ima = mx[loc]
      if ima < pcont or pcont < mintot:
         mx[loc] = 0
         if thres == 1:
            pic = pic + imb[loc*3:(loc*3)+3]
      else:
         mx[loc] = 1
         if thres == 1:
            pic = pic + chr(255)+chr(255)+chr(0)
   if thres == 1:
      imagep = pygame.image.fromstring(pic,(crop,crop),"RGB",1) 
      catSurfaceObj = imagep
      windowSurfaceObj.blit(catSurfaceObj,((width/2)-(crop /2)+offset3,(height/2)-(crop /2)+offset4))
      
   ycounter = 0
   zcounter = 0
   xcounter = 0
   while zcounter < crop*crop:
      my.append(mx[ycounter])      
      ycounter +=crop
      if ycounter > (crop * crop)- 1:
         xcounter +=1
         ycounter = xcounter
      zcounter +=1
           
# calculate line totals and store in array ars
   lcounter = 0
   while lcounter <= (crop-1):
      lcounter +=1
      loc = (lcounter-1)* crop
      ltotal = sum(mx[loc:loc+crop])
      ars[lcounter]= ltotal
      if lcounter <= crop/2 :
         loffset = (lcounter - (crop/2))-1
      else:
         loffset = (lcounter - (crop/2))
      ars1[lcounter] = (ltotal*loffset)
# calculate line value from array ars
   lcounter = 0
   ltot = 0
   toptotal = 0
   bottotal = 0
   while lcounter <= crop-1:
      lcounter +=1
      ima = ars[lcounter]
      iml = ars1[lcounter]
      ltot = ltot + iml
      if lcounter <= (crop/2):
         toptotal = toptotal + ima
      else:
         bottotal = bottotal +ima
   lpcount = (toptotal + bottotal)+1
   if lpcount == 0:
      lpcount = 1
   lcorrect = (ltot*100) / lpcount
# calculate column totals and store in array art
   ccounter = 0
   while ccounter <= (crop-1):
      ccounter +=1
      loc = (ccounter-1)* crop
      ctotal = sum(my[loc:loc+crop])
      art[ccounter]= ctotal
      if ccounter <= crop/2 :
         coffset = (ccounter - (crop/2))-1
      else:
         coffset = (ccounter - (crop/2))
      art1[ccounter] = ctotal*coffset
# calculate column value from array art
   ccounter = 0
   ctot = 0
   leftotal = 0
   rigtotal = 0
   while ccounter <= crop-1:
      ccounter +=1
      ima = art[ccounter]
      imc = art1[ccounter]
      ctot = ctot + imc
      if ccounter <= (crop/2):
         leftotal = leftotal + ima
      else:
         rigtotal = rigtotal + ima
   cpcount = (leftotal + rigtotal)+1
   ccorrect = ((ctot*100) / cpcount)
   if pcont == 0:
      lcorrect = 1
      ccorrect = 1
   acorrect = lcorrect
   bcorrect = ccorrect
   if auto_win == 1:
      if lpcount > 1 and ars[3]< 2 and ars[crop-2] < 2 and art[3] < 2 and art[crop-2] < 2:
         crop = crop - 1
         if crop < 10:
            crop = 10
      if lpcount > 1 and (ars[2] > 1 or ars[crop-2] > 1 or art[2] > 1 or art[crop-2] > 1):
         crop = crop + 1
         if crop > 128 :
            crop = 128
         if (width/2 + crop/2 + offset3 > width) or ((width/2) + offset3 - (crop /2) ) <=1 or ((height/2) + offset4 - (crop /2) ) >= height or ((height/2) - offset4 - (crop /2) ) <=1:
            crop = crop -2
      if lpcount == 1:
         crop =32
   return acorrect,bcorrect,cpcount,maxtot,mxo,crop,Sens,offset5,offset6

def commands (nscale,escale,sscale,wscale,ewi,nsi,acorrect,bcorrect,mincor):
   dirn = 'n'
   nsscale = nscale
   lcorrect = (acorrect * nsscale)/100
   if nsi != 0:
      dirn = 's'
      nsscale = sscale
      lcorrect = (acorrect * nsscale)/100
   if lcorrect <=0:
      dirn = 's'
      nsscale = sscale
      lcorrect = (acorrect * nsscale)/100
      if nsi != 0:
         dirn = 'n'
         nsscale = nscale
         lcorrect = (acorrect * nsscale)/100
      lcorrect = 0-lcorrect
   if lcorrect > 9999:
      lcorrect = 9999
   if lcorrect < mincor :
      lcorrect = 0
   Vcorrect = lcorrect
   Vcorlen = len(str(Vcorrect))
   ime = 1
   Vcorr =""
   while ime <= (4-Vcorlen):
      Vcorr = Vcorr + '0'
      ime +=1
   Vcorrt =':Mg'+dirn+Vcorr+str(Vcorrect)

   dirn = 'w'
   ewscale = wscale
   ccorrect = (bcorrect * ewscale)/100
   if ewi != 0:
      dirn = 'e'
      ewscale = escale
      ccorrect = (bcorrect * ewscale)/100
   if ccorrect <=0:
      dirn = 'e'
      ewscale = escale
      ccorrect = (bcorrect * ewscale)/100
      if ewi != 0:
         dirn = 'w'
         ewscale = wscale
         ccorrect = (bcorrect * ewscale)/100
      ccorrect = 0-ccorrect
   if ccorrect > 9999:
      ccorrect = 9999
   if ccorrect < mincor :
      ccorrect = 0
   Hcorrect = ccorrect
   Hcorlen = len(str(Hcorrect))
   ime = 1
   Hcorr=""
   while ime <= (4-Hcorlen):
      Hcorr = Hcorr + '0'
      ime +=1
   Hcorrt =':Mg'+dirn+Hcorr+str(Hcorrect)
   return Vcorrt,Hcorrt,ewi,nsi

def lx200 (Vcorrt,Hcorrt):
   if serial_connected ==1:
      ser.write(bytes(Vcorrt.encode('ascii')))
      t1 = time.time()
      while time.time() < t1 +0.5:
         t2 = time.time()
      ser.write(bytes(Hcorrt.encode('ascii')))
   return

oldnscale = nscale
oldescale = escale
oldsscale = sscale
oldwscale = wscale
oldcrop  = crop 
oldauto_g = auto_g
oldtrack = track
olddelay = Interval
oldlog = log
oldframes = frames
oldSens = Sens
oldgraph = graph
oldthres = thres
oldnr = nr
oldplot = plot
oldauto_win = auto_win
oldauto_t = auto_t
oldcrop_img = crop_img
oldrpibr = rpibr
oldrpico = rpico
oldrpiss = rpiss
oldrpiex = rpiex
oldrpiISO = rpiISO
oldrpiev = rpiev

arv = {}
arh = {}
arp = {}
count = 0
crop  = crop 
oldnsi = nsi
oldewi = ewi
posx = (width/2)
posy = (height/2)
posxi = -1
posxj = 1
posyi = -1
posyj = 1
poss = 3
cycle = 0
wd = 20
hd = 20
pct = 1
pcu = 1


wz = 1
blankline = chr(3)+ chr(3)+ chr(3)
while wz < width:
   blankline = blankline + chr(3)+ chr(3)+ chr(3)
   wz +=1
wz = 1
redline = chr(128)+ chr(0)+ chr(0)
while wz < 50:
   redline = redline + chr(128)+ chr(0)+ chr(0)
   wz +=1
wz=1
bluline = chr(0)+ chr(0)+ chr(128)
while wz < 50:
   bluline = bluline + chr(0)+ chr(0)+ chr(128)
   wz +=1
wz=1
greline = chr(0)+ chr(64)+ chr(0)
while wz < 50:
   greline = greline + chr(0)+ chr(64)+ chr(0)
   wz +=1
wz=1
gryline = chr(128)+ chr(128)+ chr(128)
while wz < 50:
   gryline = gryline + chr(128)+ chr(128)+ chr(128)
   wz +=1
if serial_connected ==1:
   ser = serial.Serial('/dev/ttyACM0',9600)
start = time.time()
xycle = 0
while cycle == 0:
   xycle = 100
   if camera_connected == 0:
      posxa =  random.randrange(posxi,posxj)
      posya =  random.randrange(posyi,posyj)
      posx = posx + posxa
      if posx > (width-50):
          posxi = -2
          posxj = 0
      if posx < 50:
          posxi = 0
          posxj = 2
      posy = posy + posya
      if posy > (height-50):
          posyi = -2
          posyj = 0
      if posy < 50:
          posyj = 2
          posyi = 0
      if (time.time() - start) >= Interval - 0.2 and serial_connected == 0:
         if auto_g == 1 and ((bcorrect/100) * escale) > mincor:
            posx = posx - (bcorrect/100)
            start = time.time()
         if auto_g == 1 and ((acorrect/100) * nscale) > mincor:   
            posy = posy - (acorrect/100)
            start = time.time()
         if auto_g == 1 and 0-((bcorrect/100) * escale) > mincor:
            posx = posx - (bcorrect/100)
            start = time.time()
         if auto_g == 1 and 0-((acorrect/100) * nscale) > mincor:   
            posy = posy - (acorrect/100)
            start = time.time()
      imu = demo(width,height,posx,posy,blankline,wd,hd)
      
   acorrect,bcorrect,cpcount,maxtot,mxo,crop,Sens,offset5,offset6 = picture (width,height,crop ,offset3,offset4,offset5,offset6,frames,Sens,camera_connected,redline,greline,bluline,gryline,blankline,imu,mxo,use_fswebcam,auto_t,arp,crop_img,w,h,rpico,rpibr,rpit,rpiex,rpiISO,rpiss,vtime,htime)
   Vcorrt,Hcorrt,ewi,nsi = commands (nscale,escale,sscale,wscale,ewi,nsi,acorrect,bcorrect,mincor)
   if track == 1:
      acorrecto = acorrect
      bcorrecto = bcorrect
      offset3o = offset3
      offset4o = offset4
      offset3 = offset3 + (bcorrect/100)
      offset4 = offset4 + ((0-acorrect)/100)
      acorrect = 0
      bcorrect = 0
      if ((width/2) + offset3 + (crop /2) ) >= width or ((width/2) + offset3 - (crop /2) ) <=1:
         offset3 = offset3o
         offset4 = offset4o
         acorrect = acorrecto
         bcorrect = bcorrecto
      if ((height/2) + offset4 - (crop /2) ) >= height or ((height/2) - offset4 - (crop /2) ) <=1:
         offset3 = offset3o
         offset4 = offset4o
         acorrect = acorrecto
         bcorrect = bcorrecto
   if (time.time() - start) >= Interval -.5 :
      if auto_i == 1 and Intervals < 10:
         if rpiex != "off":
            Interval = Intervals + int(rpit/1000)
         if rpiex == "off":
            Interval = Intervals
         acor = int(Vcorrt[4:8])
         bcor = int(Hcorrt[4:8])
         if acor >= bcor and acor > 0:
            if acor >= 1000:
               Interval = Intervals + (acor/1000)+1
         if acor <= bcor and acor < 0:
            if acor <= -1000:
               Interval = Intervals + 0-(acor/1000)+1
         if bcor > acor and bcor > 0:
            if bcor >= 1000:
               Interval = Intervals + (bcor/1000)+1
         if bcor < acor and bcor < 0:
            if bcor <= -1000:
               Interval = Intervals + 0-(bcor/1000)+1
         # print acor,bcor,Interval, Intervals
      if auto_g == 1 :
         vdir = Vcorrt[3:4]
         hdir = Hcorrt[3:4]
         vcor = int(Vcorrt[4:8])
         hcor = int(Hcorrt[4:8])
         time1 = time.time()
         vtime = ((time1 * 1000) + vcor)/1000
         htime = ((time1 * 1000) + hcor)/1000
         # print time1,vtime,htime
         start = time.time()
         if vdir == "n" and vcor > 0:
            keys ("N",18,greenColor,427,height+38,1)
            GPIO.output(N_OP,GPIO.HIGH)
            keys ("S",18,whiteColor,427,height+102,1)
            GPIO.output(S_OP,GPIO.LOW)
         if hdir == "e" and hcor > 0:
            keys ("E",18,greenColor,460,height+70,1)
            GPIO.output(E_OP,GPIO.HIGH)
            keys ("W",18,whiteColor,393,height+70,1)
            GPIO.output(W_OP,GPIO.LOW)
         if vdir == "s" and vcor > 0:
            keys ("S",18,greenColor,427,height+102,1)
            GPIO.output(S_OP,GPIO.HIGH)
            keys ("N",18,whiteColor,427,height+38,1)
            GPIO.output(N_OP,GPIO.LOW)
         if hdir == "w" and hcor > 0:
            keys ("W",18,greenColor,393,height+70,1)
            GPIO.output(W_OP,GPIO.HIGH)
            keys ("E",18,whiteColor,460,height+70,1)
            GPIO.output(E_OP,GPIO.LOW)
         # print vdir,hdir,vcor,hcor,vtime,htime
         if serial_connected ==1:
            ser.write(bytes(Vcorrt.encode('ascii')))
            time.sleep(0.2)
            ser.write(bytes(Hcorrt.encode('ascii')))
            time.sleep(0.2)
            #start = time.time()
         if log == 1:
            now = datetime.datetime.now()
            month = now.month
            if month < 10:
               month = "0" + str(month)
            day = now.day
            if day < 10:
               day = "0" + str(day)
            hour = now.hour
            if hour < 10:
               hour = "0" + str(hour)
            minute = now.minute
            if minute < 10:
               minute = "0" + str(minute)
            second = now.second
            if second < 10:
               second = "0" + str(second)
            tim = str(now.year)+"/"+str(month)+"/"+str(day)+","+str(hour)+":"+str(minute)+":"+str(second)
            timp = tim + "," + Vcorrt + "," + Hcorrt + "," + str(acorrect) + "," + str(bcorrect) + "\n"
            #filedata
            file = open(logfile, "a")
            file.write(timp)
            file.close()

# Display
   if plot == 1:
      pox = 533
      poy = 10
      pov = 50
      pol = 256
      pygame.draw.line(windowSurfaceObj, greyColor, (pox-1,poy-1),(pox+pov+1,poy-1))
      pygame.draw.line(windowSurfaceObj, greyColor, (pox+pov+1,poy-1),(pox+pov+1,poy+pol+1))
      pygame.draw.line(windowSurfaceObj, greyColor, (pox+pov+1,poy+pol+1),(pox-1,poy+pol+1))
      pygame.draw.line(windowSurfaceObj, greyColor, (pox-1,poy+pol+1),(pox-1,poy-1))
      limg +=1
      val2 = pov/2
      val3 = pov/2
      if acorrect > 0:
         val2 = (pov/2) + int(math.sqrt(acorrect))/4
      if bcorrect > 0:
         val3 = (pov/2) + int(math.sqrt(bcorrect))/4
      if acorrect < 0:
         val2 = (pov/2) - int(math.sqrt(0-acorrect))/4
      if bcorrect < 0:
         val3 = (pov/2) - int(math.sqrt(0-bcorrect))/4
      if val2 < val3:
         rimg = blankline[0:(val2)*3]
         rimg = rimg + chr(255)+ chr(0)+ chr(0)
         rimg = rimg + blankline[(val2)*3:(val3)*3]
         rimg = rimg + chr(0)+ chr(255)+ chr(0)
         rimg = rimg + blankline
         pimg = pimg + rimg[0:pov*3]
      else:
         rimg = blankline[0:(val3)*3]
         rimg = rimg + chr(0)+ chr(255)+ chr(0)
         rimg = rimg + blankline[(val3)*3:(val2)*3]
         rimg = rimg + chr(255)+ chr(0)+ chr(0)
         rimg = rimg + blankline
         pimg = pimg + rimg[0:pov*3]
      if limg > pol:
         yt = (limg-pol)*pov*3
         yu = limg*pov*3
         pimg = pimg[yt:yu]
         limg = pol
      imageg = pygame.image.fromstring(pimg,(pov,limg),"RGB",1) 
      catSurfaceObj = imageg
      windowSurfaceObj.blit(catSurfaceObj,(pox,poy))
      
   if oldauto_win != auto_win:
      if auto_win == 0:
         button (1,65,63,31,height,greyColor)
         keys ("A-Win",16,dgryColor,11,height+71,0)
      else:
         button (1,65,63,31,height,dgryColor)
         keys ("A-Win",16,greenColor,11,height+71,0)
   if oldnr != nr:
      msg = "NR"
      if nr == 0:
         button (65,97,63,31,height,greyColor)
         keys ("NR",14,dgryColor,82,height+106,0)
      else:
         button (65,97,63,31,height,dgryColor)
         keys ("NR",14,greenColor,82,height+106,0)
   if oldnsi != nsi:
      msg = "NSi"
      if nsi == 0:
         button (65,161,31,31,height,greyColor)
         keys ("NSi",14,dgryColor,68,height+169,0)
      else:
         button (65,161,31,31,height,dgryColor)
         keys ("NSi",14,greenColor,68,height+169,0)
   if oldewi != ewi:   
      msg = "EWi"
      if ewi == 0:
         button (97,161,31,31,height,greyColor)
         keys ("EWi",14,dgryColor,100,height+169,0)
      else:
         button (97,161,31,31,height,dgryColor)
         keys ("EWi",14,greenColor,100,height+169,0)
   if oldauto_t != auto_t:
      if auto_t == 0:
         button (65,65,63,31,height,greyColor)
         keys ("A-Thr",16,dgryColor,76,height+71,0)
      else:
         button (65,65,63,31,height,dgryColor)
         keys ("A-Thr",16,greenColor,76,height+71,0)
   if camera_connected == 0:
      keys ("Simulation",16,whiteColor,140,0,0)
   if auto_g == 0:
      keys (Vcorrt,16,purpleColor,0,0,0)
      keys (Hcorrt,16,purpleColor,276,0,0)
   else:
      keys (Vcorrt,16,greenColor,0,0,0)
      keys (Hcorrt,16,greenColor,276,0,0)
   if track == 1:
      keys (Vcorrt,16,blueColor,0,0,0)
      keys (Hcorrt,16,blueColor,276,0,0)
   if oldauto_g != auto_g:
      if auto_g == 0:
         button (1,33,127,31,height,greyColor)
         keys ("AutoGuide",16,dgryColor,22,height+39,0)
      else:
         button (1,33,127,31,height,dgryColor)
         keys ("AutoGuide",16,greenColor,22,height+39,0)
   if oldlog != log :
      if log == 0:
         button (1,97,63,31,height,greyColor)
         keys ("Log",16,dgryColor,15,height+103,0)
      else:
         button (1,97,63,31,height,dgryColor)
         keys ("Log",16,greenColor,15,height+103,0)
      
   if oldgraph != graph :
      if graph == 0:
         button (1,129,63,31,height,greyColor)
         keys ("Graph",16,dgryColor,11,height+135,0)
      else:
         button (1,129,63,31,height,dgryColor)
         keys ("Graph",16,greenColor,11,height+135,0)
   if oldplot != plot :
      if plot == 0:
         button (65,129,63,31,height,greyColor)
         keys ("Plot",16,dgryColor,81,height+135,0)
      else:
         button (65,129,63,31,height,dgryColor)
         keys ("Plot",16,greenColor,81,height+135,0)      
   if oldthres != thres :
      if thres == 0:
         button (1,161,63,31,height,greyColor)
         keys ("Thres",16,dgryColor,11,height+167,0)
      else:
         button (1,161,63,31,height,dgryColor)
         keys ("Thres",16,greenColor,11,height+167,0)

   if oldnscale != nscale:
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(321,height+33, 31, 31))
      keys (str(nscale),16,redColor,323,height+36,0)
   if oldsscale != sscale:
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(321,height+65, 31, 31))
      keys (str(sscale),16,redColor,323,height+68,0)
   if oldescale != escale:
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(321,height+97, 31, 31))
      keys (str(escale),16,redColor,323,height+100,0)
   if oldwscale != wscale:
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(321,height+129, 31, 31))
      keys (str(wscale),16,redColor,323,height+132,0)
   if oldSens != Sens:
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(225,height+97, 31, 31))
      keys (str(Sens),16,redColor,230,height+100,0)
   if olddelay != Interval:
      msg = str(Interval)
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(225,height+129, 31, 31))
      keys (str(Interval),16,redColor,232,height+132,0)
   if oldcrop_img != crop_img:
      msg = str(crop_img)
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(225,height+161, 31, 31))
      keys (str(crop_img),16,redColor,232,height+164,0)
   if oldframes != frames:
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(225,height+33, 31, 31))
      msg = rgb[frames]
      if frames == 1:
         keys (msg,16,redColor,230,height+34,0)
      if frames == 2:
         keys (msg,16,greenColor,230,height+34,0)
      if frames == 3:
         keys (msg,16,blueColor,230,height+34,0)
      if frames == 4:
         keys (msg,16,whiteColor,230,height+34,0)
   if oldcrop  != crop :
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(225,height+65, 31, 31))
      keys (str(crop),16,redColor,228,height+68,0)

   if oldrpibr != rpibr :
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(455,10, 31, 31))
      keys (str(rpibr),14,redColor,455,10,0)
   if oldrpico != rpico:
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(455,42, 31, 31))
      keys (str(rpico),14,redColor,455,42,0)
   if oldrpiss != rpiss:
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(455,74, 31, 31))
      keys (str(rpiss/1000),14,redColor,455,74,0)
   if oldrpiex != rpiex:
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(455,106, 64, 31))
      keys (rpiex,14,redColor,455,106,0)
      if rpiex != "off":
         pygame.draw.rect(windowSurfaceObj,blackColor,Rect(455,74, 31, 31))
         keys ('off',14,redColor,455,74,0)
      else:
         pygame.draw.rect(windowSurfaceObj,blackColor,Rect(455,74, 31, 31))
         keys (str(rpiss/1000),14,redColor,455,74,0)
   if oldrpiISO != rpiISO:
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(455,138, 31, 31))
      keys (str(rpiISO),14,redColor,455,138,0)
      if rpiISO == 0:
         pygame.draw.rect(windowSurfaceObj,blackColor,Rect(455,138, 31, 31))
         keys ('off',14,redColor,455,138,0)
   if oldrpiev != rpiev:
      pygame.draw.rect(windowSurfaceObj,blackColor,Rect(455,170, 31, 31))
      keys (str(rpiev),14,redColor,455,170,0)
      if rpiev == 0:
         pygame.draw.rect(windowSurfaceObj,blackColor,Rect(455,170, 31, 31))
         keys ('off',14,redColor,455,170,0)

   w2 = width/2 + offset3
   h2 = height/2 + offset4
   c1 = crop /2
   c2 = crop /2
   pygame.draw.line(windowSurfaceObj, redColor, (w2-c1,h2-c2),(w2+c1,h2-c2))
   pygame.draw.line(windowSurfaceObj, redColor, (w2+c1,h2-c2),(w2+c1,h2+c2))
   pygame.draw.line(windowSurfaceObj, redColor, (w2+c1,h2+c2),(w2-c1,h2+c2))
   pygame.draw.line(windowSurfaceObj, redColor, (w2-c1,h2+c2),(w2-c1,h2-c2))
   pygame.draw.line(windowSurfaceObj, redColor, (w2-4,h2),(w2+4,h2))
   pygame.draw.line(windowSurfaceObj, redColor, (w2,h2-4),(w2,h2+4))

   if auto_g == 0:
      pygame.draw.line(windowSurfaceObj, purpleColor, ((w2+(bcorrect/100)-5),(h2-(acorrect/100)-5)),((w2+(bcorrect/100)+5),(h2-(acorrect/100)+5)))
      pygame.draw.line(windowSurfaceObj, purpleColor, ((w2+(bcorrect/100)+5),(h2-(acorrect/100)-5)),((w2+(bcorrect/100)-5),(h2-(acorrect/100)+5)))
   else:
      pygame.draw.line(windowSurfaceObj, greenColor, ((w2 +(bcorrect/100)-5),(h2-(acorrect/100)-5)),((w2+(bcorrect/100)+5),(h2-(acorrect/100)+5)))
      pygame.draw.line(windowSurfaceObj, greenColor, ((w2 +(bcorrect/100)+5),(h2-(acorrect/100)-5)),((w2+(bcorrect/100)-5),(h2-(acorrect/100)+5)))
   if track == 1:
      pygame.draw.line(windowSurfaceObj, blueColor, ((w2 +(bcorrect/100)-5),(h2-(acorrect/100)-5)),((w2+(bcorrect/100)+5),(h2-(acorrect/100)+5)))
      pygame.draw.line(windowSurfaceObj, blueColor, ((w2 +(bcorrect/100)+5),(h2-(acorrect/100)-5)),((w2+(bcorrect/100)-5),(h2-(acorrect/100)+5)))

   pygame.display.update()
   oldnscale = nscale
   oldescale = escale
   oldsscale = sscale
   oldwscale = wscale
   oldcrop  = crop 
   oldauto_g = auto_g
   oldtrack = track
   olddelay = Interval
   oldlog = log
   oldframes = frames
   oldSens = Sens
   oldgraph = graph
   oldnsi = nsi
   oldewi = ewi
   oldthres = thres
   oldnr = nr
   oldplot = plot
   oldauto_win = auto_win
   oldauto_t = auto_t
   oldcrop_img = crop_img
   oldrpibr = rpibr
   oldrpico = rpico
   oldrpiss = rpiss
   oldrpiex = rpiex
   oldrpiISO = rpiISO
   oldrpiev = rpiev

# read mouse

   for event in pygame.event.get():
       if event.type == QUIT:
          pygame.quit()
          sys.exit()
       elif event.type == MOUSEBUTTONUP:
          mousex,mousey = event.pos
          z = 0
          x = mousex/32
          if mousex > 385 and mousex < 449 and mousey > 0 and mousey < height:
             y = mousey/32
             z = (20*x)+y
          if mousey > height:
             y = (mousey-height)/32
             z = (10*x)+y
          # print mousex,mousey,x,y,z
          if mousex < width and mousey < height :
             offset3o = offset3
             offset4o = offset4
             offset3 = 0-((width/2)- mousex)
             offset4 = 0-((height/2) - mousey)
             if ((width/2) + offset3 + (crop /2) ) >= width or ((width/2) + offset3 - (crop /2) ) <=1:
                offset3 = offset3o 
                offset4 = offset4o 
             if ((height/2) + offset4 + (crop /2) ) >= height or ((height/2) + offset4 - (crop /2) ) <=1:
                offset3 = offset3o 
                offset4 = offset4o
          if mousex > 539 and mousey > (256 - maxtot) and mousey < 266 and graph == 1:
             level = 256 - mousey
             Sens = maxtot - level - 10
          if z == 195:
             pygame.image.save(windowSurfaceObj,'screen' + str(pct)+'.jpg')
             pct +=1
          if z == 194:
             rpistr = "raspistill -o capture" + str(pcu) + ".jpg -co " + str(rpico) + " -br " + str(rpibr)
             if rpiex != 'off':
                rpistr = rpistr + " -t 800 -ex " + rpiex
             else:
                rpistr = rpistr + " -t 10 -ss " + str(rpiss)
             if rpiISO > 0:
                rpistr = rpistr + " -ISO " + str(rpiISO)
             if rpiev != 0:
                rpistr = rpistr + " -ev " + str(rpiev)
             rpistr = rpistr + " -n -sa " + str(rpisa)
             path = rpistr + ' -w 2592 -h 1944'
             os.system (path)
             pcu +=1
          if z == 171:
             offset3 = offset3 + 0
             offset4 = offset4 - 1
             if ((height/2) + offset4 + (crop /2) ) >= height:
                offset3 = offset3 - 0
                offset4 = offset4 + 1
             if ((height/2) + offset4 - (crop /2) ) <=1:
                offset3 = offset3 - 0
                offset4 = offset4 + 1            
          if z == 173:
             offset3 = offset3 + 0
             offset4 = offset4 + 1
             if ((height/2) + offset4 + (crop /2) ) >= height:
                offset3 = offset3 - 0
                offset4 = offset4 - 1
             if ((height/2) + offset4 - (crop /2) ) <=1:
                offset3 = offset3 - 0
                offset4 = offset4 - 1 
          if z == 182:
             offset3 = offset3 + 1
             offset4 = offset4 + 0
             if ((width/2) + offset3 + (crop /2) ) >= width:
                offset3 = offset3 - 1
                offset4 = offset4 - 0
             if ((width/2) + offset3 - (crop /2) ) <=1:
                offset3 = offset3 - 1
                offset4 = offset4 - 0 
          if z == 162:
             offset3 = offset3 - 1
             offset4 = offset4 + 0
             if ((width/2) + offset3 + (crop /2) ) >= width:
                offset3 = offset3 + 1
                offset4 = offset4 - 0
             if ((width/2) + offset3 - (crop /2) ) <=1:
                offset3 = offset3 + 1
                offset4 = offset4 - 0 
          if z == 64:
             Interval = Intervals
             Interval = Interval +1
             Intervals = Interval
          if z == 54:
             Interval = Intervals
             Interval = Interval - 1
             Intervals = Interval
             if Interval < 1:
                Interval = 1
                Intervals = Interval
                
          if z == 260:
             rpibr = rpibr + 5
             if rpibr >= 100:
                rpibr = 100
          if z == 240:
             rpibr = rpibr - 5
             if rpibr <= 0:
                rpibr = 0
          if z == 241:
             rpico = rpico - 5
             if rpico <= -100:
                rpico = -100
          if z == 261:
             rpico = rpico + 5
             if rpico >= 100:
                rpico = 100
          if z == 242:
             rpiss = rpiss - 10000
             if rpiss <= 10000:
                rpiss = 10000
          if z == 262:
             rpiss = rpiss + 10000
             if rpiss >= 340000:
                rpiss = 340000
          if z == 244:
             if rpiISO > 0:
                rpiISO = rpiISO - 100
                rpiev = 0
             if rpiISO <= 0:
                rpiISO = 0
          if z == 264:
             rpiISO = rpiISO + 100
             rpiev = 0
             if rpiISO >= 800:
                rpiISO = 800
          if z == 245:
             rpiev = rpiev - 1
             rpiISO = 0
             if rpiev <= -20:
                rpiISO = -20
          if z == 265:
             rpiev = rpiev + 1
             rpiISO = 0
             if rpiev >= 20:
                rpiev = 20

          if z == 54:
             Interval = Intervals
             Interval = Interval - 1
             Intervals = Interval
             if Interval < 1:
                Interval = 1
                Intervals = Interval
          if z == 172:
             offset3 = 0
             offset4 = 0
          if z == 990:
             auto_win = 0
             keys (" Please Wait....",16,redColor,0,height+1,1)
             track = 0
             crop  = 224
             offset3 = 0
             offset4 = 0
             acorrect,bcorrect,cpcount,maxtot,mxo,crop,Sens,offset5,offset6 = picture (width,height,crop ,offset3,offset4,offset5,offset6,frames,Sens,camera_connected,redline,greline,bluline,gryline,blankline,imu,mxo,use_fswebcam,auto_t,arp,crop_img,w,h,rpico,rpibr,rpit,rpiex,rpiISO,rpiss,vtime,htime)
             crop  = 64
             offset3 = offset3 + (bcorrect/100)
             offset4 = offset4 + ((0-acorrect)/100)
             if ((width/2) + offset3 + (crop /2) ) >= width:
                offset3 = offset3 - (bcorrect/100)
                offset4 = offset4 - ((0-acorrect)/100)
             if ((width/2) + offset3 - (crop /2) ) <=1:
                offset3 = offset3 - (bcorrect/100)
                offset4 = offset4 - ((0-acorrect)/100) 
             if ((height/2) + offset4 + (crop /2) ) >= height:
                offset3 = offset3 - (bcorrect/100)
                offset4 = offset4 - ((0-acorrect)/100)
             if ((height/2) + offset4 - (crop /2) ) <=1:
                offset3 = offset3 - (bcorrect/100)
                offset4 = offset4 - ((0-acorrect)/100)
             crop  = 32
             crop  = crop 
             acorrect,bcorrect,cpcount,maxtot,mxo,crop,Sens,offset5,offset6 = picture (width,height,crop ,offset3,offset4,offset5,offset6,frames,Sens,camera_connected,redline,greline,bluline,gryline,blankline,imu,mxo,use_fswebcam,auto_t,arp,crop_img,w,h,rpico,rpibr,rpit,rpiex,rpiISO,rpiss,vtime,htime)
             count1 = cpcount
             crop  = 64
             crop  = crop 
             acorrect,bcorrect,cpcount,maxtot,mxo,crop,Sens,offset5,offset6 = picture (width,height,crop ,offset3,offset4,offset5,offset6,frames,Sens,camera_connected,redline,greline,bluline,gryline,blankline,imu,mxo,use_fswebcam,auto_t,arp,crop_img,w,h,rpico,rpibr,rpit,rpiex,rpiISO,rpiss,vtime,htime)
             count2 = cpcount
             crop  = 96
             crop  = crop 
             acorrect,bcorrect,cpcount,maxtot,mxo,crop,Sens,offset5,offset6 = picture (width,height,crop ,offset3,offset4,offset5,offset6,frames,Sens,camera_connected,redline,greline,bluline,gryline,blankline,imu,mxo,use_fswebcam,auto_t,arp,crop_img,w,h,rpico,rpibr,rpit,rpiex,rpiISO,rpiss,vtime,htime)
             count3 = cpcount
             crop  = 128
             crop  = crop 
             acorrect,bcorrect,cpcount,maxtot,mxo,crop,Sens,offset5,offset6 = picture (width,height,crop ,offset3,offset4,offset5,offset6,frames,Sens,camera_connected,redline,greline,bluline,gryline,blankline,imu,mxo,use_fswebcam,auto_t,arp,crop_img,w,h,rpico,rpibr,rpit,rpiex,rpiISO,rpiss,vtime,htime)
             count4 = cpcount
             crop  = 32
             crop  = 32
             if count2 > count1:
                crop  = 64
                crop  = 64 
             if count3 > count2:
                crop  = 96
                crop  = 96
             if count4 > count3:
                crop  = 128
                crop  = 128
             if ((width/2) + offset3 + (crop /2) ) >= width:
                crop  = crop  - 32
             if ((width/2) + offset3 - (crop /2) ) <=1:
                crop  = crop  - 32
             if ((height/2) + offset4 + (crop /2) ) >= height:
                crop  = crop  - 32
             if ((height/2) + offset4 - (crop /2) ) <=1:
                crop  = crop  - 32
             keys (" Please Wait....",16,blackColor,0,height+1,1)
                
          if z == 62:
             auto_win =  0
             crop  = crop  + 32
             if crop  > 128:
                crop  = 32
             if ((width/2) + offset3 + (crop /2) ) >= width:
                crop  = crop  - 32
             if ((width/2) + offset3 - (crop /2) ) <=1:
                crop  = crop  - 32
             if ((height/2) + offset4 + (crop /2) ) >= height:
                crop  = crop  - 32
             if ((height/2) + offset4 - (crop /2) ) <=1:
                crop  = crop  - 32
              
          if z == 52:
             auto_win = 0
             crop  = crop  - 32
             if crop  < 32:
                crop  = 32

          if z == 190:
             keys ("N",18,whiteColor,427,height+38,1)
             GPIO.output(N_OP,GPIO.LOW)
             keys ("S",18,whiteColor,427,height+102,1)
             GPIO.output(S_OP,GPIO.LOW)
             keys ("W",18,whiteColor,393,height+70,1)
             GPIO.output(E_OP,GPIO.LOW)
             keys ("E",18,whiteColor,460,height+70,1)
             GPIO.output(W_OP,GPIO.LOW)
             sys.exit()
              
          if z == 91:
             nscale = nscale + 10
             if nscale > 800:
                nscale = 800
          if z == 81:
             nscale = nscale - 10
             if nscale < 10:
                nscale = 10
          if z == 93:
             escale = escale + 10
             if escale > 800:
                escale = 800
          if z == 83:
             escale = escale - 10
             if escale < 10:
                escale = 10
          if z == 92:
             sscale = sscale + 10
             if sscale > 800:
                sscale = 800
          if z == 82:
             sscale = sscale - 10
             if sscale < 10:
                sscale = 10
          if z == 94:
             wscale = wscale + 10
             if wscale > 800:
                wscale = 800
          if z == 84:
             wscale = wscale - 10
             if wscale < 10:
                wscale = 10
          if z == 95:
             nscale = nscale + 10
             if nscale > 800:
                nscale = 800
             wscale = wscale + 10
             if wscale > 800:
                wscale = 800
             sscale = sscale + 10
             if sscale > 800:
                sscale = 800
             escale = escale + 10
             if escale > 800:
                escale = 800
          if z == 85:
             wscale = wscale - 10
             if wscale < 10:
                wscale = 10
             escale = escale - 10
             if escale < 10:
                escale = 10
             sscale = sscale - 10
             if sscale < 10:
                sscale = 10
             nscale = nscale - 10
             if nscale < 10:
                nscale = 10
          if z == 61:
             frames = frames +1
             if frames > 4:
                frames = 1
          if z == 51:
             frames = frames -1
             if frames < 1:
                frames = 4
          if z == 53:
             Sens = Sens -1
             auto_t = 0
             if Sens < 1:
                Sens = 1
          if z == 63:
             Sens = Sens +1
             auto_t = 0
             if Sens > 100:
                Sens = 100
 
          if auto_g == 0 or auto_g == 1:
             if z == 133:
                if serial_connected == 1:
                   keys ("S",18,greenColor,427,height + 102,1)
                   lx200 (':Mgs1000',':Mgw0000')
                   keys ("S",18,whiteColor,427,height + 102,1)
                else:
                   keys ("S",18,greenColor,427,height + 102,1)
                   GPIO.output(S_OP,GPIO.HIGH)
                   keys ("N",18,whiteColor,427,height+38,1)
                   GPIO.output(N_OP,GPIO.LOW)
                   time.sleep(1)
                   keys ("S",18,whiteColor,427,height + 102,1)
                   GPIO.output(S_OP,GPIO.LOW)
                   
             if z == 131:
                if serial_connected == 1:
                   keys ("N",18,greenColor,427,height + 38,1)
                   lx200 (':Mgn1000',':Mgw0000')
                   keys ("N",18,whiteColor,427,height + 38,1)
                else:
                   keys ("N",18,greenColor,427,height + 38,1)
                   GPIO.output(N_OP,GPIO.HIGH)
                   keys ("S",18,whiteColor,427,height + 102,1)
                   GPIO.output(S_OP,GPIO.LOW)
                   time.sleep(1)
                   keys ("N",18,whiteColor,427,height+38,1)
                   GPIO.output(N_OP,GPIO.LOW)
                   
             if z == 122:
                if serial_connected == 1:
                   keys ("W",18,greenColor,393,height + 70,1)
                   lx200 (':Mgw1000',':Mgs0000')
                   keys ("W",18,whiteColor,393,height + 70,1)
                else:
                   keys ("W",18,greenColor,393,height + 70,1)
                   GPIO.output(W_OP,GPIO.HIGH)
                   keys ("E",18,whiteColor,460,height+70,1)
                   GPIO.output(E_OP,GPIO.LOW)
                   time.sleep(1)
                   keys ("W",18,whiteColor,393,height+70,1)
                   GPIO.output(W_OP,GPIO.LOW)
                   
             if z == 142:
                if serial_connected == 1:
                   keys ("E",18,greenColor,460,height + 70,1)
                   lx200 (':Mge1000',':Mgs0000')
                   keys ("E",18,whiteColor,460,height + 70,1)
                else:
                   keys ("E",18,greenColor,460,height + 70,1)
                   GPIO.output(E_OP,GPIO.HIGH)
                   keys ("W",18,whiteColor,393,height+70,1)
                   GPIO.output(W_OP,GPIO.LOW)
                   time.sleep(1)
                   keys ("E",18,whiteColor,460,height+70,1)
                   GPIO.output(E_OP,GPIO.LOW)
                   
             if z == 132:
                auto_g = 0
                if serial_connected == 1:
                   lx200 (':Q#',':Q#')
                keys ("N",18,whiteColor,427,height+38,1)
                GPIO.output(N_OP,GPIO.LOW)
                keys ("S",18,whiteColor,427,height+102,1)
                GPIO.output(S_OP,GPIO.LOW)
                keys ("W",18,whiteColor,393,height+70,1)
                GPIO.output(E_OP,GPIO.LOW)
                keys ("E",18,whiteColor,460,height+70,1)
                GPIO.output(W_OP,GPIO.LOW)
                
             if z == 23 or z == 33:
                nr = nr +1
                if nr > 1:
                   nr = 0
             if z == 290:
                keys (" Please Wait..",16,redColor,0,height+1,0)
                button (193,161,31,31,height,dgryColor)
                keys ("  CAL",14,greenColor,186,height+168,1)
                auto_g = 0
                arzn = {}
                xcrop  = crop 
                crop  = 128
                crop  = 128
                nr = 0
                x = 0
                while x < 5:
                   x +=1
                   lx200 (':Mgn1000','Mgw0000')
                   time.sleep(2)
                   if x > 2:
                      acorrect,bcorrect,cpcount,maxtot,mxo,crop,Sens,offset5,offset6 = picture (width,height,crop ,offset3,offset4,offset5,offset6,frames,Sens,camera_connected,redline,greline,bluline,gryline,blankline,imu,mxo,use_fswebcam,auto_t,arp,crop_img,w,h,rpico,rpibr,rpit,rpiex,rpiISO,rpiss)
                      pygame.draw.line(windowSurfaceObj, purpleColor, ((w2+(bcorrect/100)-5),(h2-(acorrect/100)-5)),((w2+(bcorrect/100)+5),(h2-(acorrect/100)+5)))
                      pygame.draw.line(windowSurfaceObj, purpleColor, ((w2+(bcorrect/100)+5),(h2-(acorrect/100)-5)),((w2+(bcorrect/100)-5),(h2-(acorrect/100)+5)))
                      keys (str(acorrect) + " : "+ str(bcorrect),16,redColor,100,height+1,1)
                      time.sleep(2)
                      keys (str(acorrect) + " : "+ str(bcorrect),16,blackColor,100,height+1,1)
                      pygame.display.update()
                   arzn[(x,1)] = acorrect
                move_n = ((arzn[(5,1)] - arzn[(3,1)])/4)/100
                if move_n < 0:
                   move_n = 0 - move_n
                arzs = {}
                x = 0
                while x < 5:
                   x +=1
                   lx200 (':Mgs1000','Mgw0000')
                   time.sleep(2)
                   if x > 2:
                      acorrect,bcorrect,cpcount,maxtot,mxo,crop,Sens,offset5,offset6 = picture (width,height,crop ,offset3,offset4,offset5,offset6,frames,Sens,camera_connected,redline,greline,bluline,gryline,blankline,imu,mxo,use_fswebcam,auto_t,arp,crop_img,w,h,rpico,rpibr,rpit,rpiex,rpiISO,rpiss)
                      pygame.draw.line(windowSurfaceObj, purpleColor, ((w2+(bcorrect/100)-5),(h2-(acorrect/100)-5)),((w2+(bcorrect/100)+5),(h2-(acorrect/100)+5)))
                      pygame.draw.line(windowSurfaceObj, purpleColor, ((w2+(bcorrect/100)+5),(h2-(acorrect/100)-5)),((w2+(bcorrect/100)-5),(h2-(acorrect/100)+5)))
                      keys (str(acorrect) + " : "+ str(bcorrect),16,redColor,100,height+1,1)
                      time.sleep(2)
                      keys (str(acorrect) + " : "+ str(bcorrect),16,blackColor,100,height+1,1)
                      pygame.display.update()
                   arzs[(x,1)] = acorrect
                move_s = ((arzs[(5,1)] - arzs[(3,1)])/4)/100
                if move_s < 0:
                   move_s = 0 - move_s
                if move_n > 2:
                   nscale = 1000/move_n
                if move_s > 2:
                   sscale = 1000/move_s
                arze = {}
                x = 0
                while x < 5:
                   x +=1
                   lx200 (':Mge1000','Mgn0000')
                   time.sleep(2)
                   if x > 2:
                      acorrect,bcorrect,cpcount,maxtot,mxo,crop,Sens,offset5,offset6 = picture (width,height,crop ,offset3,offset4,offset5,offset6,frames,Sens,camera_connected,redline,greline,bluline,gryline,blankline,imu,mxo,use_fswebcam,auto_t,arp,crop_img,w,h,rpico,rpibr,rpit,rpiex,rpiISO,rpiss)
                      pygame.draw.line(windowSurfaceObj, purpleColor, ((w2+(bcorrect/100)-5),(h2-(acorrect/100)-5)),((w2+(bcorrect/100)+5),(h2-(acorrect/100)+5)))
                      pygame.draw.line(windowSurfaceObj, purpleColor, ((w2+(bcorrect/100)+5),(h2-(acorrect/100)-5)),((w2+(bcorrect/100)-5),(h2-(acorrect/100)+5)))
                      keys (str(acorrect) + " : "+ str(bcorrect),16,redColor,100,height+1,1)
                      time.sleep(1)
                      keys (str(acorrect) + " : "+ str(bcorrect),16,blackColor,100,height+1,1)
                      pygame.display.update()
                   arze[(x,1)] = bcorrect
                move_e = ((arze[(5,1)] - arze[(3,1)])/4)/100
                if move_e < 0:
                   move_e = 0 - move_e
                arzw = {}
                x = 0
                while x < 5:
                   x +=1
                   lx200 (':Mgw1000','Mgn0000')
                   time.sleep(2)
                   if x > 2:
                      acorrect,bcorrect,cpcount,maxtot,mxo,crop,Sens,offset5,offset6 = picture (width,height,crop ,offset3,offset4,offset5,offset6,frames,Sens,camera_connected,redline,greline,bluline,gryline,blankline,imu,mxo,use_fswebcam,auto_t,arp,crop_img,w,h,rpico,rpibr,rpit,rpiex,rpiISO,rpiss)
                      pygame.draw.line(windowSurfaceObj, purpleColor, ((w2+(bcorrect/100)-5),(h2-(acorrect/100)-5)),((w2+(bcorrect/100)+5),(h2-(acorrect/100)+5)))
                      pygame.draw.line(windowSurfaceObj, purpleColor, ((w2+(bcorrect/100)+5),(h2-(acorrect/100)-5)),((w2+(bcorrect/100)-5),(h2-(acorrect/100)+5)))
                      keys (str(acorrect) + " : "+ str(bcorrect),16,redColor,100,height+1,1)
                      time.sleep(1)
                      keys (str(acorrect) + " : "+ str(bcorrect),16,blackColor,100,height+1,1)
                      pygame.display.update()
                   arzw[(x,1)] = bcorrect
                move_w = ((arzw[(5,1)] - arzw[(3,1)])/4)/100
                if move_w < 0:
                   move_w = 0 - move_w
                if move_e > 2:
                   escale = 850/move_e
                if move_w > 2:
                   wscale = 850/move_w
                crop  = xcrop 
                crop  = crop
                fontObj = pygame.font.Font('freesansbold.ttf',14)
                button (193,161,31,31,height,greyColor)
                keys ("  CAL",14,dgryColor,186,height+168,1)
                keys (" Please Wait....",16,blackColor,0,height+1,1)
                
          if z == 1 or z == 11 or z == 21 or z == 31:
             auto_g = auto_g +1
             if auto_g == 1:
                track = 0
             if auto_g > 1:
                auto_g = 0
          if z == 5 or z == 15:
             thres = thres + 1
             if thres > 1:
                thres = 0
          if z == 4 or z == 14:
             graph = graph + 1
             if graph > 1:
                graph = 0
                pygame.draw.rect(windowSurfaceObj,blackColor,Rect(587,9,53,259))
          if z == 24 or z == 34:
             plot = plot + 1
             if plot > 1:
                plot = 0
                pygame.draw.rect(windowSurfaceObj,blackColor,Rect(532,9,53,259))

          if z == 2 or z == 12:
             auto_win = auto_win +1
             if auto_win > 1:
                auto_win = 0
          if z == 22 or z == 32:
             auto_t = auto_t +1
             if auto_t > 1:
                auto_t = 0
          if z == 263:
             tflag = 0
             if rpiex == 'auto':
                rpiex = 'night'
                tflag = 1
             if rpiex == 'night' and tflag == 0:
                rpiex = 'fireworks'
                tflag = 1
             if rpiex == 'fireworks' and tflag == 0:
                rpiex = 'off'
                tflag = 1
             if rpiex == 'off' and tflag == 0:
                rpiex = 'auto'
                tflag = 1
          if z == 243:
             tflag = 0
             if rpiex == 'auto':
                rpiex = 'off'
                tflag = 1
             if rpiex == 'off' and tflag == 0:
                rpiex = 'fireworks'
                tflag = 1
             if rpiex == 'fireworks' and tflag == 0:
                rpiex = 'night'
                tflag = 1
             if rpiex == 'night' and tflag == 0:
                rpiex = 'auto'
                tflag = 1
          if z == 3 or z == 13:
             log = log + 1
             if log > 1:
                log = 0
             if log == 1:
                now = datetime.datetime.now()
                month = now.month
                if month < 10:
                   month = "0" + str(month)
                day = now.day
                if day < 10:
                   day = "0" + str(day)
                hour = now.hour
                if hour < 10:
                   hour = "0" + str(hour)
                minute = now.minute
                if minute < 10:
                   minute = "0" + str(minute)
                second = now.second
                if second < 10:
                   second = "0" + str(second)   
                logfile = "/run/shm/"+str(now.year)+str(month)+str(day)+str(hour)+str(minute)+str(second)+".txt"
                keys (" Logging to " + logfile,16,redColor,0,height+1,1)
                time.sleep(2)
                keys (" Logging to " + logfile,16,blackColor,0,height+1,1)
          if z == 65 and use_fswebcam == 0 :
             crop_img = crop_img + 1
             if crop_img > max_res:
                crop_img = max_res
             if camera_connected == 1:
                if crop_img == 0:
                   w = 352
                   h = 288
                   scale = 1
                if crop_img == 1:
                   w = 640
                   h = 480
                   scale = 1.8
                if crop_img == 2:
                   w = 800
                   h = 600
                   scale = 1.25
                if crop_img == 3:
                   w = 960
                   h = 720
                   scale = 1.2
                if crop_img == 4:
                   w = 1920
                   h = 1440
                   scale = 2
                if crop_img == 5:
                   w = 2592
                   h = 1944
                   scale = 1.35
                if crop_img > 0:
                   nscale = int(nscale / scale)
                   escale = int(escale / scale)
                   sscale = int(sscale / scale)
                   wscale = int(wscale / scale)
                if use_RPiwebcam == 0:
                   cam.stop()
                   pygame.camera.init()
                   if crop_img == 0:
                      cam = pygame.camera.Camera("/dev/video0",(352,288))
                   if crop_img == 1 and max_res >= 1:
                      cam = pygame.camera.Camera("/dev/video0",(640,480))
                   if crop_img == 2 and max_res >= 2:
                      cam = pygame.camera.Camera("/dev/video0",(800,600))
                   if crop_img == 3 and max_res >= 3:
                      cam = pygame.camera.Camera("/dev/video0",(960,720))
                   cam.start()
                if crop_img == 0:
                   offset3 = offset3/2
                   offset4 = offset4/2
             if camera_connected == 0:
                wd = 20 + (crop_img * 4)
                hd = wd
                
          if z == 55 and use_fswebcam == 0:
             crop_img = crop_img - 1
             if crop_img < 0:
                crop_img = 0
             if camera_connected == 1:
                if crop_img == 0:
                   w = 352
                   h = 288
                   scale = 1.8
                if crop_img == 1:
                   w = 640
                   h = 480
                   scale = 1.25
                if crop_img == 2:
                   w = 800
                   h = 600
                   scale = 1.2
                if crop_img == 3:
                   w = 960
                   h = 720
                   scale = 2
                if crop_img == 4:
                   w = 1920
                   h = 1440
                   scale = 1.35
                if crop_img == 5:
                   w = 2592
                   h = 1944
                if crop_img != oldcrop_img:
                   nscale = int(nscale * scale)
                   escale = int(escale * scale)
                   sscale = int(sscale * scale)
                   wscale = int(wscale * scale)
                if use_RPiwebcam == 0:
                   cam.stop()
                   pygame.camera.init()
                   if crop_img == 0:
                      cam = pygame.camera.Camera("/dev/video0",(352,288))
                   if crop_img == 1 and max_res >= 1:
                      cam = pygame.camera.Camera("/dev/video0",(640,480))
                   if crop_img == 2 and max_res >= 2:
                      cam = pygame.camera.Camera("/dev/video0",(800,600))
                   if crop_img == 3 and max_res >= 3:
                      cam = pygame.camera.Camera("/dev/video0",(960,720))
                   cam.start()
                if crop_img == 0:
                   offset3 = offset3/2
                   offset4 = offset4/2
             if camera_connected == 0:                
                wd = 20 + (crop_img * 4)
                hd = wd
          if z == 25:
             nsi = nsi + 1
             if nsi > 1:
                nsi = 0
          if z == 35:
             ewi = ewi + 1
             if ewi > 1:
                ewi = 0
          if (z == 165 or z == 175 or z == 185):
             deffile = "config" + str((z-155)/10)
             fil = "0000"
             timp = str(auto_g) + fil[len(str(nscale)):len(str(nscale))+4] + str(nscale) + fil[len(str(sscale)):len(str(sscale))+4] + str(sscale)
             timp = timp + fil[len(str(escale)):len(str(escale))+4] + str(escale) + fil[len(str(wscale)):len(str(wscale))+4] +str(wscale) + str(ewi)
             timp = timp + str(nsi) +fil[len(str(crop)):len(str(crop))+4] + str(crop)
             if offset3 < 0:
                offset3a = 0-offset3
                timp = timp + "9"
             else:
                offset3a = offset3
                timp = timp + "0"
             timp = timp + fil[len(str(offset3a))+1:len(str(offset3a))+4] + str(offset3a)
             if offset4 < 0:
                offset4a = 0-offset4
                timp = timp + "9"
             else:
                offset4a = offset4
                timp = timp + "0"
             timp = timp + fil[len(str(offset4a))+1:len(str(offset4a))+4] + str(offset4a) + fil[len(str(Intervals)):len(str(Intervals))+4] + str(Intervals) + str(log)
             timp = timp + str(frames) + fil[len(str(Sens)):len(str(Sens))+4] + str(Sens) + str(thres) + str(graph) + str(nr) + str(plot)
             timp = timp + str(auto_win) + str(auto_t) + str(crop_img)
             timp = timp + fil[len(str(rpibr)):len(str(rpibr))+4] + str(rpibr)
             if rpico < 0:
                rpicoa = 0-rpico
                timp = timp + "9"
             else:
                rpicoa = rpico
                timp = timp + "0"
             timp = timp + fil[len(str(rpicoa))+1:len(str(rpicoa))+4] + str(rpicoa)                         
             if rpiev < 0:
                rpieva = 0-rpiev
                timp = timp + "9"
             else:
                rpieva = rpiev
                timp = timp + "0"
             timp = timp + fil[len(str(rpieva))+1:len(str(rpieva))+4] + str(rpieva) + fil[len(str(int(rpiss/1000))):len(str(int(rpiss/1000)))+4] + str(int(rpiss/1000)) + fil[len(str(rpiISO)):len(str(rpiISO))+4] + str(rpiISO) +rpiex
             
             file = open(deffile + ".txt", "w")
             file.write(timp)
             file.close()
          if (z == 125 or z == 135 or z == 145):
             deffile = "config" + str((z-115)/10)
             file = open(deffile + ".txt","r")
             inputx = file.readline()
             file.close()
             auto_g = int(inputx[0:1])
             nscale = int(inputx[1:5])
             sscale = int(inputx[5:9])
             escale = int(inputx[9:13])
             wscale = int(inputx[13:17])
             ewi = int(inputx[17:18])
             nsi = int(inputx[18:19])
             crop = int(inputx[19:23])
             offset3 = int(inputx[23:27])
             if offset3 > 9000:
                offset3 = 0-(offset3-9000)
             offset4 = int(inputx[27:31])
             if offset4 > 9000:
                offset4 = 0-(offset4-9000)
             Intervals = int(inputx[31:35])
             log2 = log
             log = int(inputx[35:36])
             if log == 1 and log2 == 0:
                now = datetime.datetime.now()
                month = now.month
                if month < 10:
                   month = "0" + str(month)
                day = now.day
                if day < 10:
                   day = "0" + str(day)
                hour = now.hour
                if hour < 10:
                   hour = "0" + str(hour)
                minute = now.minute
                if minute < 10:
                   minute = "0" + str(minute)
                second = now.second
                if second < 10:
                   second = "0" + str(second)   
                logfile = "/tmp/"+str(now.year)+str(month)+str(day)+str(hour)+str(minute)+str(second)+".txt"
                keys (" Logging to " + logfile,16,redColor,0,height+1,1)
                time.sleep(2)
                keys (" Logging to " + logfile,16,blackColor,0,height+1,1)
             frames = int(inputx[36:37])
             Sens = int(inputx[37:41])
             thres = int(inputx[41:42])
             graph = int(inputx[42:43])
             nr = int(inputx[43:44])
             plot = int(inputx[44:45])
             auto_win = int(inputx[45:46])
             auto_t = int(inputx[46:47])
             if camera_connected == 1 and use_fswebcam == 0:
                crop_img = int(inputx[47:48])
                if crop_img == 0:
                   w = 352
                   h = 288
                if crop_img == 1:
                   w = 640
                   h = 480
                if crop_img == 2:
                   w = 800
                   h = 600
                if crop_img == 3:
                   w = 960
                   h = 720
                if crop_img == 4:
                   w = 1920
                   h = 1440
                if crop_img == 5:
                   w = 2592
                   h = 1944
                if use_RPiwebcam == 0:
                   cam.stop()
                   pygame.camera.init()
                   if crop_img == 0:
                      cam = pygame.camera.Camera("/dev/video0",(352,288))
                   if crop_img == 1 and max_res >= 1:
                      cam = pygame.camera.Camera("/dev/video0",(640,480))
                   if crop_img == 2 and max_res >= 2:
                      cam = pygame.camera.Camera("/dev/video0",(800,600))
                   if crop_img == 3 and max_res >= 3:
                      cam = pygame.camera.Camera("/dev/video0",(960,720))
                   cam.start()
             if camera_connected == 0:
                crop_img = int(inputx[47:48])
                wd = 20 + (crop_img * 4)
                hd = wd
             rpibr = int(inputx[48:52])
             rpico = int(inputx[52:56])
             if rpico > 9000:
                rpico = 0-(rpico-9000)
             rpiev = int(inputx[56:60])
             if rpiev > 9000:
                rpiev = 0-(rpiev-9000)
             rpiss = (int(inputx[60:64]))*1000
             rpiISO = int(inputx[64:68])
             rpiex = inputx[68:71]
             if rpiex == 'aut':
                rpiex = 'auto'
             if rpiex == 'nig':
                rpiex = 'night'
             if rpiex == 'fir':
                rpiex = 'fireworks'
                
                   

             



