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
import subprocess
import time
import shlex #command line splitting
import thread

#from asyncproc import Process

#Konstanten - oder so
akku_typ = ["NiCd", "NiMH", "Blei", "Bgel", "LiIO", "LiPo", "LiFe", "Uixx"]
amprogramm = ["Lade", "Entladen", "E+L", "L+E", "(L)E+L", "(E)L+E", "Sender"]
ladeart = ["Konst", "Puls", "Reflex"]
stromwahl = ["Auto", "Limit", "Fest", "Ext. Wiederstand"]
stoppmethode = ["Lademenge", "Gradient", "Delta-Peak-1", "Delta-Peak-2", "Delta-Peak-3"]
fehlercode = [ "Akku Stop", "Akku Voll", "Akku Leer", "Fehler Timeout", "Fehler Lade-Menge", "Fehler Akku zu Heiss", "Fehler Versorgungsspannung", "Fehler Akkuspannung,", "Fehler Zellenspannung,", "Fehler Alarmeingang", "Fehler Stromregler", "Fehler Polung/Kurzschluss", "Fehler Regelfenster", "Fehler Messfenster", "Fehler Temperatur", "Fehler Tempsens", "Fehler Hardware"]

liporgb = ["3399ff", "55ff00", "ff9922", "3311cc", "123456", "ff0000", "3388cc", "cc8833", "88cc33", "ffff00", "ff00ff", "00ffff"]

anzahl_zellen = 0

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
    previous_line1 = ""
    previousline2 = ""
    current_time1 = 0
    previous_time1 = 0
    current_time2 = 0
    previous_time2 = 0

    print "*************************************************"
    print "****             Serial-Splitting            ****"
    print "****                                         ****"

    #TODO python like...
    os.system("cp '" + exe_dir + "/serial-akkumatik.dat' '" + exe_dir + "/.tmp'")
    os.system("rm " + exe_dir + "/Akku?-??.dat")
    os.system("rm " + exe_dir + "/Akku?-??.png")
    fhI = open_file(exe_dir + '/.tmp', "r")

    for line in fhI.readlines():

        file_line += 1

        #filter out useless lines
        #could also check for last thing is a newline ... hm.
        #TODO: won't work when some spezial line got printed
        if len(previous_line1) > len(line) and previous_line1 > 0:
            continue #probably last broken line

        if line[2:10] == "00:00:00": #not begun yet
            continue

        #if line[11:16] == "00000": #no volt lines
          #print ("FILTER OUT: Volt has Zero value")
          #continue

        if line[0:1] == "1":

            current_time1 = long(line[2:4]) * 60 + long(line[5:7]) * 60 + long(line[8:10]) #in seconds

            if previous_time1 == current_time1:  #duplicate time -> ignore (so far)
                #print ("FILTER OUT: Duplicate Time. Line [ " + str(file_line) + "] ")
                continue

            previous_line1 = line

            line_counter1 += 1

            if current_time1 < previous_time1:
                fname = exe_dir + '/Akku1-'+ "%02i" % (file_zaehler1)+'.dat'
                fh1 = open_file(fname, "w+")
                fh1.write(ausgang1_part)
                fh1.close()
                print "**** Generated: " + "%28s" % (fname[-27:]) + " ****"
                file_zaehler1 += 1
                ausgang1_part = line
                line_counter1 = 0
            else:
                ausgang1_part += line

            previous_time1 = current_time1

        elif line[0:1] == "2": #"2"

            current_time2 = long(line[2:4]) * 60 + long(line[5:7]) * 60 + long(line[8:10]) #in seconds

            if previous_time2 == current_time2:  #duplicate time -> ignore so far
                print ("FILTER OUT: Duplicate Time. Line [ " + str(file_line) + "] ")
                continue

            previousline2 = line

            line_counter2 += 1
            if line[2:10] == "00:00:01" and line_counter2 > 1: #only write when did not just begun
                fname = exe_dir + '/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
                fh2 = open_file(fname, "w+")
                fh2.write(ausgang2_part)
                fh2.close()
                print "**** Generated: " + "%28s" % (fname[-27:]) + " ****"
                file_zaehler2 += 1
                ausgang2_part = line
                line_counter2 = 0
            else:
                ausgang2_part += line

            previous_time2 = current_time2

        else:
            print "==============================================================="
            print "SPEZ: " + line
            print "==============================================================="



    if len(ausgang1_part) > 0:
        fname = exe_dir + '/Akku1-'+ "%02i" % (file_zaehler1)+'.dat'
        fh1 = open_file(fname, "w+")
        fh1.write(ausgang1_part)
        fh1.close()
        print "**** Generated: " + "%28s" % (fname[-27:]) + " ****"
    if len(ausgang2_part) > 0:
        fname = exe_dir + '/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
        fh2 = open_file(fname, "w+")
        fh2.write(ausgang2_part)
        print "**** Generated: " + "%28s" % (fname[-27:]) + " ****"

    #close files
    fhI.close()


    os.system("rm '" + exe_dir + "/.tmp'")

