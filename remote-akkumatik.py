#!/usr/bin/env python
# coding=utf-8

import os
import sys
import errno

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
import platform

import matplotlib.pyplot as plt


class akkumatik_display:
##########################################}}}
#Divers stuff{{{
##########################################

    def get_pos_hex(self, string, konst_arr):

        position = konst_arr.index(string)
        string = "%02x" % (position)
        #Well, just return %02i would work too on values <10 what is 'always' the case
        final_str = ""
        for c in string:
            final_str += chr(int("30", 16) + int(c, 16))
        return final_str

    def get_16bit_hex(self, integer):
        #integer to hex
        string = "%04x" % (integer)
        #switch around hi and low byte
        string = string[2:] + string[0:2]
        # add 0x30 (48) to those hex-digits and add that finally to the string
        final_str = ""
        for c in string:
            final_str += chr(int("30", 16) + int(c, 16))
        return final_str

    def command_thread(self, tname, com_str):
        self.threadlock.acquire() #TODO make it how it *should be* instead of that here...

        if self.command_abort == True: #skip on further soon to arrive commands
            self.threadlock.release()
            return

        self.command_wait = True
        self.ser.write(com_str)
        try:
            self.ser.write(com_str)
        except serial.SerialTimeoutException, e:
            print "%s", e

        ok = False
        i=0
        while i < 10:
            time.sleep(0.2)
            i += 1
            if self.command_wait == False: #put on True before sending. - here waiting for False
                ok = True
                break

        if ok == False:
            print "\n* [Kommando] *******************************************"
            print "Kommando <%s> kam *nicht* an" % (com_str)
            self.command_abort = True #skip on further soon to arrive commands
        self.threadlock.release()

    def akkumatik_command(self, string):

        checksum = 2
        for x in string:
            checksum ^= ord(x)

        checksum ^= 64 #dummy checksum byte itself to checksum...

        #try:
        thread.start_new_thread(self.command_thread, ("Issue_Command", chr(2) + string + chr(checksum) + chr(3)))
        #except:
        #    print "Error: unable to start thread"

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
        """NiCd and NiMH gnuplot 2nd chart"""

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
            gpst +=  'set yrange [600:1899];\n'
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
        print "\n* [Gnu-Plotting] ****************************************************"
        for fname in dirList:
            if fname[0:4] == "Akku" and fname[4:6] == str(self.gewaehlter_ausgang) + "-" and fname [8:12] == ".dat":
                qiv_files += self.chart_dir + "/" + fname[:-4] + ".png "

                f = self.open_file(self.tmp_dir + "/" + fname, "r")
                while True: #ignore other than real data lines
                    l = f.readline()
                    if l[0] != "#":
                        break
                f.close()
                if platform.system() == "Windows":
                    line_a = l.split(" ")
                else:
                    line_a = l.split("\xff")

                phasenr = long(line_a[9])
                atyp = long(line_a[12])

                #titel stuff
                atyp_str = self.AKKU_TYP[long(line_a[12])] #Akkutyp
                prg = self.AMPROGRAMM[long(line_a[13])] #Programm
                lart = self.LADEART[long(line_a[14])] #Ladeart
                stromw = self.STROMWAHL[long(line_a[15])] #stromwahl
                stoppm = self.STOPPMETHODE[long(line_a[16])] #stromwahl
                #Stop >= 50?
                anz_zellen = long(line_a[8]) #Zellenzahl / bei Stop -> 'Fehlercode'
                if anz_zellen >= 40: # not really needed there in the title anyway.
                    anz_z_str = ""
                else:
                    anz_z_str = str(anz_zellen) + "x"

                titel_plus = " ["+anz_z_str+atyp_str+", "+prg+", "+lart+", "+stromw+", "+stoppm+"] - "
                titel_little = " ["+anz_z_str+atyp_str+"] - "

                if atyp == 5 and len(line_a) > 19: #lipo -> Balancer graph TODO what when no balancer?
                    f = self.open_file(self.tmp_dir + "/" + fname, "r")
                    rangeval = self.get_balancer_range(f)
                    f.close()

                if phasenr >= 1 and phasenr <= 5:
                    titel = "LADEN" + titel_plus
                    g('set yrange [0:*];')
                elif phasenr >= 7 and phasenr < 9:
                    titel = "ENTLADEN" + titel_little
                    g('set yrange [*:0];')
                elif phasenr == 10:
                    titel = "PAUSE - Entladespannung erreicht" + titel_little
                    g('set yrange [*:*];')
                elif phasenr == 0:
                    titel = "STOP (Erhaltungladung)" + titel_plus
                    g('set yrange [*:*];')
                else:
                    titel = "Unbekannte Phase <"+str(phasenr)+">" + titel_plus
                    g('set yrange [*:*];')

                g('set terminal png size 1280, 1024;')
                g('set output "' + self.chart_dir + "/" + fname[:-4] + '.png"')

                g('set xdata time;')

                if platform.system() == "Windows":
                    g("set datafile separator ' ';")
                else:
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
                g('set title "Akkumatik - ' + titel + ' (' + fname + ')";')


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
                print "Generated:  "+"%44s"%(self.chart_dir + "/" +fname[-27:-4])+".png"
            else:
                continue

        if platform.system() != "Windows": #on MS, it just created the pictures...
            if len(qiv_files) > 0:
                time.sleep(1.8) #sonst finded qiv (noch) nichts allenfalls
                args = shlex.split(qiv_files)
                arguments = ' '.join(str(n) for n in args)
                thread.start_new_thread(os.system,(self.picture_exe+' '+arguments,))

