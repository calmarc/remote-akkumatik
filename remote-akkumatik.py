#!/usr/bin/env python
# coding=utf-8

import serial
import sys
import pygtk
pygtk.require('2.0')
import gtk
import pango
import gobject
import os
import Gnuplot, Gnuplot.funcutils
from subprocess import *

def filesplit():
      file_line = 0
      line_counter1 = 0
      line_counter2 = 0
      oldline = ""
      file_zaehler1 = 1
      file_zaehler2 = 1
      flag1 = False
      flag2 = False
      ausgang1_part = ""
      ausgang2_part = ""
      oldline1 = ""
      oldline2 = ""

      fhI = open('/home/calmar/akkumatik/serial-akkumatik.dat', "r")

      for line in fhI.readlines():
            file_line += 1
            #filter out useless lines
            if line[2:10] == "00:00:00": #not begun yet
                  continue

            #if line[11:16] == "00000": #no volt lines
                #print ("FILTER OUT: Volt has Zero value")
                #continue

            if line[0:1] == "1":

                if oldline1[2:10] == line[2:10]:  #duplicate time for some reason
                    print ("FILTER OUT: Duplicate Time. Line [ " + str(file_line) + "] ")
                    continue

                oldline1 = line

                line_counter1 += 1
                if line[2:10] == "00:00:01" and line_counter1 > 1: #don't write when it just begun

                    fname = '/home/calmar/akkumatik/Akku1-'+ "%02i" % (file_zaehler1)+'.dat'
                    fh1 = open(fname, "w+")
                    fh1.write(ausgang1_part)
                    print "*********************************************************************"
                    print "**** Generating: " + fname + " ****"
                    print "*********************************************************************"
                    fh1.close()
                    file_zaehler1 += 1
                    ausgang1_part = line
                    line_counter1 = 0
                else:
                    ausgang1_part += line

            elif line[0:1] == "2": #"2"
                if oldline2[2:10] == line[2:10]:  #duplicate time for some reason
                    print ("FILTER OUT: Duplicate Time")
                    continue

                oldline2 = line

                line_counter2 += 1
                if line[2:10] == "00:00:01" and line_counter2 > 1: #don't write when it just begun
                    fname = '/home/calmar/akkumatik/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
                    fh2 = open(fname, "w+")
                    fh2.write(ausgang2_part)
                    print "*********************************************************************"
                    print "**** Generating: " + fname + " ****"
                    print "*********************************************************************"
                    fh2.close()
                    file_zaehler2 += 1
                    ausgang2_part = line
                    line_counter2 = 0
                else:
                    ausgang2_part += line

      if len(ausgang1_part) > 0:
            fname = '/home/calmar/akkumatik/Akku1-'+ "%02i" % (file_zaehler1)+'.dat'
            fh1 = open(fname, "w+")
            fh1.write(ausgang1_part)
            print "********************************************8************************"
            print "**** Generating: " + fname + " ****"
            print "*********************************************************************"
            fh1.close()
      if len(ausgang2_part) > 0:
            fname = '/home/calmar/akkumatik/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
            fh2 = open(fname, "w+")
            print "*********************************************************************"
            print "**** Generating: " + fname + " ****"
            print "*********************************************************************"
            fh2.write(ausgang2_part)
            fh2.close()

      #close files
      fhI.close()

def gnuplot():

    g = Gnuplot.Gnuplot(debug=1)

    path="."
    dirList=os.listdir(path)
    for fname in dirList:
        if fname[0:4] == "Akku" and fname[5] == "-" and fname [8:12] == ".dat":
            print "********************************"
            print "**** Plotting: " + fname + " ****"
            print "********************************"

            #g('set terminal wxt')
            g('set terminal png size 1280, 1024;')
            g('set output "' + fname[:-4] + '.png"')

            g('set title "Akkumatik (Stefan Estner)";')
            g('set xdata time;')
            g('set datafile separator "";')
            g('set timefmt "%H:%M:%S";')
            g('set grid')

            #set bmargin 5
            g('set lmargin 10')
            g('set rmargin 10')
            #set tmargin 5
            g('set multiplot;')

            g('set key box')
            g('set ylabel "Laden mA / Kapazitaet mAh"')
            g('set ytics nomirror;')

            g('set y2range [-10:70];')
            g('set y2label "Grad Celsius";')
            g('set y2tics border;')

            g('set nolabel;')
            g('set xtics axis;')

            g('set size 1.0,0.50;')

            g('set origin 0.0,0.5;')
            g('wfile="' + fname + '";')
            g('set title "Ent-Laden";')

            g('plot \
wfile using 2:4 with lines title "mA" lw 2 lc rgbcolor "#009900" , \
wfile using 2:5 smooth bezier with lines title "mAh" lw 2 lc rgbcolor "#0000ff", \
wfile using 2:8 smooth bezier with lines title "Bat C" axes x1y2 lc rgbcolor "#cc0000" , \
wfile using 2:18 smooth bezier with lines title "KK C" axes x1y2 lc rgbcolor "#999999";')


            g('set nolabel;')
            g('set notitle;')

            g('set ylabel "mVolt Akku"')
            g('set yrange [0:*];')
            g('set ytics nomirror;')

            g('set y2range [*:*];')
            g('set y2label "Innerer Widerstand Ohm";')
            g('set y2tics border;')


            g('set size 1.0,0.50;')
            g('set origin 0.0,0.0;')

            g('plot wfile using 2:6 with lines title "IOhm" axes x1y2 lw 1 lc rgbcolor "#aabbaa", \
wfile using 2:3 with lines title "mVolt" lw 2 lc rgbcolor "#ff0000";')

            g('set nomultiplot;')

            #    g('set terminal png;')
            #    g('set output "' + arg + '.png"')
            #    g('replot"')
            g('reset')
            #raw_input('Please press return to continue...\n')
            print "**************************************"
            print "**** Plot Generated: " + fname[:-4] + ".png ****"
            print "**************************************"
        else:
            continue
    os.system("/usr/local/bin/qiv " + "*.png" )
    #stuff0 = call("ls")

