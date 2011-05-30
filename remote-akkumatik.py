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

#Konstanten - oder so
phase_list = ["Voll", "Laden", "SLaden normal?", "3NA", "4NA", "5NA", "6NA", "7NA", "8NA", "Entladen", "Pause", "11NA"] 
exe_dir = sys.path[0]

def open_file(file_name, mode):
    """Open a file."""
    try:
        the_file = open(file_name, mode)
    except(IOError), e:
        print "Unable to open the file", file_name, "Ending program.\n", e
        raw_input("\n\nPress the enter key to exit.")
        sys.exit()
    else:
        return the_file

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

    #TODO python like...
    os.system("cp '" + exe_dir + "/serial-akkumatik.dat' '" + exe_dir + "/.tmp'")
    fhI = open_file(exe_dir + '/.tmp', "r")

    for line in fhI.readlines():
        print "************************"
        print line
        print "************************"
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

                fname = exe_dir + '/Akku1-'+ "%02i" % (file_zaehler1)+'.dat'
                fh1 = open_file(fname, "w+")
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
                fname = exe_dir + '/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
                fh2 = open_file(fname, "w+")
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
          fname = exe_dir + '/Akku1-'+ "%02i" % (file_zaehler1)+'.dat'
          fh1 = open_file(fname, "w+")
          fh1.write(ausgang1_part)
          print "********************************************8************************"
          print "**** Generating: " + fname + " ****"
          print "*********************************************************************"
          fh1.close()
    if len(ausgang2_part) > 0:
          fname = exe_dir + '/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
          fh2 = open_file(fname, "w+")
          print "*********************************************************************"
          print "**** Generating: " + fname + " ****"
          print "*********************************************************************"
          fh2.write(ausgang2_part)
          fh2.close()

    #close files
    fhI.close()
    os.system("rm '" + exe_dir + "/.tmp'")

def gnuplot():

    g = Gnuplot.Gnuplot(debug=1)

    path = exe_dir
    qiv_files = ""
    dirList=os.listdir(path)
    for fname in dirList:
        if fname[0:4] == "Akku" and fname[5] == "-" and fname [8:12] == ".dat":
            qiv_files += exe_dir + "/" + fname[:-4] + ".png "
            print "********************************"
            print "**** Plotting: " + fname + " ****"
            print "********************************"

            #g('set terminal wxt')
            g('set terminal png size 1280, 1024;')
            g('set output "' + exe_dir + "/" + fname[:-4] + '.png"')

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
            g('wfile="' + exe_dir + "/" + fname + '";')
            
            f = open_file(exe_dir + "/" +fname, "r")
            l = f.readline()
            f.close()
            text = (l.split(""))[9]
            g('set title "' + phase_list[long(text)] + '";')

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

            g('plot wfile using 2:7 with lines title "RiOhm" axes x1y2 lw 1 lc rgbcolor "#aabbaa", \
wfile using 2:3 with lines title "mVolt" lw 2 lc rgbcolor "#ff0000";')

            g('set nomultiplot;')

            #    g('set terminal png;')
            #    g('set output "' + arg + '.png"')
            #    g('replot"')
            g('reset')
            print "**************************************"
            print "**** Plot Generated: " + fname[:-4] + ".png ****"
            print "**************************************"
        else:
            continue
    os.system("sleep 1") #sonst finded qiv (noch) nicht
    os.system("/usr/local/bin/qiv " + qiv_files + " &")

class akkumatik_display:

    def delete_event(self, widget, event, data=None):
    # Change FALSE to TRUE and the main window will not be destroyed
    # with a "delete_event".
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def buttoncb (self, widget, data=None):
        if data == "Chart":
            print "*********************"
            print "*** FileSplitting ***"
            print "*********************"
            filesplit()
            print "*********************"
            print "***  Gnuplotting  ***"
            print "*********************"
            gnuplot()

        elif data == "Exit":
            gtk.main_quit()


    def draw_pixbuf(self, widget, event):
        path = exe_dir + '/bilder/Display.jpg'
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


        self.ser = serial.Serial(
            port='/dev/ttyS0',
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            #bytesize=serial.EIGHTBITS, #geht nicht irgendwie
            bytesize=serial.SEVENBITS,
            dsrdtr=True,
            rtscts=False
            #interCharTimeout = 1100 # ??? hm.
            )