##########################################}}}
#Matplot stuff{{{
##########################################
    #def matplot(self):
        #plt.plot([1,2,3,4])
        #plt.ylabel('some numbers')
        #plt.show()

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

        print "\n* [Serial Splitting] ************************************************"

        for file in os.listdir(self.tmp_dir):
            if len(file) == 12 and file[0:4] == "Akku":
                os.remove(self.tmp_dir + "/" + file)

        self.file_block = True #stop getting more serial data
        self.f.close()

        if os.path.getsize(self.tmp_dir + '/serial-akkumatik.dat') < 10:
            self.f = self.open_file(self.tmp_dir + '/serial-akkumatik.dat', 'a') #reopen
            print "Not sufficient Serial Data avaiable"
            self.file_block = False
            return

        self.file_block = True #stop getting more serial data
        self.f = self.open_file(self.tmp_dir + '/serial-akkumatik.dat', 'r')

        for line in self.f.readlines():
            if self.file_block == True:
                self.f.close()
                self.f = self.open_file(self.tmp_dir + '/serial-akkumatik.dat', 'a') #reopen
                self.file_block = False #allow further getting serial adding..

            file_line += 1

            #filter out useless lines
            #could also check for last thing is a newline ... hm.
            #TODO: won't work when some spezial line got printed "^#..."

            if line[0:2] == "A1": #remove command-acknowledged string
                line = line [5:]

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
                    fname = self.tmp_dir + '/Akku1-'+ "%02i" % (file_zaehler1)+'.dat'
                    fh1 = self.open_file(fname, "w+")

                    if platform.system() == "Windows":
                        ausgang1_part = ausgang1_part.replace('\xff', " ")

                    fh1.write(ausgang1_part)
                    fh1.close()
                    print "Generated:  " + "%48s" % (fname[-47:])
                    file_zaehler1 += 1
                    ausgang1_part = line
                    line_counter1 = 0
                else:
                    ausgang1_part += line

                previous_time1 = current_time1

            elif line[0:1] == "2": #"2"

                current_time2 = long(line[2:4]) * 60 + long(line[5:7]) * 60 + long(line[8:10]) #in seconds

                if previous_time2 == current_time2:  #duplicate time -> ignore so far
                    #print ("FILTER OUT: Duplicate Time. Line [ " + str(file_line) + "] ")
                    continue

                previousline2 = line

                line_counter2 += 1
                if line[2:10] == "00:00:01" and line_counter2 > 1: #only write when did not just begun
                    fname = self.tmp_dir + '/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
                    fh2 = self.open_file(fname, "w+")

                    if platform.system() == "Windows":
                        ausgang2_part = ausgang2_part.replace('\xff', " ")

                    fh2.write(ausgang2_part)
                    fh2.close()
                    print "Generated:  " + "%48s" % (fname[-47:])
                    file_zaehler2 += 1
                    ausgang2_part = line
                    line_counter2 = 0
                else:
                    ausgang2_part += line

                previous_time2 = current_time2

            else:
                print "\n= [Spez Line...] ============================================================"
                print "SPEZ: " + line

        if len(ausgang1_part) > 0:
            fname = self.tmp_dir + '/Akku1-'+ "%02i" % (file_zaehler1)+'.dat'
            fh1 = self.open_file(fname, "w+")

            if platform.system() == "Windows":
                ausgang1_part = ausgang1_part.replace('\xff', " ")

            fh1.write(ausgang1_part)
            fh1.close()
            print "Generated: " + "%28s" % (fname[-27:])
        if len(ausgang2_part) > 0:
            fname = self.tmp_dir + '/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
            fh2 = self.open_file(fname, "w+")

            if platform.system() == "Windows":
                ausgang2_part = ausgang2_part.replace('\xff', " ")

            fh2.write(ausgang2_part)
            print "Generated: " + "%28s" % (fname[-27:])

