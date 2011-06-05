#!/usr/bin/env python
# coding=utf-8

import os
import sys

import shutil
import shlex #command line splitting
import tempfile

import time
import subprocess
import thread

import pygtk
pygtk.require('2.0')
import gtk
import pango
import gobject

import Gnuplot, Gnuplot.funcutils
import serial


class akkumatik_display:

##########################################}}}
#GnuPlotting stuff{{{
##########################################


    def lipo_gnuplot(self, line_a, rangeval):
        """lipo gnuplot 2nd chart"""
        gpst = ""

        gpst += 'set nolabel;\n'
        gpst += 'set ylabel "mVolt Zellen (Avg)"\n'
        gpst += 'set yrange [2992:4208];\n'
        gpst += 'set ytics nomirror;\n'

        #gpst += 'set autoscale {y{|min|max|fixmin|fixmax|fix} | fix | keepfix}

        gpst += 'set y2range ['+str(-1*rangeval)+':'+str(rangeval)+'];\n'
        gpst += 'set y2label "Balancer ∆";\n'
        gpst += 'set y2tics 4;\n'
        gpst += 'set my2tics 4;\n'

        gpst += "plot "

        avg_string = "("
        x = 0
        for i in range(18, len(line_a) - 1):
            avg_string += "$"+str(i+1)+"+"
            x += 1
        avg_string = avg_string[0:-1] + ")/" + str(x)

        gpst += 'wfile using 2:('+avg_string+') with lines title "mV (avg)" lw 2 lc rgbcolor "#cc3333" '

        for i in range(18, len(line_a) - 1):
            gpst += ', wfile using 2:($'+str(i+1)+'-'+ str(avg_string)+') smooth bezier with lines title "∆ '+str(i-17)+'" axes x1y2 lw 1 lc rgbcolor "#'+self.LIPORGB[i-18]+'"'
        gpst += ';'

        return (gpst)

    def else_gnuplot(self):
        """other than lipo gnuplot 2nd chart"""

        gpst = ""

        gpst +=  'set ylabel "mVolt Pro Zelle (Avg. von '+str(self.anzahl_zellen[self.gewaehlter_ausgang])+' Zellen)"\n'
        gpst +=  'set yrange [*:*];\n'
        gpst +=  'set ytics nomirror;\n'

        #gpst += 'set y2range [*:*];\n'
        #gpst += 'set y2label "Innerer Widerstand Ri (mOhm)";\n'
        #gpst += 'set y2tics border;\n'

        gpst += 'plot wfile using 2:($3/'+str(self.anzahl_zellen[self.gewaehlter_ausgang])+') with lines title "mVolt" lw 2 lc rgbcolor "#ff0000";'
        return gpst

    def nixx_gnuplot(self):
        """NiCd and NiMh gnuplot 2nd chart"""

        gpst = ""

        gpst +=  'set ylabel "mVolt Pro Zelle (Avg. von '+str(self.anzahl_zellen[self.gewaehlter_ausgang])+' Zellen)"\n'
        gpst +=  'set ytics nomirror;\n'

        gpst += 'set y2range [*:*];\n'
        gpst += 'set y2label "Innerer Widerstand Ri (mOhm)";\n'
        gpst += 'set y2tics border;\n'

        if self.anzahl_zellen[self.gewaehlter_ausgang] == 0: #e.g on restarts + anz-zellen >=50 (errorstuff)
            gpst +=  'set yrange [*:*];\n'
            divisor = "1"
        else:
            gpst +=  'set yrange [600:1700];\n'
            divisor = str(self.anzahl_zellen[self.gewaehlter_ausgang])

        gpst += 'plot wfile using 2:($3/'+divisor+') with lines title "mVolt" lw 2 lc rgbcolor "#ff0000", \
                    wfile using 2:7 with lines title "mOhm" axes x1y2 lw 1 lc rgbcolor "#000044";'
        return gpst

    def get_balancer_range(self, f):
        bmin = 0
        bmax = 0
        for  l in f.readlines():
            if l[0] == "#":
                continue

            line_a = l.split("\xff")
            avg = 0
            div = 0.0
            for i in range(18, len(line_a) - 1): #average
                avg += long(line_a[i])
                div += 1
            avg /= float(div)

            index=17
            for val in line_a[18:-1]: # get min and max
                index += 1
                if (long(val) - avg) < bmin:
                    bmin = long(val) - avg
                elif (long(val) - avg) > bmax:
                    bmax = long(val) - avg

            if abs(bmin) > bmax: # get hicher of limits
                rangeval = abs(bmin)
            else:
                rangeval = bmax

            if rangeval < 12:  # set range-limit minimum to 12   
                rangeval = 12
        return rangeval

    def gnuplot(self):
        """Create charts"""

        g = Gnuplot.Gnuplot(debug=0)

        qiv_files = ""
        dirList=os.listdir(self.tmp_dir)
        dirList.sort()
        print "*********************************************************************"
        print "****                       (Gnu-)Plotting                        ****"
        print "****                                                             ****"
        for fname in dirList:
            if fname[0:4] == "Akku" and fname[4:6] == str(self.gewaehlter_ausgang) + "-" and fname [8:12] == ".dat":
                qiv_files += self.tmp_dir + "/" + fname[:-4] + ".png "

                f = self.open_file(self.tmp_dir + "/" + fname, "r")
                while True: #ignore other than real data lines
                    l = f.readline()
                    if l[0] != "#":
                        break
                f.close()
                line_a = l.split("\xff")
                phasenr = long(line_a[9])
                atyp = long(line_a[12])

                if atyp == 5 and len(line_a) > 19: #lipo -> Balancer graph TODO what when no balancer
                    f = self.open_file(self.tmp_dir + "/" + fname, "r")
                    rangeval = self.get_balancer_range(f)
                    f.close()

                #TODO better titel (phase)....
                if phasenr >= 1 and phasenr <= 5:
                    phase = "LADEN"
                    g('set yrange [0:*];')
                elif phasenr >= 7 and phasenr < 9:
                    phase = "ENTLADEN"
                    g('set yrange [*:0];')
                elif phasenr == 10:
                    phase = "PAUSE (Entladespannung erreicht)"
                    g('set yrange [*:*];')
                elif phasenr == 0:
                    phase = "STOP (Erhaltungladung)"
                    g('set yrange [*:*];')
                else:
                    phase = "Unbekannte Phase <"+str(phasenr)+"> (oder so)"
                    g('set yrange [*:*];')



                # does not really work so far...{{{
                ##################################################
                #dummy plot for enhancing balance skale if needed.
                ##################################################
                #if atyp == 5 and len(line_a) > 18: #lipo -> Balancer graph TODO what when no balancer
                    #g('wfile="' + self.exe_dir + "/" + fname + '";')
                    #g('set xdata time;')
                    #g("set datafile separator '\xff';")
                    #g('set timefmt "%H:%M:%S";')

                    #g('set terminal unknown;')

                    #gpst = "plot "
                    #avg_string = "("
                    #x = 0
                    #for i in range(18, len(line_a) - 1):
                        #avg_string += "$"+str(i+1)+"+"
                        #x += 1
                    #avg_string = avg_string[0:-1] + ")/" + str(x)

                    #for i in range(18, len(line_a) - 1):
                        #gpst += 'wfile using 2:($'+str(i+1)+'-'+ str(avg_string)+'),'
                    #gpst = gpst[:-1]+';'


                    #g(gpst)
                    #print gpst
                    #g('bmin=GPVAL_DATA_Y_MIN;')
                    #g('bmax=GPVAL_DATA_Y_MAX;')

                ##################################################}}}
                g('set terminal png size 1280, 1024;')
                g('set output "' + self.tmp_dir + "/" + fname[:-4] + '.png"')

                g('set title "Akkumatik (Stefan Estner)";')
                g('set xdata time;')
                g("set datafile separator '\xff';")
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


                g('wfile="' + self.tmp_dir + "/" + fname + '";')
                g('set title "' + phase + ' (' + fname + ')";')


                g('plot \
                    wfile using 2:4 with lines title "mA" lw 2 lc rgbcolor "#009900" , \
                    wfile using 2:5 smooth bezier with lines title "mAh" lw 2 lc rgbcolor "#0000ff", \
                    wfile using 2:8 smooth bezier with lines title "Bat C" axes x1y2 lc rgbcolor "#cc0000" , \
                    wfile using 2:18 smooth bezier with lines title "KK C" axes x1y2 lc rgbcolor "#222222";')


                g('set nolabel;')
                g('set notitle;')

                g('set size 1.0,0.45;')
                g('set origin 0.0,0.0;')

                if atyp == 5 and len(line_a) > 19: #lipo -> Balancer graph TODO what when no balancer
                    g(self.lipo_gnuplot(line_a, rangeval))
                elif atyp == 0 or atyp == 1:
                    g(self.nixx_gnuplot())
                else:
                    g(self.else_gnuplot())

                g('set nomultiplot;')
                g('reset')
                print "**** Generated: "+"%44s"%(self.tmp_dir + "/" +fname[-27:-4])+".png ****"
            else:
                continue

        time.sleep(1.8) #sonst finded qiv (noch) nichts allenfalls
        args = shlex.split(qiv_files)
        arguments = ' '.join(str(n) for n in args)
        thread.start_new_thread(os.system,(self.picture_exe+' '+arguments,))