#        self.ser = serial.Serial(
#            port='/dev/ttyS0',
#            baudrate=9600,
#            parity=serial.PARITY_ODD,
#            stopbits=serial.STOPBITS_TWO,
#            bytesize=serial.SEVENBITS
#            )



        self.ser.open()
        self.ser.isOpen()

        gobject.timeout_add(1, self.read_line) #1 is prinzipally enough -> readline waits.

        if len(sys.argv) > 1 and (sys.argv[1] == "-c" or sys.argv[1] == "-C"):
            self.f = open_file(exe_dir + '/serial-akkumatik.dat', 'a')
            print "CONTINUE: Appending to file"
        else:
            self.f = open_file(exe_dir + '/serial-akkumatik.dat', 'w+')
        self.i = 0

    def read_line(self):

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
            VersU = long(daten[5])
            RiOhm = long(daten[6])
            cBat = long(daten[7])
            zellen = long(daten[8])

            phase = phase_list[long(daten[9])]

            zyklus = long(daten[10])
            sp = long(daten[11])
            W = long(daten[12])
            Wh = long(daten[13])
            #cKK = long(daten[14])
            cKK = long(daten[17])
            Balanced = long(daten[15])

            output ="%i%s%1i %6.3fV %s %6imA \n %8.3fAh Ri: %4i\n %4i°(B) %4i°(Kk) %4i Z" % (ausgang, phase[0:1], zyklus, ladeV, zeit, mA, mAh, RiOhm, cBat, cKK, zellen)

            output_tty ="Ausgang %1i,  Phase/Zyklus: %s/%1i %8.3fV %s %6imA %8.3fAh Ri Ohm: %4i\n %4i°(Batterie) %4i°(Kuehlkoerper) %4i Zellen" % (ausgang, phase, zyklus, ladeV, zeit, mA, mAh, RiOhm, cBat, cKK, zellen)
            output_tty += "\nBalanced: %i | Watt: %i | Wh: %i | Spannung: %i\n\n" % (Balanced, W, Wh, sp)
            #output = "1LL2 11.9V 4:44\n +2.20A5 +0.137mAh"

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