def lipo_gnuplot(line_a):
    global liporgb
    gpst = ""

    gpst += 'set nolabel;\n'
    gpst += 'set ylabel "mVolt Zellen (Avg)"\n'
    gpst += 'set yrange [3000:4250];\n'
    gpst += 'set ytics nomirror;\n'

    gpst += 'set y2range [-16:16];\n'
    gpst += 'set y2label "Balancer Delta";\n'
    gpst += 'set y2tics 4;\n'
    gpst += 'set my2tics 4;\n'

    gpst += "plot "

    avg_string = "("
    x = 0
    for i in range(18, len(line_a) - 1):
        avg_string += "$"+str(i+1)+"+"
        x += 1
    avg_string = avg_string[0:-1] + ")/" + str(x)

    for i in range(18, len(line_a) - 1):
        gpst += 'wfile using 2:($'+str(i+1)+'-'+ str(avg_string)+') smooth bezier with lines title " Zelle '+str(i-17)+'" axes x1y2 lw 1 lc rgbcolor "#'+liporgb[i-18]+'",'

    gpst += 'wfile using 2:('+avg_string+') with lines title "Average mV" lw 2 lc rgbcolor "#ff3333";'
    return (gpst)

def else_gnuplot():
    gpst = ""
    gpst += 'set y2range [*:*];\n'
    gpst += 'set y2label "Innerer Widerstand Ri (mOhm)";\n'
    gpst += 'set y2tics border;\n'

    gpst += 'plot wfile using 2:3 with lines title "mVolt" lw 2 lc rgbcolor "#ff0000", \
                wfile using 2:7 with lines title "mOhm" axes x1y2 lw 1 lc rgbcolor "#000044";'
    return gpst

def gnuplot():

    g = Gnuplot.Gnuplot(debug=1)

    path = exe_dir
    qiv_files = ""
    dirList=os.listdir(path)
    dirList.sort()
    print "*************************************************"
    print "****             (Gnu-)Plotting              ****"
    print "****                                         ****"
    for fname in dirList:
        if fname[0:4] == "Akku" and fname[5] == "-" and fname [8:12] == ".dat":
            qiv_files += exe_dir + "/" + fname[:-4] + ".png "

            f = open_file(exe_dir + "/" + fname, "r")
            while True: #ignore other than real data lines
                l = f.readline()
                if l[0] != "#":
                    break

            f.close()
            line_a = l.split("\x7f")
            phasenr = long(line_a[9])
            if phasenr >= 1 and phasenr <= 5:
                phase = "LADEN"
            elif phasenr >= 7 and phasenr < 9:
                phase = "ENTLADEN"
            elif phasenr == 10:
                phase = "PAUSE (Entladespannung erreicht)"
            elif phasenr == 0:
                phase = "STOP (Erhaltungladung)"
            else:
                phase = "Unbekannte Phase <"+str(phasenr)+"> (oder so)"

            atyp = long(line_a[12])

            #g('set terminal wxt')
            g('set terminal png size 1280, 1024;')
            g('set output "' + exe_dir + "/" + fname[:-4] + '.png"')

            g('set title "Akkumatik (Stefan Estner)";')
            g('set xdata time;')
            g("set datafile separator '\x7f';")
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

            g('set size 1.0,0.45;')
            g('set origin 0.0,0.5;')

            g('wfile="' + exe_dir + "/" + fname + '";')

            g('set title "' + phase + ' (' + fname + ')";')

            g('plot \
                wfile using 2:4 with lines title "mA" lw 2 lc rgbcolor "#009900" , \
                wfile using 2:5 smooth bezier with lines title "mAh" lw 2 lc rgbcolor "#0000ff", \
                wfile using 2:8 smooth bezier with lines title "Bat C" axes x1y2 lc rgbcolor "#cc0000" , \
                wfile using 2:18 smooth bezier with lines title "KK C" axes x1y2 lc rgbcolor "#222222";')


            g('set nolabel;')
            g('set notitle;')

            g('set ylabel "mVolt Akku"')
            g('set yrange [*:*];')
            g('set ytics nomirror;')

            g('set size 1.0,0.45;')
            g('set origin 0.0,0.0;')

            if atyp == 5 and len(line_a) > 18: #lipo -> Balancer graph TODO what when no balancer
                g(lipo_gnuplot(line_a))
            else:
                g(else_gnuplot())

            g('set nomultiplot;')
            g('reset')
            print "**** Generated: "+"%24s"%(fname[-27:-4])+".png ****"
        else:
            continue

    time.sleep(1.8) #sonst finded qiv (noch) nichts allenfall

    args = shlex.split(qiv_files)
    arguments = ' '.join(str(n) for n in args)
    thread.start_new_thread(os.system,('/usr/local/bin/qiv '+arguments,))