##########################################}}}
#File handling stuff {{{
##########################################

    def open_file(self, file_name, mode):
        """Open a file."""
        try:
            the_file = open(file_name, mode)
        except(IOError), e:
            print "Unable to open the file", file_name, "Ending program.\n", e
            raw_input("\n\nPress the enter key to exit.")
            sys.exit()
        else:
            return the_file


    def filesplit(self, fh):
        """Create files for gnuplot"""
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

        print "*********************************************************************"
        print "****                       Serial-Splitting                      ****"
        print "****                                                             ****"

        for file in os.listdir(self.tmp_dir):
            if len(file) == 12 and file[0:4] == "Akku":
                os.remove(self.tmp_dir + "/" + file)

        self.file_block = True #stop getting more serial data
        self.f.close()
        self.f = self.open_file(self.tmp_dir + '/serial-akkumatik.dat', 'r')
        for line in self.f.readlines():
            if self.file_block == True:
                self.f.close()
                self.f = self.open_file(self.tmp_dir + '/serial-akkumatik.dat', 'a') #reopen
                self.file_block = False #allow further getting serial adding..

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

            #TODO fails when there is some command ackknowledge string...
            if line[0:1] == "1":

                current_time1 = long(line[2:4]) * 60 + long(line[5:7]) * 60 + long(line[8:10]) #in seconds

                if previous_time1 == current_time1:  #duplicate time -> ignore (so far)
                    #print ("FILTER OUT: Duplicate Time. Line [ " + str(file_line) + "] ")
                    continue

                previous_line1 = line

                line_counter1 += 1

                if current_time1 < previous_time1:
                    fname = self.tmp_dir + '/Akku1-'+ "%02i" % (file_zaehler1)+'.dat'
                    fh1 = self.open_file(fname, "w+")
                    fh1.write(ausgang1_part)
                    fh1.close()
                    print "**** Generated: " + "%48s" % (fname[-47:]) + " ****"
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
                    fname = self.tmp_dir + '/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
                    fh2 = self.open_file(fname, "w+")
                    fh2.write(ausgang2_part)
                    fh2.close()
                    print "**** Generated: " + "%48s" % (fname[-47:]) + " ****"
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
            fname = self.tmp_dir + '/Akku1-'+ "%02i" % (file_zaehler1)+'.dat'
            fh1 = self.open_file(fname, "w+")
            fh1.write(ausgang1_part)
            fh1.close()
            print "**** Generated: " + "%28s" % (fname[-27:]) + " ****"
        if len(ausgang2_part) > 0:
            fname = self.tmp_dir + '/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
            fh2 = self.open_file(fname, "w+")
            fh2.write(ausgang2_part)
            print "**** Generated: " + "%28s" % (fname[-27:]) + " ****"