##   [Anzeige Einstellungen Kanal 01]
##   ## Zeit, Spannung, Strom, Ladung, Versorgungsspannung, Innenwiderstand,
##   ## Temperatur, Zellenzahl, Ladephase (0..5), Zyklusnummer
##   ## nicht in Grafik: Akkuspeicher, Akkutyp, Programm, Ladeart, Stromwahl,
##   ##                  Stopmethode, Entladereduzierung, Erhaltungsladen,
##   ##                  Stop-Delay, DeltaPeakLevel
##   ##
##   ## zusätzliche 3: U/Zelle [V], Leistung [W], Energie [Wh]
##   Zeitbasis                       = Zeit
##   Einheit                         = s
##   Symbol                          = t
##   Messgröße1                      = Spannung
##   Einheit1                        = V
##   Symbol1                         = U
##   Faktor1                         = 
##   OffsetWert1                     = 
##   OffsetSumme1                    = 
##   
##   Messgröße2                      = Strom
##   Einheit2                        = A
##   Symbol2                         = I
##   Faktor2                         = 
##   OffsetWert2                     = 
##   OffsetSumme2                    = 
##   
##   Messgröße3                      = Ladung
##   Einheit3                        = mAh
##   Symbol3                         = C
##   Faktor3                         = 
##   OffsetWert3                     = 
##   OffsetSumme3                    = 
##   
##   Messgröße4                      = V-Spg.
##   Einheit4                        = V
##   Symbol4                         = U
##   Faktor4                         = 
##   OffsetWert4                     = 
##   OffsetSumme4                    = 
##   
##   Messgröße5                      = Ri/Zelle
##   Einheit5                        = mOhm
##   Symbol5                         = R
##   Faktor5                         = 
##   OffsetWert5                     = 
##   OffsetSumme5                    = 
##   
##   Messgröße6                      = Temperatur
##   Einheit6                        = °C
##   Symbol6                         = T
##   Faktor6                         = 
##   OffsetWert6                     = 
##   OffsetSumme6                    = 
##   
##   Messgröße7                      = Zellen
##   Einheit7                        = St.
##   Symbol7                         = 
##   Faktor7                         = 
##   OffsetWert7                     = 
##   OffsetSumme7                    = 
##   
##   Messgröße8                      = Phase
##   Einheit8                        = Nr.
##   Symbol8                         = 
##   Faktor8                         = 
##   OffsetWert8                     = 
##   OffsetSumme8                    = 
##   
##   Messgröße9                      = Zyklus
##   Einheit9                        = Nr.
##   Symbol9                         = 
##   Faktor9                         = 
##   OffsetWert9                     = 
##   OffsetSumme9                    = 
##   
##   Messgröße10                     = Spg./Zelle
##   Einheit10                       = V*
##   Symbol10                        = U*
##   Faktor10                        = 
##   OffsetWert10                    = 
##   OffsetSumme10                   = 
##   
##   Messgröße11                     = Leistung
##   Einheit11                       = W
##   Symbol11                        = P
##   Faktor11                        = 
##   OffsetWert11                    = 
##   OffsetSumme11                   = 
##   
##   Messgröße12                     = Energie
##   Einheit12                       = Wh
##   Symbol12                        = E
##   Faktor12                        = 
##   OffsetWert12                    = 
##   OffsetSumme12                   = 
##   
##   Messgröße13                     = Kühlkörper
##   Einheit13                       = °C
##   Symbol13                        = T
##   Faktor13                        = 
##   OffsetWert13                    = 
##   OffsetSumme13                   = 
##   
##   Messgröße14                     = Balanced
##   Einheit14                       = mV
##   Symbol14                        = Bal
##   Faktor14                        = 
##   OffsetWert14                    = 
##   OffsetSumme14                   = 
##   
##   Messgröße15                     = Zelle1
##   Einheit15                       = V
##   Symbol15                        = U
##   Faktor15                        = 
##   OffsetWert15                    = 
##   OffsetSumme15                   = 
##   
##   OneAxisName15                   = Zelle 1-12 [V]
##   OneAxisGroup15                  = 1
##   
##   Messgröße16                     = Zelle2
##   Einheit16                       = V
##   Symbol16                        = U
##   Faktor16                        = 
##   OffsetWert16                    = 
##   OffsetSumme16                   = 
##   
##   OneAxisGroup16                  = 1
##   
##   Messgröße17                     = Zelle3
##   Einheit17                       = V
##   Symbol17                        = U
##   Faktor17                        = 
##   OffsetWert17                    = 
##   OffsetSumme17                   = 
##   
##   OneAxisGroup17                  = 1
##   
##   Messgröße18                     = Zelle4
##   Einheit18                       = V
##   Symbol18                        = U
##   Faktor18                        = 
##   OffsetWert18                    = 
##   OffsetSumme18                   = 
##   
##   OneAxisGroup18                  = 1
##   
##   Messgröße19                     = Zelle5
##   Einheit19                       = V
##   Symbol19                        = U
##   Faktor19                        = 
##   OffsetWert19                    = 
##   OffsetSumme19                   = 
##   
##   OneAxisGroup19                  = 1
##   
##   Messgröße20                     = Zelle6
##   Einheit20                       = V
##   Symbol20                        = U
##   Faktor20                        = 
##   OffsetWert20                    = 
##   OffsetSumme20                   = 
##   
##   OneAxisGroup20                  = 1
##   
##   Messgröße21                     = Zelle7
##   Einheit21                       = V
##   Symbol21                        = U
##   Faktor21                        = 
##   OffsetWert21                    = 
##   OffsetSumme21                   = 
##   
##   OneAxisGroup21                  = 1
##   
##   Messgröße22                     = Zelle8
##   Einheit22                       = V
##   Symbol22                        = U
##   Faktor22                        = 
##   OffsetWert22                    = 
##   OffsetSumme22                   = 
##   
##   OneAxisGroup22                  = 1
##   
##   Messgröße23                     = Zelle9
##   Einheit23                       = V
##   Symbol23                        = U
##   Faktor23                        = 
##   OffsetWert23                    = 
##   OffsetSumme23                   = 
##   
##   OneAxisGroup23                  = 1
##   
##   Messgröße24                     = Zelle10
##   Einheit24                       = V
##   Symbol24                        = U
##   Faktor24                        = 
##   OffsetWert24                    = 
##   OffsetSumme24                   = 
##   
##   OneAxisGroup24                  = 1
##   
##   Messgröße25                     = Zelle11
##   Einheit25                       = V
##   Symbol25                        = U
##   Faktor25                        = 
##   OffsetWert25                    = 
##   OffsetSumme25                   = 
##   
##   OneAxisGroup25                  = 1
##   
##   Messgröße26                     = Zelle12
##   Einheit26                       = V
##   Symbol26                        = U
##   Faktor26                        = 
##   OffsetWert26                    = 
##   OffsetSumme26                   = 
##   
##   OneAxisGroup26                  = 1
##   