class akkumatik_display:

    def delete_event(self, widget, event, data=None):
    # Change FALSE to TRUE and the main window will not be destroyed
    # with a "delete_event".
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def buttoncb (self, widget, data=None):
        if data == "Chart":
            filesplit()
            print "Hello again - %s was pressed" % data
            gnuplot()

        elif data == "Exit":
            gtk.main_quit()


    def draw_pixbuf(self, widget, event):
        path = 'Display.jpg'
        pixbuf = gtk.gdk.pixbuf_new_from_file(path)
        widget.window.draw_pixbuf(widget.style.bg_gc[gtk.STATE_NORMAL], pixbuf, 0, 0, 0,0)

    def __init__(self):

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title('Akkumatic Remote Display')
        self.window.set_size_request(622,168)
        self.window.set_default_size(622,168)
        self.window.set_position(gtk.WIN_POS_CENTER)

        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.set_border_width(10)


        self.hbox = gtk.HBox()
        self.window.add(self.hbox)
        self.hbox.connect('expose-event', self.draw_pixbuf)

        self.label = gtk.Label()
        self.label.modify_font(pango.FontDescription("sans 22"))

        self.hbox.pack_start(self.label, True, False, 0)
        self.vbox = gtk.VBox()

        self.hbox.pack_start(self.vbox, False, False, 0)

        self.button1 = gtk.Button("Chart")
        self.button1.connect("clicked", self.buttoncb, "Chart")
        self.vbox.pack_start(self.button1, True, True, 0)
        self.button2 = gtk.Button("Exit")
        self.button2.connect("clicked", self.buttoncb, "Exit")
        self.vbox.pack_start(self.button2, True, True, 0)


        self.window.show_all()

#      gobject.timeout_add(1, self.read_line) #1 is prinzipally enough -> readline waits.

#      self.ser = serial.Serial(
#          port='/dev/ttyS0',
#          baudrate=9600,
#          parity=serial.PARITY_ODD,
#          stopbits=serial.STOPBITS_TWO,
#          bytesize=serial.SEVENBITS
#      )
#
#      self.ser.open()
#      self.ser.isOpen()
#
#      self.f = open('/home/calmar/akkumatik/serial-akkumatik.dat', 'w')
#
#      self.i = 0

    def read_line(self):

    #output = "1LL2 11.9V 4:44\n +2.20A5 +0.137mAh"
    #self.i +=1
    #self.label.set_markup('<span foreground="#333333">' + str(self.i) + output + '</span>')
    #return True

    #it hangs here

        lin = self.ser.readline()
        self.f.write(lin)

        daten = lin.split('\x7f')
        if daten[0] == "1":
            ausgang = long(daten[0])
            zeit = daten[1]
            ladeV = long(daten[2])/1000.0
            mA = long(daten[3])
            mAh = long(daten[4])/1000.0
            ri = daten[6]
            cBat = long(daten[7])
            zellen = daten[8]
            phase = daten[9]
            zyklus = daten[10]
            sp = daten[11]
            watt = daten[12]
            Wh = daten[13]
            cKK = long(daten[17])

            output ="%i: %8.3fV %s\n %6imA %8.3fAh\n %4i°(B) %4i°(Kk) %4i iOhm" % (ausgang, ladeV, zeit, mA, mAh, cBat, cKK, ri)
            output_tty ="%i: %8.3fV %s %6imA %8.3fAh %4i°(B) %4i°(Kk) %4i iOhm\n" % (ausgang, ladeV, zeit, mA, mAh, cBat, cKK, ri)
      #output = daten[0] + ": " \
         #+ daten[1] + " " \
         #+ str(long(daten[2]) / 1000.0) + "V " \
         #+ str(long(daten[3])) + "mA" \
         #+ " Ladung:" + str(long(daten[4])) \
         #+ " Ri:" + daten[6] \
         #+ " " + str(long(daten[7])) + "C" \
         #+ "\n" \
         #+ " Zellen:" + str(long(daten[8])) \
         #+ " Phase:" + str(long(daten[9])) \
         #+ " Zyklus:" + daten[10] \
         #+ " Sp/n:" + daten[11] \
         #+ " " + daten[12] + "W " \
         #+ daten[13] + "Wh " \
         #+ daten[17] + "C    "
      #output += '\x0D'

      #terminal output

            sys.stdout.write (output_tty)
            sys.stdout.flush()

      #graphical output
            self.label.set_markup('<span foreground="#333333">'+ output + '</span>')
            while gtk.events_pending():
                gtk.main_iteration()

        return True
                     
    def main(self):
        gtk.main()


if __name__ == '__main__':
    displ = akkumatik_display()
    displ.main()