##########################################}}}
#Serial + output stuff{{{
##########################################

    def output_data(self, output_tty, output):
        #terminal output
        sys.stdout.write (output_tty)
        sys.stdout.flush()

        #graphical output
        self.label.set_markup('<span foreground="#333333">'+ output + '</span>')
        while gtk.events_pending():
            gtk.main_iteration()

    def akkumatik_command(self, hex_string):
        checksum = 2
        for x in hex_string:
            checksum ^= int("3"+x, 16)

        checksum ^= 64 #dummy checksum byte itself to checksum...
        self.ser.write(chr(2) + hex_string + chr(checksum) + chr(3))
        #print(chr(2) + string + chr(checksum) + chr(3))


    def read_line(self):
        """Read serial data (called via interval via gobject.timeout_add)"""

        if self.file_block == True:
            print "********************** Blocked serial input adding"
            return True

        lin = self.ser.readline()

        self.f.write(lin)

        daten = lin.split('\xff')

        #TODO print some 'command is OK' thing when is is akkmatiks' acknowledge thing

        if len(daten) < 18:
            return True #ignore (defective?) line

        #-1:0 - remove potential command return thing
        if (daten[-1:] == "1" and self.gewaehlter_ausgang == 1) \
                or (daten[-1:] == "2" and self.gewaehlter_ausgang == 2):
            ausgang = str(long(daten[-1:])) #Ausgang
            zeit = daten[1] #Stunden Minuten Sekunden
            ladeV = long(daten[2])/1000.0 #Akkuspannung mV
            ladeV = "%6.3fV" % (ladeV) #format into string
            ampere = long(daten[3]) #Strom A
            if ampere >= 1000 or ampere <= -1000:
                ampere = "%+.2fA" % (ampere/1000.0)
            else:
                ampere = "%imA" % (ampere)

            Ah = long(daten[4])/1000.0 #Ladungsmenge Ah
            VersU = long(daten[5]) #Versorungsspannung mV
            RimOhm = long(daten[6]) #akku-unnen mOhm
            cBat = long(daten[7]) #Akkutemperatur
            tmp_zellen = long(daten[8]) #Zellenzahl / bei Stop -> 'Fehlercode'
            if tmp_zellen < 50:
                self.anzahl_zellen[long(ausgang)] = tmp_zellen

            phase = long(daten[9]) #Ladephase 0-stop ...
            zyklus = long(daten[10]) #Zyklus
            sp = long(daten[11]) #Aktive Akkuspeicher
            atyp = self.AKKU_TYP[long(daten[12])] #Akkutyp
            prg = self.AMPROGRAMM[long(daten[13])] #Programm
            lart = self.LADEART[long(daten[14])] #Ladeart
            strohmw = self.STROMWAHL[long(daten[15])] #stromwahl
            stoppm = self.STOPPMETHODE[long(daten[16])] #stromwahl
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
                if tmp_zellen >= 54: # FEHLER
                    output_tty = self.FEHLERCODE[tmp_zellen - 50] + "\n\n"
                    output = self.FEHLERCODE[tmp_zellen - 50]
                    self.output_data(output_tty, output)
                    return True

                if tmp_zellen >= 50: #'gute' codes
                    phasedesc = "%-11s" % (self.FEHLERCODE[tmp_zellen - 50])
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
                phasedesc = " PAUSE    "
                ladeV = ""
            else:
                if phase >= 1 and phase <= 5:
                    c = "L"
                elif phase >=7 and phase <= 9:
                    c = "E"
                    phase = "-"

                phasedesc = atyp[0:1] + c + str(phase)

            #terminal print
            output_tty ="[Ausgang %s] [Phase/Zyklus: %s/%i] [%s] [%s] [%.3fAh] [Ri: %imOhm] [%s]\n" % (self.gewaehlter_ausgang, phasedesc, zyklus, ladeV, ampere, Ah, RimOhm, zeit)
            output_tty += "[Programm: %s] [Ladeart %s] [Stromwahl: %s] [Stoppmethode %s]\n" % (prg, lart, strohmw, stoppm)
            output_tty += "[%i°(Batterie)] [%i°(Kuehlkoerper)] [%i x %s][Akkuspeicher: %i]\n" % (cBat, cKK, self.anzahl_zellen[long(self.gewaehlter_ausgang)], atyp, sp)
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
            if len(daten) > 19:
                RimOhm = "∆%2imV " % (balance_delta)

            output ="%s%s %s %s|%s %2i°B \n%-7s   %+6.3fAh|%ix%s %2i°K" % (ausgang, phasedesc, ladeV, zeit, RimOhm, cBat, ampere, Ah, self.anzahl_zellen[self.gewaehlter_ausgang], atyp, cKK)

            self.output_data(output_tty, output)

        return True