##########################################}}}
#Serial + output stuff{{{
##########################################

    def output_data(self, output, output2):
        #terminal output
        #sys.stdout.write (output_tty)
        #sys.stdout.flush()

        #graphical output
        self.label.set_markup('<span foreground="#333333">'+ output + '</span>')
        self.label2.set_markup('<span foreground="#339933">'+ output2 + '</span>')
        while gtk.events_pending():
            gtk.main_iteration()


    def read_line(self):
        """Read serial data (called via interval via gobject.timeout_add)"""

        if self.file_block == True:
            print "* [Debug] ********************* Blocked serial input adding"
            return True

        lin = self.ser.readline()

        #TODO how about filter stuff out here already?
        #     would also fix some howto on serial splitting
        self.f.write(lin)

        daten = lin.split('\xff')


        if len(daten) < 18:
            return True #ignore (defective?) line

        if len(daten[0]) > 1:
            self.command_wait = False # Kommando kam an
            daten[0] = daten[0][-1:] #last digit only (Ausgang)

        #-1:0 - remove potential command return thing
        if (daten[0] == "1" and self.gewaehlter_ausgang == 1) \
                or (daten[0] == "2" and self.gewaehlter_ausgang == 2):
            ausgang = str(long(daten[0][-1:])) #Ausgang
            zeit = daten[1] #Stunden Minuten Sekunden
            ladeV = long(daten[2])/1000.0 #Akkuspannung mV
            ladeV = "%6.3fV" % (ladeV) #format into string
            ampere = long(daten[3]) #Strom A
            if ampere >= 1000 or ampere <= -1000:
                ampere = "%+.2fA" % (ampere/1000.0)
            else:
                ampere = "%imA" % (ampere)

            Ah = long(daten[4])/1000.0 #Ladungsmenge Ah
            VersU = long(daten[5])/1000.0 #Versorungsspannung mV
            RimOhm_BalDelta = long(daten[6]) #akku-unnen mOhm
            cBat = long(daten[7]) #Akkutemperatur
            tmp_zellen = long(daten[8]) #Zellenzahl / bei Stop -> 'Fehlercode'
            if tmp_zellen < 50:
                self.anzahl_zellen[long(ausgang)] = tmp_zellen

            phase = long(daten[9]) #Ladephase 0-stop ...
            if phase == 0:
                self.button_start.set_sensitive(True)
                self.button_stop.set_sensitive(False)
            else:
                if phase == 10: #Pause
                    self.button_start.set_sensitive(True)
                else:
                    self.button_start.set_sensitive(False)
                self.button_stop.set_sensitive(True)

            #TODO 'beim Formieren' also sonst immer 0? dann output2 anpassen
            zyklus = long(daten[10]) #Zyklus
            sp = long(daten[11]) #Aktive Akkuspeicher

            self.atyp[self.gewaehlter_ausgang] = long(daten[12]) #Akkutyp
            atyp = self.AKKU_TYP[long(daten[12])] #Akkutyp

            self.prg[self.gewaehlter_ausgang] = long(daten[13]) #Programm
            prg = self.AMPROGRAMM[long(daten[13])] #Programm

            self.lart[self.gewaehlter_ausgang] = long(daten[14]) #Ladeart
            lart = self.LADEART[long(daten[14])] #Ladeart

            self.stromw[self.gewaehlter_ausgang] = long(daten[15]) #stromwahl
            stromw = self.STROMWAHL[long(daten[15])] #stromwahl

            self.stoppm[self.gewaehlter_ausgang] = long(daten[16]) #stromwahl
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
                    output = self.FEHLERCODE[tmp_zellen - 50]
                    self.output_data(output, "")
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

            #< stunde dann Minunte:Sekunden, sonst Stunde:Minuten
            if zeit[0:2] == "00":
                zeit = zeit [3:]
            else:
                zeit = zeit [:-3]

            #label print
            RimOhm_BalDelta = "Ri:%03i" % (RimOhm_BalDelta)
            #TODO:  more elgegant...
            if len(daten) > 19:
                RimOhm_BalDelta = "∆%2imV " % (balance_delta)

            output ="%s%s %s %s\n%-7s   %+6.3fAh" % (ausgang, phasedesc, ladeV, zeit, ampere, Ah)

            output2 ="%ix%s %2i° %s Z:%1i/%i\n" % (self.anzahl_zellen[self.gewaehlter_ausgang], atyp, cBat, RimOhm_BalDelta, zyklus, self.zyklen[self.gewaehlter_ausgang])
            output2 +="%s %s %s %s\n" % (prg, lart, stromw, stoppm)
            output2 +="Kap:%imAh ILa:%imA IEn:%imA\n" % (self.kapazitaet[self.gewaehlter_ausgang], self.ladelimit[self.gewaehlter_ausgang], self.entladelimit[self.gewaehlter_ausgang])
            output2 +="Menge:%imAh VerU:%5.2fV %2i°KK\n" % (self.menge[self.gewaehlter_ausgang], VersU, cKK)

            self.output_data(output, output2)

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
        #Konstanten{{{
        self.AKKU_TYP = ["NiCd", "NiMH", "Blei", "Bgel", "LiIo", "LiPo", "LiFe", "Uixx"]
        self.AMPROGRAMM = ["Laden", "Entladen", "E+L", "L+E", "(L)E+L", "(E)L+E", "Sender"]
        self.LADEART = ["Konst", "Puls", "Reflex"]
        self.STROMWAHL = ["Auto", "Limit", "Fest", "Ext. Wiederstand"]
        self.STOPPMETHODE = ["Lademenge", "Gradient", "Delta-Peak-1", "Delta-Peak-2", "Delta-Peak-3"]
        self.FEHLERCODE = [ "Akku Stop", "Akku Voll", "Akku Leer", "", "Fehler Timeout", "Fehler Lade-Menge", "Fehler Akku zu Heiss", "Fehler Versorgungsspannung", "Fehler Akkuspannung", "Fehler Zellenspannung", "Fehler Alarmeingang", "Fehler Stromregler", "Fehler Polung/Kurzschluss", "Fehler Regelfenster", "Fehler Messfenster", "Fehler Temperatur", "Fehler Tempsens", "Fehler Hardware"]
        self.LIPORGB = ["3399ff", "55ff00", "ff9922", "3311cc", "123456", "ff0000", "3388cc", "cc8833", "88cc33", "ffff00", "ff00ff", "00ffff"]

        ##########################################
        #Class Variablen
        self.threadlock = thread.allocate_lock()
        self.file_block = False
        self.command_wait = False # threads are waiting when True on command acknowledge text
        self.command_abort = False #indicates missed commands - skip next ones
        self.anzahl_zellen = [0,0,0] # defautls to 0 (on restarts + errorcode (>=50) = no plotting limits

        #     Entweter laufenden programm (wobei das sendet ja erst nach start) oder
        #     halt unabhaengig die dialog dinger speichern
        #     Alternativ ok = starten! dann sollte das ganze synchronisiert sein...
        #
        #     ^^^^ (Was jetzt auch der Fal ist......)
        #
        # wird ueberschrieben vom laufenden programm
        self.atyp = [0,0,0]
        self.prg = [0,0,0]
        self.lart = [0,0,0]
        self.stromw = [0,0,0]
        self.stoppm = [0,0,0]
        # gespeichert vom dialog
        self.kapazitaet =  [0,0,0]
        self.ladelimit =  [0,0,0]
        self.entladelimit =  [0,0,0]
        self.menge =  [0,0,0]
        self.zyklen =  [0,0,0]

        self.gewaehlter_ausgang = 1
        self.exe_dir = sys.path[0]

        #Defaults
        self.picture_exe = '/usr/local/bin/qiv'
        self.serial_port = '/dev/ttyS0'
        self.tmp_dir = tempfile.gettempdir() + "/remote-akkumatik"
        self.chart_dir = self.tmp_dir

        if os.path.exists(self.exe_dir + "/config.txt"):
            fh = self.open_file(self.exe_dir + "/config.txt", "r")

            for line in fh.readlines():
                if len(line.strip()) < 5:
                    continue
                split = line.split("=", 1)
                if split[0].strip().lower()[0] == "#":
                    continue
                elif split[0].strip().lower() == "viewer":
                    self.picture_exe = split[1].strip().replace("\\","/") #windows hm...
                elif split[0].strip().lower() == "serial_port":
                    self.serial_port = split[1].strip()
                elif split[0].strip().lower() == "chart_path":
                    self.chart_dir = split[1].strip().replace("\\","/")
                elif split[0].strip().lower() == "tmp_path":
                    self.tmp_dir = split[1].strip().replace("\\","/")

        print "* [ Config ] ***********************************"
        print "Picture viewer: %s" % (self.picture_exe)
        print "Serial Port:    %s" % (self.serial_port)
        print "Chart Path:     %s" % (self.chart_dir)
        print "Tmp Path:       %s" % (self.tmp_dir)

        if not os.path.isdir(self.tmp_dir):
            try:
                os.mkdir(self.tmp_dir)
            except OSError, e: # Python >2.5
                if OSError.errno == errno.EEXIST:
                    pass
                else:
                    print "Unable to create [%s] directory" % self.tmp_dir, "Ending program.\n", e
                    raw_input("\n\nPress the enter key to exit.")
                    sys.exit()
        if not os.path.isdir(self.chart_dir):
            try:
                os.mkdir(self.chart_dir)
            except OSError, e: # Python >2.5
                if OSError.errno == errno.EEXIST:
                    pass
                else:
                    print "Unable to create [%s] directory" % self.chart_dir, "Ending program.\n", e
                    raw_input("\n\nPress the enter key to exit.")
                    sys.exit()

        #}}}
        ##########################################
        #GTK Stuff{{{
        def delete_event(widget, event, data=None):
            return False

        def destroy(widget, data=None):
            gtk.main_quit()

        def buttoncb (widget, data=None):
            if data == "Chart":
                self.filesplit(self.f)
                self.gnuplot()
                #self.matplot()

            elif data == "Exit":
                gtk.main_quit()

            elif data == "Ausg":
                if self.gewaehlter_ausgang == 1: #toggle ausgang
                    self.gewaehlter_ausgang = 2
                    self.button_start.set_sensitive(False)
                    self.button_stop.set_sensitive(False)
                else:
                    self.gewaehlter_ausgang = 1
                    self.button_start.set_sensitive(False)
                    self.button_stop.set_sensitive(False)
            elif data == "Start":
                self.command_abort = False #reset
                if self.gewaehlter_ausgang == 1: #toggle ausgang
                    self.akkumatik_command("44")
                else:
                    self.akkumatik_command("48")

            elif data == "Stop":
                self.command_abort = False #reset
                if self.gewaehlter_ausgang == 1: #toggle ausgang
                    self.akkumatik_command("41")
                else:
                    self.akkumatik_command("42")

            elif data == "Akku_Settings": #{{{

                self.dialog = gtk.Dialog("Akkumatik Settings Ausgang "\
                        + str(self.gewaehlter_ausgang), self.window,\
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
                self.dialog.add_button("Start Ausgang %i" % (self.gewaehlter_ausgang), -3)

                #hbox over the whole dialog
                hbox = gtk.HBox(False, 0)
                self.dialog.vbox.pack_start(hbox, True, True, 0)
                hbox.show()

                #frame 1 (vbox)
                frame = gtk.Frame(None)
                hbox.pack_start(frame, True, True, 0)

                vbox = gtk.VBox(False, 0)
                vbox.set_border_width(5)
                frame.add(vbox)
                frame.show()
                vbox.show()

                #stuff into frame (vbox)
                label = gtk.Label("Batterie Typ")
                vbox.pack_start(label, True, True, 0)
                label.show()
                cb_atyp = gtk.combo_box_new_text()
                for item in self.AKKU_TYP:
                    cb_atyp.append_text(item)
                cb_atyp.set_active(self.atyp[self.gewaehlter_ausgang])
                cb_atyp.show()
                vbox.pack_start(cb_atyp, True, True, 0)

                label = gtk.Label("Programm")
                vbox.pack_start(label, True, True, 0)
                label.show()
                cb_prog = gtk.combo_box_new_text()
                for item in self.AMPROGRAMM:
                    cb_prog.append_text(item)
                cb_prog.set_active(self.prg[self.gewaehlter_ausgang])
                cb_prog.show()
                vbox.pack_start(cb_prog, True, True, 0)

                label = gtk.Label("Ladeart")
                vbox.pack_start(label, True, True, 0)
                label.show()
                cb_lart = gtk.combo_box_new_text()
                for item in self.LADEART:
                    cb_lart.append_text(item)
                cb_lart.set_active(self.lart[self.gewaehlter_ausgang])
                cb_lart.show()
                vbox.pack_start(cb_lart, True, True, 0)

                label = gtk.Label("Stromwahl")
                vbox.pack_start(label, True, True, 0)
                label.show()
                cb_stromw = gtk.combo_box_new_text()
                for item in self.STROMWAHL:
                    cb_stromw.append_text(item)
                cb_stromw.set_active(self.stromw[self.gewaehlter_ausgang])
                cb_stromw.show()
                vbox.pack_start(cb_stromw, True, True, 0)

                label = gtk.Label("Stoppmethode")
                vbox.pack_start(label, True, True, 0)
                label.show()
                cb_stoppm = gtk.combo_box_new_text()
                for item in self.STOPPMETHODE:
                    cb_stoppm.append_text(item)
                cb_stoppm.set_active(self.stoppm[self.gewaehlter_ausgang])
                cb_stoppm.show()
                vbox.pack_start(cb_stoppm, True, True, 0)


                #frame 2 (vbox)
                frame = gtk.Frame(None)
                hbox.pack_start(frame, True, True, 0)

                vbox = gtk.VBox(False, 0)
                vbox.set_border_width(5)
                frame.add(vbox)
                frame.show()
                vbox.show()

                label = gtk.Label("Zellen Anzahl")
                vbox.pack_start(label, True, True, 0)
                label.show()
                adj = gtk.Adjustment(self.anzahl_zellen[self.gewaehlter_ausgang], 0, 30, 1, 1, 0.0)
                sp_anzzellen = gtk.SpinButton(adj, 0.0, 0)
                sp_anzzellen.set_wrap(False)
                sp_anzzellen.set_numeric(True)
                vbox.pack_start(sp_anzzellen, False, True, 0)
                sp_anzzellen.show()

                label = gtk.Label("Kapazität mAh")
                vbox.pack_start(label, True, True, 0)
                label.show()
                adj = gtk.Adjustment(self.kapazitaet[self.gewaehlter_ausgang], 0.0, 99999, 25, 25, 0.0)
                sp_kapazitaet = gtk.SpinButton(adj, 1.0, 0)
                sp_kapazitaet.set_wrap(False)
                sp_kapazitaet.set_numeric(True)
                #sp_kapazitaet.set_size_request(55, -1)
                vbox.pack_start(sp_kapazitaet, False, True, 0)
                sp_kapazitaet.show()

                label = gtk.Label("I-Laden mA")
                vbox.pack_start(label, True, True, 0)
                label.show()
                adj = gtk.Adjustment(self.ladelimit[self.gewaehlter_ausgang], 0.0, 9999, 25, 25, 0.0)
                sp_ladelimit = gtk.SpinButton(adj, 1.0, 0)
                sp_ladelimit.set_wrap(False)
                sp_ladelimit.set_numeric(True)
                vbox.pack_start(sp_ladelimit, False, True, 0)
                sp_ladelimit.show()

                label = gtk.Label("I-Entladen mA")
                vbox.pack_start(label, True, True, 0)
                label.show()
                adj = gtk.Adjustment(self.entladelimit[self.gewaehlter_ausgang], 0.0, 9999, 25, 25, 0.0)
                sp_entladelimit = gtk.SpinButton(adj, 1.0, 0)
                sp_entladelimit.set_wrap(False)
                sp_entladelimit.set_numeric(True)
                vbox.pack_start(sp_entladelimit, False, True, 0)
                sp_entladelimit.show()

                label = gtk.Label("Menge mAh")
                vbox.pack_start(label, True, True, 0)
                label.show()
                adj = gtk.Adjustment(self.menge[self.gewaehlter_ausgang], 0.0, 99999, 25, 25, 0.0)
                sp_menge = gtk.SpinButton(adj, 1.0, 0)
                sp_menge.set_wrap(False)
                sp_menge.set_numeric(True)
                vbox.pack_start(sp_menge, False, True, 0)
                sp_menge.show()

                label = gtk.Label("Zyklen")
                vbox.pack_start(label, True, True, 0)
                label.show()
                adj = gtk.Adjustment(self.zyklen[self.gewaehlter_ausgang], 1, 10, 1, 1, 0.0)
                sp_zyklen = gtk.SpinButton(adj, 0.0, 0)
                sp_zyklen.set_wrap(False)
                sp_zyklen.set_numeric(True)
                vbox.pack_start(sp_zyklen, False, True, 0)
                sp_zyklen.show()

                # run the dialog
                retval = self.dialog.run()
                self.dialog.destroy()

                if retval == -3: #OK got pressed
                    hex_str = str(30 + self.gewaehlter_ausgang) #kommando 31 or 32
                    hex_str += self.get_pos_hex(cb_atyp.get_active_text(),self.AKKU_TYP)
                    hex_str += self.get_pos_hex(cb_prog.get_active_text(),self.AMPROGRAMM)
                    hex_str += self.get_pos_hex(cb_lart.get_active_text(),self.LADEART)
                    hex_str += self.get_pos_hex(cb_stromw.get_active_text(),self.STROMWAHL)
                    hex_str += self.get_pos_hex(cb_stoppm.get_active_text(),self.STOPPMETHODE)

                    hex_str += self.get_16bit_hex(int(sp_anzzellen.get_value()))
                    hex_str += self.get_16bit_hex(int(sp_kapazitaet.get_value()))
                    hex_str += self.get_16bit_hex(int(sp_ladelimit.get_value()))
                    hex_str += self.get_16bit_hex(int(sp_entladelimit.get_value()))
                    hex_str += self.get_16bit_hex(int(sp_menge.get_value()))
                    hex_str += self.get_16bit_hex(int(sp_zyklen.get_value()))

                    self.kapazitaet[self.gewaehlter_ausgang] = int(sp_kapazitaet.get_value())
                    self.ladelimit[self.gewaehlter_ausgang] = int(sp_ladelimit.get_value())
                    self.entladelimit[self.gewaehlter_ausgang] = int(sp_entladelimit.get_value())
                    self.menge[self.gewaehlter_ausgang] = int(sp_menge.get_value())
                    self.zyklen[self.gewaehlter_ausgang] = int(sp_zyklen.get_value())

                    #Kommando       //  0    1    2  ......
                    #u08 Akkutyp    // NICD, NIMH, BLEI, BGEL, Li36, Li37, LiFe, IUxx
                    #u08 program    // LADE, ENTL, E+L, L+E, (L)E+L, (E)L+E, SENDER
                    #u08 lade_mode  // KONST, PULS, REFLEX
                    #u08 strom_mode // AUTO, LIMIT, FEST, EXT-W
                    #u08 stop_mode  // LADEMENGE, GRADIENT, DELTA-PK-1, DELTA-PK-2, DELTA-PK-3
                    #u16 zellenzahl // 0...n (abhaengig von Akkutyp und Ausgang)
                    #u16 capacity   // [mAh] max. FFFFh
                    #u16 i_lade     // [mA] max. 8000 bzw. 2600
                    #u16 i_entl     // [mA] max. 5000
                    #u16 menge      // [mAh] max. FFFFh
                    #u16 zyklenzahl // 0...9

                    self.command_abort = False #reset

                    #if self.gewaehlter_ausgang == 1: #toggle ausgang
                        #self.akkumatik_command("41")
                    #else:
                        #self.akkumatik_command("42")

                    #time.sleep(0.6) #needs somehow, else the threads gets out of order possibly

                    self.akkumatik_command(hex_str)

                    time.sleep(0.6) #needs somehow, else the threads gets out of order possibly

                    if self.gewaehlter_ausgang == 1: #toggle ausgang
                        self.akkumatik_command("44")
                    else:
                        self.akkumatik_command("48")

        #}}}
        def draw_pixbuf(widget, event):
            path = self.exe_dir + '/bilder/Display.jpg'
            pixbuf = gtk.gdk.pixbuf_new_from_file(path)
            widget.window.draw_pixbuf(widget.style.bg_gc[gtk.STATE_NORMAL], pixbuf, 0, 0, 0,0)

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title('Akkumatic Remote Display')
        self.window.set_size_request(1006,168)
        self.window.set_default_size(1006,168)
        self.window.set_position(gtk.WIN_POS_CENTER)

        self.window.connect("delete_event", delete_event)
        self.window.connect("destroy", destroy)
        self.window.set_border_width(8)

        # overall hbox
        hbox = gtk.HBox()
        self.window.add(hbox)
        hbox.connect('expose-event', draw_pixbuf)

        # akkumatik display label
        self.label = gtk.Label()
        if platform.system() == "Windows": #TODO check once if that fits...
            self.label.modify_font(pango.FontDescription("mono 25"))
        else:
            self.label.modify_font(pango.FontDescription("mono 22"))

        gfixed = gtk.Fixed()
        gfixed.put(self.label, 48 , 35)

        hbox.pack_start(gfixed, False, False, 0)

        self.label2 = gtk.Label()
        if platform.system() == "Windows": #TODO check once if that fits...
            self.label2.modify_font(pango.FontDescription("mono 15"))
        else:
            self.label2.modify_font(pango.FontDescription("mono 12"))

        gfixed.put(self.label2, 440, 30)

        #vbox for buttons
        vbox = gtk.VBox()
        hbox.pack_end(vbox, False, False, 0)

        # hbox for radios
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False, False, 0)

        # TODO nicht wirklich toll diese Radios
        r1button = gtk.RadioButton(None, None)
        r1button.connect("toggled", buttoncb , "Ausg")
        hbox.pack_start(r1button, True, True, 0)

        label_ausgang = gtk.Label("1   2")
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

        self.button_start = gtk.Button("Start")
        self.button_start.connect("clicked", buttoncb, "Start")
        hbox.pack_start(self.button_start, False, True, 0)
        self.button_start.set_sensitive(False)

        self.button_stop = gtk.Button("Stop")
        self.button_stop.connect("clicked", buttoncb, "Stop")
        hbox.pack_end(self.button_stop, False, True, 0)
        self.button_stop.set_sensitive(False)

        vbox.pack_start(gtk.HSeparator(), False, True, 5)

        button = gtk.Button("Akku Para")
        button.connect("clicked", buttoncb, "Akku_Settings")
        vbox.pack_start(button, False, True, 0)

        button = gtk.Button("Chart")
        button.connect("clicked", buttoncb, "Chart")
        vbox.pack_start(button, False, True, 0)

        button = gtk.Button("Exit")
        button.set_size_request(98,20)
        button.connect("clicked", buttoncb, "Exit")
        vbox.pack_end(button, False, True, 0)

        vbox.pack_end(gtk.HSeparator(), False, True, 5)

        #}}}
        ##########################################
        #Serial{{{
        if platform.system() == "Windows":
            self.serial_port = '\\\\.\\' + self.serial_port #needen on comx>10 - seems to work

        self.ser = serial.Serial(
            port=self.serial_port,
            baudrate = 9600,
            parity = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout = 0.1, #some tuning around with that value possibly
            writeTimeout = 2.0)


        if platform.system() != "Windows":
            self.ser.open()

        self.ser.isOpen()

        if len(sys.argv) > 1 and (sys.argv[1] == "-c" or sys.argv[1] == "-C"):
            self.f = self.open_file(self.tmp_dir + '/serial-akkumatik.dat', 'a')
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
    if len(sys.argv) > 1 and (sys.argv[1] == "-h" or sys.argv[1] == "--help"):
        print """Usage:

    -c      Continue with collecting serial data
    -n      Begin from scratch
    -h      Print this."""
        sys.exit()

    displ = akkumatik_display()
    displ.main()
#}}}