class akkumatik_display:

    def delete_event(self, widget, event, data=None):
    # Change FALSE to TRUE and the main window will not be destroyed
    # with a "delete_event".
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def buttoncb (self, widget, data=None):
        if data == "Chart":
            self.f.flush()
            os.fsync(self.f)
            filesplit()
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
        self.window.set_size_request(792,168)
        self.window.set_default_size(792,168)
        self.window.set_position(gtk.WIN_POS_CENTER)

        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.set_border_width(10)


        self.hbox = gtk.HBox()
        self.window.add(self.hbox)
        self.hbox.connect('expose-event', self.draw_pixbuf)

        self.label = gtk.Label()
        self.label.modify_font(pango.FontDescription("mono 22"))

        self.hbox.pack_start(self.label, False, False, 50)
        self.vbox = gtk.VBox()

        self.hbox.pack_end(self.vbox, False, False, 0)

        self.button1 = gtk.Button("Chart")
        self.button1.connect("clicked", self.buttoncb, "Chart")
        self.vbox.pack_start(self.button1, True, True, 0)
        self.button2 = gtk.Button("Exit")
        self.button2.connect("clicked", self.buttoncb, "Exit")
        self.vbox.pack_start(self.button2, True, True, 0)




        self.ser = serial.Serial(
            port='/dev/ttyS0',
            baudrate = 9600,
            parity = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            #bytesize=serial.EIGHTBITS, #geht nicht irgendwie
            bytesize = serial.SEVENBITS,
            dsrdtr = True,
            rtscts = False,
            timeout = 0, #0.2 worked nicely
            interCharTimeout = None
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

        if len(sys.argv) > 1 and (sys.argv[1] == "-c" or sys.argv[1] == "-C"):
            self.f = open_file(exe_dir + '/serial-akkumatik.dat', 'a')
            print "CONTINUE: Appending to file"
        elif len(sys.argv) > 1 and (sys.argv[1] == "-n" or sys.argv[1] == "-N"):
            self.f = open_file(exe_dir + '/serial-akkumatik.dat', 'w+')
        else:
            raw_input("Press key to continue with *new* data-collecting (else Ctrl-D)")
            self.f = open_file(exe_dir + '/serial-akkumatik.dat', 'w+')

        self.window.show_all() # after file-open (what is needed on plotting)...

        #finally begin collecting
        gobject.timeout_add(490, self.read_line) # too low - means long blocking on ser.readline
                                                 # should be < 500, since every 500 new line
    def output_data(self, output_tty, output):
        #terminal output
        sys.stdout.write (output_tty)
        sys.stdout.flush()

        #graphical output
        self.label.set_markup('<span foreground="#333333">'+ output + '</span>')
        while gtk.events_pending():
            gtk.main_iteration()

    def read_line(self):

        global anzahl_zellen

        lin = self.ser.readline()
        self.f.write(lin)

        daten = lin.split('\x7f')
        if len(daten) < 18:
            return True #ignore (defective?) line

        if daten[0] == "1":
            ausgang = str(long(daten[0])) #Ausgang
            zeit = daten[1] #Stunden Minuten Sekunden
            ladeV = long(daten[2])/1000.0 #Akkuspannung mV
            ladeV = "%6.3fV" % (ladeV) #format into string
            ampere = long(daten[3])/1000.0 #Strom A
            ampere = "%+.2fA" % (ampere)
            Ah = long(daten[4])/1000.0 #Ladungsmenge Ah
            VersU = long(daten[5]) #Versorungsspannung mV
            RimOhm = long(daten[6]) #akku-unnen mOhm
            cBat = long(daten[7]) #Akkutemperatur
            tmp_zellen = long(daten[8]) #Zellenzahl / bei Stop -> 'Fehlercode'
            if tmp_zellen <= 50:
                anzahl_zellen = tmp_zellen

            phase = long(daten[9]) #Ladephase 0-stop ...
            zyklus = long(daten[10]) #Zyklus
            sp = long(daten[11]) #Aktive Akkuspeicher
            atyp = akku_typ[long(daten[12])] #Akkutyp
            prg = amprogramm[long(daten[13])] #Programm
            lart = ladeart[long(daten[14])] #Ladeart
            strohmw = stromwahl[long(daten[15])] #stromwahl
            stoppm = stoppmethode[long(daten[16])] #stromwahl
            cKK = long(daten[17]) #KK Celsius

            cellmV = ""
            tmp_a = []
            for cell in daten[18:-1]:
                cellmV += " " + cell + " "
                tmp_a.append(long(cell))

            balance_delta = -1
            if len(tmp_a) > 0:
                balance_delta = max(tmp_a) - min(tmp_a)


            if phase == 0: #dann 'Fehlercode' zwangsweise ...?
                if tmp_zellen >= 53: # FEHLER
                    output_tty = fehlercode[tmp_zellen - 50] + "\n\n"
                    output = fehlercode[tmp_zellen - 50]
                    self.output_data(output_tty, output)
                    return True

                if tmp_zellen >= 50: #'gute' codes
                    phasedesc = "%-11s" % (fehlercode[tmp_zellen - 50])
                    ausgang = ""
                    ladeV = ""

                else:
                    phasedesc = "?????" # should never happen possibly

            #• 51 VOLL   Ladevorgang wurde korrekt beendet, Akku ist voll geladen
            #• 52 LEER   Entladevorgang wurde korrekt beendet, Akku ist leer
            #• TODO: 52 od 51 + "x..." FERTIG Lipo-Lagerprogramm wurde korrekt beendet, Akku ist fertig zum Lagern
            #• TODO: 52 od 51 + "x ": ? MENGE  Vorgang wurde durch eingestelltes Mengenlimit beendet
            #• 50 STOP Vorgang wurde manuell (vorzeitig) beendet
            #• FEHLER Vorgang wurde fehlerhaft beendet

            elif phase == 10:
                phasedesc = "PAUSE"
                ausgang = ""
                ladeV = ""
            else:
                if phase >= 1 and phase <= 5:
                    c = "L"
                elif phase >=7 and phase <= 9:
                    c = "E"
                    phase = "-"

                phasedesc = atyp[0:1] + c + str(phase)

            #terminal print
            output_tty ="[Ausgang %s] [Phase/Zyklus: %s/%i] [%s] [%s] [%.3fAh] [Ri: %imOhm] [%s]\n" % (ausgang, phasedesc, zyklus, ladeV, ampere, Ah, RimOhm, zeit)
            output_tty += "[Programm: %s] [Ladeart %s] [Stromwahl: %s] [Stoppmethode %s]\n" % (prg, lart, strohmw, stoppm)
            output_tty += "[%i°(Batterie)] [%i°(Kuehlkoerper)] [%s x %s][Akkuspeicher: %i]" % (cBat, cKK, anzahl_zellen, atyp, sp)
            if cellmV != "":
                output_tty += "[Zellenspannung mV: %s | Delta: %imV ]" %( cellmV, balance_delta)
            output_tty += "\n\n"

            #< stunde dann Minunte:Sekunden, sonst Stunde:Minuten
            if zeit[0:2] == "00":
                zeit = zeit [3:]
            else:
                zeit = zeit [:-3]

            #label print
            RimOhm = "Ri:%03i" % (RimOhm)
            #TODO:  more elgegant...
            if len(daten) > 18:
                RimOhm = "∆%2imV " % (balance_delta)

            output ="%s%s %s %s|%s %2i°B \n%-7s   %+6.3fAh|%sx%s %2i°K" % (ausgang, phasedesc, ladeV, zeit, RimOhm, cBat, ampere, Ah, anzahl_zellen, atyp, cKK)

            self.output_data(output_tty, output)

        return True

    def main(self):
        gtk.main()

if __name__ == '__main__':
    displ = akkumatik_display()
    displ.main()