##########################################}}}
#main {{{
##########################################

    def main(self):
        gtk.main()

##########################################}}}
#INIT{{{
##########################################

    def __init__(self):

        ##########################################
        #Konstanten
        self.AKKU_TYP = ["NiCd", "NiMH", "Blei", "Bgel", "LiIo", "LiPo", "LiFe", "Uixx"]
        self.AMPROGRAMM = ["Lade", "Entladen", "E+L", "L+E", "(L)E+L", "(E)L+E", "Sender"]
        self.LADEART = ["Konst", "Puls", "Reflex"]
        self.STROMWAHL = ["Auto", "Limit", "Fest", "Ext. Wiederstand"]
        self.STOPPMETHODE = ["Lademenge", "Gradient", "Delta-Peak-1", "Delta-Peak-2", "Delta-Peak-3"]
        self.FEHLERCODE = [ "Akku Stop", "Akku Voll", "Akku Leer", "", "Fehler Timeout", "Fehler Lade-Menge", "Fehler Akku zu Heiss", "Fehler Versorgungsspannung", "Fehler Akkuspannung,", "Fehler Zellenspannung,", "Fehler Alarmeingang", "Fehler Stromregler", "Fehler Polung/Kurzschluss", "Fehler Regelfenster", "Fehler Messfenster", "Fehler Temperatur", "Fehler Tempsens", "Fehler Hardware"]
        self.LIPORGB = ["3399ff", "55ff00", "ff9922", "3311cc", "123456", "ff0000", "3388cc", "cc8833", "88cc33", "ffff00", "ff00ff", "00ffff"]

        ##########################################}}}
        #Class Variablen
        self.file_block = False
        self.anzahl_zellen = [0,0,0] # defautls to 0 (on restarts + errorcode (>=50) = no plotting limits
        self.gewaehlter_ausgang = 1
        self.exe_dir = sys.path[0]
        self.tmp_dir = tempfile.gettempdir() + "/remote-akkumatik"
        if not os.path.isdir(self.tmp_dir):
            os.mkdir(self.tmp_dir)

        self.picture_exe = '/usr/local/bin/qiv'

        ##########################################}}}
        #GTK Stuff
        def delete_event(widget, event, data=None):
            return False

        def destroy(widget, data=None):
            gtk.main_quit()

        def buttoncb (widget, data=None):
            if data == "Chart":
                self.filesplit(self.f)
                self.gnuplot()

            elif data == "Exit":
                gtk.main_quit()

            elif data == "Ausg":
                if self.gewaehlter_ausgang == 1: #toggle ausgang
                    self.gewaehlter_ausgang = 2
                else:
                    self.gewaehlter_ausgang = 1
            elif data == "Start":
                if self.gewaehlter_ausgang == 1: #toggle ausgang
                    self.akkumatik_command("44")
                else:
                    self.akkumatik_command("48")

            elif data == "Stop":
                if self.gewaehlter_ausgang == 1: #toggle ausgang
                    self.akkumatik_command("41")
                else:
                    self.akkumatik_command("42")

            elif data == "Akku_Settings":

                    #hex_str = "31"          #Kommando       //  0    1    2  ......
                    #hex_str += "00"         #u08 Akkutyp    // NICD, NIMH, BLEI, BGEL, Li36, Li37, LiFe, IUxx
                    #hex_str += "04"         #u08 program    // LADE, ENTL, E+L, L+E, (L)E+L, (E)L+E, SENDER
                    #hex_str += "02"         #u08 lade_mode  // KONST, PULS, REFLEX
                    #hex_str += "00"         #u08 strom_mode // AUTO, LIMIT, FEST, EXT-W
                    #hex_str += "04"         #u08 stop_mode  // LADEMENGE, GRADIENT, DELTA-PK-1, DELTA-PK-2, DELTA-PK-3
                    #hex_str += "0800" #0008 #u16 zellenzahl // 0...n (abhaengig von Akkutyp und Ausgang)
                    ##hex_str += "a406" #06a4 -> 1700  #u16 capacity   // [mAh] max. FFFFh
                    #hex_str += "0807" #0708 -> 1800  #u16 capacity   // [mAh] max. FFFFh
                    #hex_str += "0000"       #u16 i_lade     // [mA] max. 8000 bzw. 2600
                    #hex_str += "0000"       #u16 i_entl     // [mA] max. 5000
                    #hex_str += "0000"       #u16 menge      // [mAh] max. FFFFh
                    #hex_str += "0300" #(3)  #u16 zyklenzahl // 0...9

                    #self.akkumatik_command(hex_str)
                self.dialog = gtk.Dialog("Akkumatik Settings Ausgang "\
                        + str(self.gewaehlter_ausgang), self.window,\
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,\
                        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

                label = gtk.Label("Batteie Typ")
                self.dialog.vbox.pack_start(label, True, True, 0)
                label.show()

                combobox = gtk.combo_box_new_text()
                combobox.append_text("NiCa")
                combobox.prepend_text("NiMh")
                combobox.insert_text(1, "LiPo")
                combobox.show()

                self.dialog.vbox.pack_start(combobox, True, True, 0)

                self.dialog.run()
                self.dialog.destroy()

                #self.dialog.show()

        def draw_pixbuf(widget, event):
            path = self.exe_dir + '/bilder/Display.jpg'
            pixbuf = gtk.gdk.pixbuf_new_from_file(path)
            widget.window.draw_pixbuf(widget.style.bg_gc[gtk.STATE_NORMAL], pixbuf, 0, 0, 0,0)

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title('Akkumatic Remote Display')
        self.window.set_size_request(872,168)
        self.window.set_default_size(872,168)
        self.window.set_position(gtk.WIN_POS_CENTER)

        self.window.connect("delete_event", delete_event)
        self.window.connect("destroy", destroy)
        self.window.set_border_width(10)

        # overall hbox
        hbox = gtk.HBox()
        self.window.add(hbox)
        hbox.connect('expose-event', draw_pixbuf)

        # akkumatik display label
        label = gtk.Label()
        label.modify_font(pango.FontDescription("mono 22"))

        hbox.pack_start(label, False, False, 50)
        
        #vbox for buttons
        vbox = gtk.VBox()
        hbox.pack_end(vbox, False, False, 0)

        #label_ausgang = gtk.Label("<1 Ausgang 2> "+str(self.gewaehlter_ausgang))
        #vbox.pack_start(label_ausgang, False, True, 0)

        # hbox for radios
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False, False, 0)

        # TODO nicht wirklich toll diese Radios
        r1button = gtk.RadioButton(None, None)
        r1button.connect("toggled", buttoncb , "Ausg")
        hbox.pack_start(r1button, True, True, 0)

        label_ausgang = gtk.Label("1 - 2")
        hbox.pack_start(label_ausgang, True, True, 0)

        r2button = gtk.RadioButton(r1button, None)
        hbox.pack_start(r2button, True, True, 0)

        if self.gewaehlter_ausgang == 1:
            r1button.set_active(True)
        else:
            r2button.set_active(True)
        
        #hbox fuer 'start/stop'
        hbox = gtk.HBox()
        vbox.pack_start(hbox, True, True, 0)

        button = gtk.Button("Start")
        button.connect("clicked", buttoncb, "Start")
        hbox.pack_start(button, False, True, 0)

        button = gtk.Button("Stop")
        button.connect("clicked", buttoncb, "Stop")
        hbox.pack_end(button, False, True, 0)


        button = gtk.Button("Chart")
        button.connect("clicked", buttoncb, "Chart")
        vbox.pack_start(button, False, True, 0)

        button = gtk.Button("Exit")
        button.connect("clicked", buttoncb, "Exit")
        vbox.pack_end(button, False, True, 0)

        button = gtk.Button("Akku Para")
        button.connect("clicked", buttoncb, "Akku_Settings")
        vbox.pack_end(button, False, True, 0)

        ##########################################}}}
        #Serial
        self.ser = serial.Serial(
            port='/dev/ttyS0',
            baudrate = 9600,
            parity = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            dsrdtr = True,
            rtscts = False,
            timeout = 0.1, #some tuning around with that value possibly
            interCharTimeout = None)


        self.ser.open()
        self.ser.isOpen()

        if len(sys.argv) > 1 and (sys.argv[1] == "-c" or sys.argv[1] == "-C"):
            self.f = self.open_file(self.tmp_dir + '/serial-akkumatik.dat', 'a')
            print "CONTINUE: Appending to file"
        elif len(sys.argv) > 1 and (sys.argv[1] == "-n" or sys.argv[1] == "-N"):
            self.f = self.open_file(self.tmp_dir + '/serial-akkumatik.dat', 'w+')
        else:
            raw_input("Press key to continue with *new* data-collecting (else Ctrl-D)")
            time.sleep(0.5)
            self.f = self.open_file(self.tmp_dir + '/serial-akkumatik.dat', 'w+')

        self.window.show_all() # after file-open (what is needed on plotting)...

        #finally begin collecting
        gobject.timeout_add(400, self.read_line) # some tuning around with that value possibly

if __name__ == '__main__':
    displ = akkumatik_display()
    displ.main()
#}}}
