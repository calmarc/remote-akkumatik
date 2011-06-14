#!/usr/bin/env python
# coding=utf-8

#{{{imports
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

import cfg
#}}}

def command_thread(tname, com_str): #{{{

    cfg.threadlock.acquire() #TODO make it how it *should be* instead of that here...

    if cfg.command_abort == True: #skip on further soon to arrive commands
        cfg.threadlock.release()
        return

    cfg.command_wait = True
    try:
        #cfg.ser.setDTR(True)
        cfg.ser.write(com_str)
        #cfg.ser.setDTR(False) #TODO Testing... not really knowing what I do..
    except serial.SerialException, e:
        print "%s", e

    ok = False
    i=0
    sys.stdout.write("Waiting for Command Ack: ")
    sys.stdout.flush()
    while i < 60:
        time.sleep(0.1)
        sys.stdout.write(".")
        sys.stdout.flush()
        i += 1
        if cfg.command_wait == False: #put on True before sending. - here waiting for False
            sys.stdout.write(" OK\n")
            sys.stdout.flush()
            ok = True
            break

    if ok == False:
        sys.stdout.write(" Failed\n")
        sys.stdout.flush()
        cfg.command_abort = True #skip on further soon to arrive commands
    cfg.threadlock.release()

#}}}

def akkumatik_command(string): #{{{

    checksum = 2
    for x in string:
        checksum ^= ord(x)

    checksum ^= 64 #dummy checksum byte itself to checksum...

    #try:
    #thread.start_new_thread(command_thread, ("Issue_Command", chr(2) + string + chr(checksum) + chr(3), cfg.threadlock, cfg.ser))
    thread.start_new_thread(command_thread, ("Issue_Command", chr(2) + string + chr(checksum) + chr(3)))
    #except:
    #    print "Error: unable to start thread"

#}}}

##########################################
#GnuPlotting stuff{{{
##########################################

def lipo_gnuplot(line_a, rangeval, anz_z): #{{{

    """lipo gnuplot 2nd chart"""
    gpst = ""

    gpst += 'set nolabel;\n'
    gpst += 'set ytics nomirror;\n'
    gpst += 'set ylabel "mVolt Zellen (Avg)"\n'
    gpst += 'set yrange [2992:4208];\n'

    #gpst += 'set autoscale {y{|min|max|fixmin|fixmax|fix} | fix | keepfix}

    if rangeval != -1:
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
            gpst += ', wfile using 2:($'+str(i+1)+'-'+ str(avg_string)+') smooth bezier with lines title "∆ '+str(i-17)+'" axes x1y2 lw 1 lc rgbcolor "#'+cfg.LIPORGB[i-18]+'"'
        gpst += ';'
    else:
        string = 'mV (avg)'
        if anz_z == -1:
            gpst += 'set yrange [0:*];\n'
            gpst += 'set ylabel "mVolt Zellen"\n'
            anz_z = 1
            string = 'mVolt'

        gpst += 'plot wfile using 2:($3/'+str(anz_z)+') with lines title "'+string+'" lw 2 lc rgbcolor "#cc3333" '

    return (gpst)

#}}}

def else_gnuplot(): #{{{

    """other than lipo gnuplot 2nd chart"""

    gpst = ""

    gpst +=  'set ylabel "mVolt Pro Zelle (Avg. von '+str(cfg.anzahl_zellen[cfg.gewaehlter_ausgang])+' Zellen)"\n'
    gpst +=  'set yrange [*:*];\n'
    gpst +=  'set ytics nomirror;\n'

    #gpst += 'set y2range [*:*];\n'
    #gpst += 'set y2label "Innerer Widerstand Ri (mOhm)";\n'
    #gpst += 'set y2tics border;\n'

    gpst += 'plot wfile using 2:3 with lines title "mVolt" lw 2 lc rgbcolor "#ff0000";'
    return gpst

#}}}

def nixx_gnuplot(): #{{{

    """NiCd and NiMH gnuplot 2nd chart"""

    gpst = ""

    gpst +=  'set ylabel "mVolt Pro Zelle (Avg. von '+str(cfg.anzahl_zellen[cfg.gewaehlter_ausgang])+' Zellen)"\n'
    gpst +=  'set ytics nomirror;\n'

    gpst += 'set y2range [*:*];\n'
    gpst += 'set y2label "Innerer Widerstand Ri (mOhm)";\n'
    gpst += 'set y2tics border;\n'

    if cfg.anzahl_zellen[cfg.gewaehlter_ausgang] == 0: #e.g on restarts + anz-zellen >=50 (errorstuff)
        gpst +=  'set yrange [*:*];\n'
        divisor = "1"
    else:
        gpst +=  'set yrange [600:1899];\n'
        divisor = str(cfg.anzahl_zellen[cfg.gewaehlter_ausgang])

    gpst += 'plot wfile using 2:($3/'+divisor+') with lines title "mVolt" lw 2 lc rgbcolor "#ff0000", \
                wfile using 2:7 with lines title "mOhm" axes x1y2 lw 1 lc rgbcolor "#000044";'
    return gpst

#}}}

def get_balancer_range(f): #{{{

    bmin = 0
    bmax = 0
    rangeval = 0
    for  l in f.readlines():
        if l[0] == "#":
            continue

        line_a = l.split("\xff")
        avg = 0
        div = 0.0
        for i in range(18, len(line_a) - 1): #average
            avg += long(line_a[i])
            div += 1

        if div > 0.0:
            avg /= float(div)
        else:
            continue


        index=17
        for val in line_a[18:-1]: # get min and max
            index += 1
            if (long(val) - avg) < bmin:
                bmin = long(val) - avg
            elif (long(val) - avg) > bmax:
                bmax = long(val) - avg

        if abs(bmin) > bmax: # get higher of limits
            rangeval = abs(bmin)
        else:
            rangeval = bmax

    if rangeval < 12:  # set range-limit minimum to 12
        rangeval = 12
    return rangeval

#}}}

def gnuplot(): #{{{
    """Create charts"""

    g = Gnuplot.Gnuplot(debug=0)

    qiv_files = ""
    dirList=os.listdir(cfg.tmp_dir)
    dirList.sort()
    print "\n* [Gnu-Plotting] ****************************************************"
    for fname in dirList:
        if fname[0:4] == "Akku" and fname[4:6] == str(cfg.gewaehlter_ausgang) + "-" and fname [8:12] == ".dat":
            qiv_files += cfg.chart_dir + "/" + fname[:-4] + ".png "

            f = open_file(cfg.tmp_dir + "/" + fname, "r")
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
            atyp_i = long(line_a[12])

            #titel stuff
            atyp_str = cfg.AKKU_TYP[long(line_a[12])] #Akkutyp
            prg_str = cfg.AMPROGRAMM[long(line_a[13])] #Programm
            lart_str = cfg.LADEART[long(line_a[14])] #Ladeart
            stromw_str = cfg.STROMWAHL[long(line_a[15])] #stromwahl
            stoppm_str = cfg.STOPPMETHODE[long(line_a[16])] #stromwahl
            #Stop >= 50?
            anz_zellen = long(line_a[8]) #Zellenzahl / bei Stop -> 'Fehlercode'
            anz_z = anz_zellen
            if anz_zellen >= 40: # not really needed there in the title anyway.
                anz_z_str = ""
                anz_z = -1 #unknown
            else:
                anz_z_str = str(anz_zellen) + "x"

            titel_plus = " ["+anz_z_str+atyp_str+", "+prg_str+", "+lart_str+", "+stromw_str+", "+stoppm_str+"] - "
            titel_little = " ["+anz_z_str+atyp_str+"] - "

            rangeval = -1 # stays like that when no balancer attached
            if atyp_i == 5 and len(line_a) > 19: #lipo -> Balancer graph TODO what when no balancer?
                f = open_file(cfg.tmp_dir + "/" + fname, "r")
                rangeval = get_balancer_range(f)
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
            #gnuplot does not like MS-Windoof's \
            g('set output "' + (cfg.chart_dir).replace('\\','/') + "/" + fname[:-4] + '.png"')

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


            #gnuplot does not like MS-Windoof's \
            g('wfile="' + cfg.tmp_dir.replace('\\', '/') + "/" + fname + '";')
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

            if atyp_i == 5:
                g(lipo_gnuplot(line_a, rangeval, anz_z))
            elif atyp_i == 0 or atyp_i == 1:
                g(nixx_gnuplot())
            else:
                g(else_gnuplot())

            g('set nomultiplot;')
            g('reset')
            print "Generated:  "+"%44s"%(cfg.chart_dir + "/" +fname[-27:-4])+".png"
        else:
            continue

    if len(qiv_files) > 0:
        time.sleep(1.8) #sonst finded qiv (noch) nichts allenfalls
        args = shlex.split(qiv_files)
        arguments = ' '.join(str(n) for n in args)
        if platform.system() == "Windows":
            for x in args:
                # os.startfile(x)
                thread.start_new_thread(os.startfile,(x,))
                break #one is enough for eg. irfanview
        else:
            thread.start_new_thread(os.system,(cfg.picture_exe+' '+arguments,))

#}}}

##########################################}}}
#Matplot stuff{{{
##########################################
#def matplot():
    #plt.plot([1,2,3,4])
    #plt.ylabel('some numbers')
    #plt.show()

##########################################}}}
#File handling stuff {{{
##########################################

def open_file(file_name, mode): #{{{
    """Open a file."""

    try:
        the_file = open(file_name, mode)
    except(IOError), e:
        print "Unable to open the file", file_name, "Ending program.\n", e
        raw_input("\n\nPress the enter key to exit.")
        sys.exit()
    else:
        return the_file

#}}}

def filesplit(fh): #{{{
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

    for file in os.listdir(cfg.tmp_dir):
        if len(file) == 12 and file[0:4] == "Akku":
            os.remove(cfg.tmp_dir + "/" + file)

    cfg.file_block = True #stop getting more serial data
    cfg.fser.close()

    if os.path.getsize(cfg.tmp_dir + '/serial-akkumatik.dat') < 10:
        f = open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'ab') #reopen
        print "Not sufficient Serial Data avaiable"
        cfg.file_block = False
        return

    cfg.fser = open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'rb')

    for line in cfg.fser.readlines(): #get all lines in one step
        if cfg.file_block == True:
            cfg.fser.close()
            cfg.fser = open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'ab') #reopen
            cfg.file_block = False #allow further getting serial adding..

        if line[0:1] == "1":

            current_time1 = long(line[2:4]) * 60 + long(line[5:7]) * 60 + long(line[8:10]) #in seconds

            previous_line1 = line

            line_counter1 += 1

            if current_time1 < previous_time1:
                fname = cfg.tmp_dir + '/Akku1-'+ "%02i" % (file_zaehler1)+'.dat'
                fh1 = open_file(fname, "wb+")

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

            previousline2 = line

            line_counter2 += 1
            if line[2:10] == "00:00:01" and line_counter2 > 1: #only write when did not just begun
                fname = cfg.tmp_dir + '/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
                fh2 = open_file(fname, "wb+")

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
        fname = cfg.tmp_dir + '/Akku1-'+ "%02i" % (file_zaehler1)+'.dat'
        fh1 = open_file(fname, "wb+")

        if platform.system() == "Windows":
            ausgang1_part = ausgang1_part.replace('\xff', " ")

        fh1.write(ausgang1_part)
        fh1.close()
        print "Generated: " + "%28s" % (fname[-27:])
    if len(ausgang2_part) > 0:
        fname = cfg.tmp_dir + '/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
        fh2 = open_file(fname, "wb+")

        if platform.system() == "Windows":
            ausgang2_part = ausgang2_part.replace('\xff', " ")

        fh2.write(ausgang2_part)
        print "Generated: " + "%28s" % (fname[-27:])

#}}}

##########################################}}}
#Serial + output stuff{{{
##########################################

def output_data(output, label, output2, label2): #{{{

    label.set_markup('<span foreground="#444444">'+ output + '</span>')
    label2.set_markup('<span foreground="#339933">'+ output2 + '</span>')
    while gtk.events_pending():
        gtk.main_iteration()

#}}}

def read_line(args): #{{{
    """Read serial data (called via interval via gobject.timeout_add) and print it to display"""

    (label, label2) = args

    if cfg.file_block == True:
        print "* [Debug] ********************* Blocked serial input"
        return True

    try:
        lin = cfg.ser.readline()
    except serial.SerialException, e:
        print "%s" % e
        return True

    daten = lin.split('\xff')

    ################*################
    #Clean/check lines before writing or so

    yeswrite = True

    if lin[:1] == "#": #ignore all together for now
        return True

    #handle command-acknowledged string
    if len(daten[0]) > 1:
        while lin[0:2] == "A1": #more Ack.. can be there
            lin = lin[5:]
            daten[0] = daten[0][-1:] #last digit only (Ausgang) wird kaum gehen
            cfg.command_wait = False # Kommando kam an

    if len(daten[0]) <> 1: # something is not right..
        #print "komische dings oder?"
        #print lin
        return True

    if len(daten) < 19: #scrumbled or empty line
        return True

    curtime = lin[2:10]

    if curtime == "00:00:00": #not begun yet
        yeswrite = False

    if curtime == cfg.oldtime[int(daten[0])]:
        yeswrite = False

    #if lin[11:16] == "00000": #no volt lines
        #print ("FILTER OUT: Volt has Zero value")
        #return ""

    cfg.oldtime[int(daten[0])] = curtime

    try: 
        if yeswrite:
            cfg.fser.write(lin)
    except  ValueError, e:
        print "%s" % e
        print "Should not happen, but reopening file anyway"
        cfg.fser = open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'ab')
        return True


    if (daten[0] == "1" and cfg.gewaehlter_ausgang == 1) \
            or (daten[0] == "2" and cfg.gewaehlter_ausgang == 2):
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
            cfg.anzahl_zellen[long(ausgang)] = tmp_zellen

        phase = long(daten[9]) #Ladephase 0-stop ...
        if phase == 0:
            button_start.set_sensitive(True)
            button_stop.set_sensitive(False)
        else:
            if phase == 10: #Pause
                button_start.set_sensitive(True)
            else:
                button_start.set_sensitive(False)
            button_stop.set_sensitive(True)

        #TODO 'beim Formieren' also sonst immer 0? dann output2 anpassen
        zyklus = long(daten[10]) #Zyklus
        sp = long(daten[11]) #Aktive Akkuspeicher

        cfg.atyp[cfg.gewaehlter_ausgang] = int(daten[12]) #Akkutyp
        atyp_str = cfg.AKKU_TYP[long(daten[12])] #Akkutyp

        cfg.prg[cfg.gewaehlter_ausgang] = long(daten[13]) #Programm
        prg_str = cfg.AMPROGRAMM[long(daten[13])] #Programm

        try:
            cfg.lart[cfg.gewaehlter_ausgang] = long(daten[14]) #Ladeart
            lart_str = cfg.LADEART[long(daten[14])] #Ladeart
        except IndexError, e:
            print "%s" % e
            print "-> %i" % long(daten[14])
            time.sleep(10)
            sys.exit()

        cfg.stromw[cfg.gewaehlter_ausgang] = long(daten[15]) #stromwahl
        stromw_str = cfg.STROMWAHL[long(daten[15])] #stromwahl

        cfg.stoppm[cfg.gewaehlter_ausgang] = long(daten[16]) #stromwahl
        stoppm_str = cfg.STOPPMETHODE[long(daten[16])] #stromwahl

        cKK = long(daten[17]) #KK Celsius

        cellmV = ""
        tmp_a = []
        for cell in daten[18:-1]:
            cellmV += " " + cell + " "
            try:
                tmp_a.append(long(cell))
            except:
                print "00:00:00 to long error"
                print daten
                print "----------------------"

        balance_delta = -1
        if len(tmp_a) > 0:
            balance_delta = max(tmp_a) - min(tmp_a)

        if phase == 0: #dann 'Fehlercode' zwangsweise ...?
            if tmp_zellen >= 54: # FEHLER
                output = cfg.FEHLERCODE[tmp_zellen - 50]
                output_data(output, label, "", label2)
                return True

            if tmp_zellen >= 50: #'gute' codes
                phasedesc = "%-11s" % (cfg.FEHLERCODE[tmp_zellen - 50])
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

            phasedesc = atyp_str[0:1] + c + str(phase)

        #< stunde dann Minunte:Sekunden, sonst Stunde:Minuten
        if zeit[0:2] == "00":
            zeit = zeit [3:]
        else:
            zeit = zeit [:-3]

        #label print
        RimOhm_BalDelta = "Ri:%03i" % (RimOhm_BalDelta)
        #TODO:  more elgegant...
        if cfg.atyp[cfg.gewaehlter_ausgang] == 5: #LiPo
            if len(daten) > 19:
                RimOhm_BalDelta = "∆%2imV " % (balance_delta)
            else:
                RimOhm_BalDelta = "∆..mV "
            cfg.menge[cfg.gewaehlter_ausgang] = 0
            lart_str = "[LiPo]"
            stromw_str = "[LiPo]"
            stoppm_str = "[LiPo]"


        output ="%s%s %s %s\n%-7s   %+6.3fAh" % (ausgang, phasedesc, ladeV, zeit, ampere, Ah)

        zykll = str(cfg.zyklen[cfg.gewaehlter_ausgang])
        if zykll == "0":
            zykll = "-"

        output2 ="%ix%s %2i° %s Z:%1i/%s\n" % (cfg.anzahl_zellen[cfg.gewaehlter_ausgang], atyp_str, cBat, RimOhm_BalDelta, zyklus, zykll)
        output2 +="%s %s %s %s\n" % (prg_str, lart_str, stromw_str, stoppm_str)

        kapa = str(cfg.kapazitaet[cfg.gewaehlter_ausgang])
        llimit = str(cfg.ladelimit[cfg.gewaehlter_ausgang])
        entll = str( cfg.entladelimit[cfg.gewaehlter_ausgang])
        menge_str = str(cfg.menge[cfg.gewaehlter_ausgang])
        if kapa == "0":
            kapa = "-"
        if llimit == "0":
            llimit = "-"
        if entll == "0":
            entll = "-"
        if menge_str == "0":
            menge_str = "-"

        output2 +="Kap:%smAh ILa:%smA IEn:%smA\n" % (kapa , llimit, entll)
        output2 +="Menge:%smAh VerU:%5.2fV %2i°KK\n" % (menge_str, VersU, cKK)

        output_data(output, label, output2, label2)

    return True

#}}}

def serial_setup(): #{{{

    print "* [ Serial Port ] ***********************************"
    sys.stdout.write("Trying to open serial port '%s': " % cfg.serial_port)
    sys.stdout.flush()
    if platform.system() == "Windows":
        cfg.serial_port = '\\\\.\\' + cfg.serial_port #needen on comx>10 - seems to work

    try:
        cfg.ser = serial.Serial(
            port=cfg.serial_port,
            baudrate = 9600,
            parity = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            bytesize = serial.EIGHTBITS,
            xonxoff=0,
            rtscts=0,
            dsrdtr = False,
            timeout = 0.1, #some tuning around with that value possibly
            writeTimeout = 2.0)

        if platform.system() != "Windows":
            cfg.ser.open()

        cfg.ser.isOpen()

        sys.stdout.write("OK\n\n")
        sys.stdout.flush()

    except serial.SerialException, e:
        sys.stdout.write("Failed\n\n")
        sys.stdout.flush()
        print "Program abort: \"%s\"" % e
        time.sleep(3)
        sys.exit()

    return cfg.ser

#}}}

def serial_file_setup(): #{{{

    if len(sys.argv) > 1 and (sys.argv[1] == "-c" or sys.argv[1] == "-C"):
        f = open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'ab')
    elif len(sys.argv) > 1 and (sys.argv[1] == "-n" or sys.argv[1] == "-N"):
        f = open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'wb+')
    else:
        print "\n********************************************************"
        sys.stdout.write("New serial-collecting (3 seconds to abort (Ctrl-C)): ")
        sys.stdout.flush()
        time.sleep(1.0)
        for i in range(1,4):
            sys.stdout.write("..." + str(i))
            sys.stdout.flush()
            time.sleep(1.0)
        sys.stdout.write("\n\n")
        sys.stdout.flush()
        f = open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'wb+')

    return f

#}}}

##########################################}}}
# Akku Parameter Dialog{{{
##########################################

def akkupara_dialog(): #{{{

    def get_pos_hex(string, konst_arr):

        position = konst_arr.index(string)
        string = "%02x" % (position)
        #Well, just return %02i would work too on values <10 what is 'always' the case
        final_str = ""
        for c in string:
            final_str += chr(int("30", 16) + int(c, 16))
        return final_str

    def get_16bit_hex(integer):
        #integer to hex
        string = "%04x" % (integer)
        #switch around hi and low byte
        string = string[2:] + string[0:2]
        # add 0x30 (48) to those hex-digits and add that finally to the string
        final_str = ""
        for c in string:
            final_str += chr(int("30", 16) + int(c, 16))
        return final_str

    def save_akkulist():
        fh = open_file(cfg.exe_dir + "/liste_akkus.dat", "wb")
        for item in akkulist:
            line = ""
            for x in item:
                line += str(x)  + '\xff'
            line = line[:-1] # remove last xff
            line += "\n"
            fh.write(line)
        fh.close()

    def button_akku_cb(widget, para_dia, data=None):
        if data == "+":
            dialog = gtk.Dialog("Name Akkuparameter ",\
                    para_dia,\
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,\
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

            label = gtk.Label("Akkuparameter Name")
            dialog.vbox.pack_start(label, True, True, 8)
            label.show()

            tb = gtk.Entry()
            tb.set_max_length(20)
            tb.show()
            dialog.vbox.pack_start(tb, True, True, 8)

            # run the dialog
            retval = dialog.run()

            if retval == -3: #OK
                txt = tb.get_text()

                #check if there is that name already - possibly remove it then
                i = 0
                for item in akkulist:
                    if item[0] == txt:
                        akkulist.pop(i)
                        cb_akkulist.remove_text(i)
                        print 'Akkuparameter: "%s" wurden ueberschrieben' % txt
                        break
                    i += 1

                akkulist.append([txt, \
                        int(cb_atyp.get_active()),\
                        int(cb_prog.get_active()),\
                        int(cb_lart.get_active()),\
                        int(cb_stromw.get_active()),\
                        int(cb_stoppm.get_active()),\
                        int(sp_anzzellen.get_value()),\
                        int(sp_kapazitaet.get_value()),\
                        int(sp_ladelimit.get_value()),\
                        int(sp_entladelimit.get_value()),\
                        int(sp_menge.get_value()),\
                        int(sp_zyklen.get_value())])

                #sort on 'name'
                akkulist.sort(key = lambda x: x[0].lower())

                #find new item in new ordered list
                i=0
                for item in akkulist:
                    if item[0] == txt:
                        break
                    i += 1

                #append new just there into gtk-combo
                cb_akkulist.insert_text(i, txt)
                cb_akkulist.set_active(i)

            dialog.destroy()
            save_akkulist()

        elif data == "x":

            active_i = cb_akkulist.get_active()
            if active_i == -1:
                return

            dialog = gtk.Dialog("Akkuparameter löschen",\
                    para_dia,\
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,\
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

            active_i = cb_akkulist.get_active()

            label = gtk.Label('Akkuparameter "%s" löschen?' % (akkulist[active_i][0]))
            align = gtk.Alignment(0,0,0,0)
            align.set_padding(16,16,8,8)
            align.show()
            align.add(label)
            dialog.vbox.pack_start(align, True, True, 0)
            label.show()

            # run the dialog
            retval = dialog.run()

            if retval == -3: #OK
                akkulist.pop(active_i) #gtk synchron to akkulist (should)
                cb_akkulist.remove_text(active_i)

            dialog.destroy()

            save_akkulist()

    def cb_akkulist_cb(data=None):
        """ Assign values according to saved Akku-parameters """
        val = cb_akkulist.get_active_text()
        for item in akkulist:
            if item[0] == val:
                cb_atyp.set_active(int(item[1]))
                cb_prog.set_active(int(item[2]))
                cb_lart.set_active(int(item[3]))
                cb_stromw.set_active(int(item[4]))
                cb_stoppm.set_active(int(item[5]))
                sp_anzzellen.set_value(int(item[6]))
                sp_kapazitaet.set_value(int(item[7]))
                sp_ladelimit.set_value(int(item[8]))
                sp_entladelimit.set_value(int(item[9]))
                sp_menge.set_value(int(item[10]))
                sp_zyklen.set_value(int(item[11]))
                break

    def combo_prog_stromw_cb(data=None):
        val = cb_prog.get_active_text()
        val2 = cb_stromw.get_active_text()

        if val2 == "Auto": #always False
            sp_ladelimit.set_sensitive(False)
            sp_entladelimit.set_sensitive(False)

        elif val == "Laden":
            sp_entladelimit.set_sensitive(False)
            sp_ladelimit.set_sensitive(True)

        elif val == "Entladen":
            sp_entladelimit.set_sensitive(True)
            sp_ladelimit.set_sensitive(False)
        else: #programs that require both
            sp_entladelimit.set_sensitive(True)
            sp_ladelimit.set_sensitive(True)

    def combo_atyp_cb(data, lipo_flag):
        val = cb_atyp.get_active_text()
        if val == cfg.AKKU_TYP[5]: #LiPo
            cb_lart.remove_text(1) #Puls
            cb_lart.remove_text(1) #Reflex
            cb_lart.append_text(cfg.LADEART[3])
            cb_lart.set_active(0)

            cb_stromw.set_active(1)
            cb_stromw.set_sensitive(False)
            cb_stoppm.set_active(-1)
            cb_stoppm.set_sensitive(False)

            lipo_flag[0] = True

        elif lipo_flag[0] == True:
            cb_stoppm.set_active(0) # was -1
            cb_stoppm.set_sensitive(True) # was disabled

            cb_lart.remove_text(1) # remove LiPo Fast charge method
            cb_lart.append_text(cfg.LADEART[1])
            cb_lart.append_text(cfg.LADEART[2])
            cb_lart.set_active(0) # and set to 0

            cb_stromw.set_sensitive(True)

            lipo_flag[0] = False

    def get_akkulist():
        if os.path.exists(cfg.exe_dir + "/liste_akkus.dat"):
            fh = open_file(cfg.exe_dir + "/liste_akkus.dat", "rb")
        else:
            return []

        ret = []
        for item in fh.readlines():
            tmp = item.split('\xff')
            #tmp = tmp[:-1] # remove -  last is newline
            if len(tmp) != 12:
                print "Some Error in liste_akkus.dat - is " + str(len(tmp)) + " - should be 12"
                continue

            #shoveling into r but with integer values now (besides of first)
            r = []
            flag = True
            for xy in tmp:
                if flag == True:
                    r.append(str(xy))
                    flag = False
                else:
                    r.append(int(xy))
            ret.append(r)

        fh.close()
        return ret

    #######################################
    #GTK Akku parameter dialog main cfg.gtk_window

    dialog = gtk.Dialog("Akkumatik Settings Ausgang "\
            + str(cfg.gewaehlter_ausgang), cfg.gtk_window,\
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))

    dialog.add_button("Übertragen", 2)
    dialog.add_button("Starten", -3)

    frame = gtk.Frame(None)
    dialog.vbox.pack_start(frame, True, True, 0)

    hbox = gtk.HBox(False, 0)
    hbox.show()
    frame.add(hbox)
    frame.show()

    button = gtk.Button("+")
    button.connect("clicked", button_akku_cb, dialog, "+")
    hbox.pack_start(button, False, True, 1)
    button.show()

    cb_akkulist = gtk.combo_box_new_text()
    hbox.pack_start(cb_akkulist, True, True, 1)

    # [ atyp, prog, lart, stromw, stoppm, Zellen, Kapa, I-lade, I-entlade, Menge ]
    akkulist = get_akkulist()

    for item in akkulist:
        cb_akkulist.append_text(item[0])

    cb_akkulist.connect("changed", cb_akkulist_cb)
    cb_akkulist.show()

    button = gtk.Button("x")
    button.connect("clicked", button_akku_cb, dialog, "x")
    hbox.pack_start(button, False, True, 1)
    button.show()

    #####################################
    # hbox over the whole dialog (besides of akkulist)

    hbox = gtk.HBox(False, 0)
    dialog.vbox.pack_start(hbox, True, True, 0)
    hbox.show()

    #frame 1 (vbox)
    frame = gtk.Frame(None)
    hbox.pack_start(frame, True, True, 0)

    vbox = gtk.VBox(False, 0)
    vbox.set_border_width(5)
    frame.add(vbox)
    frame.show()
    vbox.show()

    lipo_flag = [False] #list, so the callback-function can change the value

    #stuff into frame (vbox)
    label = gtk.Label("Batterie Typ")
    vbox.pack_start(label, True, True, 0)
    label.show()
    cb_atyp = gtk.combo_box_new_text()
    for item in cfg.AKKU_TYP:
        cb_atyp.append_text(item)
    cb_atyp.set_active(cfg.atyp[cfg.gewaehlter_ausgang])
    cb_atyp.show()
    cb_atyp.connect("changed", combo_atyp_cb, lipo_flag)

    vbox.pack_start(cb_atyp, True, True, 0)

    label = gtk.Label("Programm")
    vbox.pack_start(label, True, True, 0)
    label.show()
    cb_prog = gtk.combo_box_new_text()

    if cfg.gewaehlter_ausgang == 1:
        for item in cfg.AMPROGRAMM:
            cb_prog.append_text(item)
    else: #no Entladen...
        cb_prog.append_text(cfg.AMPROGRAMM[0])
        cb_prog.append_text(cfg.AMPROGRAMM[6])

    cb_prog.set_active(cfg.prg[cfg.gewaehlter_ausgang])
    cb_prog.connect("changed", combo_prog_stromw_cb)
    cb_prog.show()
    vbox.pack_start(cb_prog, True, True, 0)

    label = gtk.Label("Ladeart")
    vbox.pack_start(label, True, True, 0)
    label.show()
    cb_lart = gtk.combo_box_new_text()
    for item in cfg.LADEART[:-1]: #exclude LiPo
        cb_lart.append_text(item)
    cb_lart.set_active(cfg.lart[cfg.gewaehlter_ausgang])
    cb_lart.show()
    vbox.pack_start(cb_lart, True, True, 0)

    label = gtk.Label("Stromwahl")
    vbox.pack_start(label, True, True, 0)
    label.show()
    cb_stromw = gtk.combo_box_new_text()
    for item in cfg.STROMWAHL:
        cb_stromw.append_text(item)
    cb_stromw.set_active(cfg.stromw[cfg.gewaehlter_ausgang])
    cb_stromw.connect("changed", combo_prog_stromw_cb)
    cb_stromw.show()
    vbox.pack_start(cb_stromw, True, True, 0)

    label = gtk.Label("Stoppmethode")
    vbox.pack_start(label, True, True, 0)
    label.show()
    cb_stoppm = gtk.combo_box_new_text()
    for item in cfg.STOPPMETHODE:
        cb_stoppm.append_text(item)
    cb_stoppm.set_active(cfg.stoppm[cfg.gewaehlter_ausgang])
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
    adj = gtk.Adjustment(cfg.anzahl_zellen[cfg.gewaehlter_ausgang], 0.0, 30, 1, 1, 0.0)
    sp_anzzellen = gtk.SpinButton(adj, 0.0, 0)
    sp_anzzellen.set_wrap(False)
    sp_anzzellen.set_numeric(True)
    vbox.pack_start(sp_anzzellen, False, True, 0)
    sp_anzzellen.show()

    label = gtk.Label("Kapazität mAh")
    vbox.pack_start(label, True, True, 0)
    label.show()
    adj = gtk.Adjustment(cfg.kapazitaet[cfg.gewaehlter_ausgang], 0.0, 99999, 25, 25, 0.0)
    sp_kapazitaet = gtk.SpinButton(adj, 1.0, 0)
    sp_kapazitaet.set_wrap(False)
    sp_kapazitaet.set_numeric(True)
    vbox.pack_start(sp_kapazitaet, False, True, 0)
    sp_kapazitaet.show()

    label = gtk.Label("I-Laden mA")
    vbox.pack_start(label, True, True, 0)
    label.show()
    adj = gtk.Adjustment(cfg.ladelimit[cfg.gewaehlter_ausgang], 0.0, 9999, 25, 25, 0.0)
    sp_ladelimit = gtk.SpinButton(adj, 1.0, 0)
    sp_ladelimit.set_wrap(False)
    sp_ladelimit.set_numeric(True)
    vbox.pack_start(sp_ladelimit, False, True, 0)
    sp_ladelimit.show()

    label = gtk.Label("I-Entladen mA")
    vbox.pack_start(label, True, True, 0)
    label.show()
    adj = gtk.Adjustment(cfg.entladelimit[cfg.gewaehlter_ausgang], 0.0, 9999, 25, 25, 0.0)
    sp_entladelimit = gtk.SpinButton(adj, 1.0, 0)
    sp_entladelimit.set_wrap(False)
    sp_entladelimit.set_numeric(True)
    vbox.pack_start(sp_entladelimit, False, True, 0)

    if cfg.gewaehlter_ausgang == 2:
        sp_entladelimit.set_sensitive(False)

    sp_entladelimit.show()

    label = gtk.Label("Menge mAh")
    vbox.pack_start(label, True, True, 0)
    label.show()
    adj = gtk.Adjustment(cfg.menge[cfg.gewaehlter_ausgang], 0.0, 99999, 25, 25, 0.0)
    sp_menge = gtk.SpinButton(adj, 1.0, 0)
    sp_menge.set_wrap(False)
    sp_menge.set_numeric(True)
    vbox.pack_start(sp_menge, False, True, 0)
    sp_menge.show()

    label = gtk.Label("Zyklen")
    vbox.pack_start(label, True, True, 0)
    label.show()
    adj = gtk.Adjustment(cfg.zyklen[cfg.gewaehlter_ausgang], 1, 10, 1, 1, 0.0)
    sp_zyklen = gtk.SpinButton(adj, 0.0, 0)
    sp_zyklen.set_wrap(False)
    sp_zyklen.set_numeric(True)
    vbox.pack_start(sp_zyklen, False, True, 0)
    sp_zyklen.show()

    combo_atyp_cb("", lipo_flag)
    combo_prog_stromw_cb(None)

    # run the dialog
    retval = dialog.run()
    dialog.destroy()

    if retval == -3 or retval == 2: #OK or uebertragen got pressed
        hex_str = str(30 + cfg.gewaehlter_ausgang) #kommando 31 or 32
        hex_str += get_pos_hex(cb_atyp.get_active_text(),cfg.AKKU_TYP)
        hex_str += get_pos_hex(cb_prog.get_active_text(),cfg.AMPROGRAMM)
        hex_str += get_pos_hex(cb_lart.get_active_text(),cfg.LADEART)
        hex_str += get_pos_hex(cb_stromw.get_active_text(),cfg.STROMWAHL)

        x = cb_stoppm.get_active_text()
        if x == None: #was for not showing anything on lipo here we need something
            x = cfg.STOPPMETHODE[0] #"Lademenge"
        hex_str += get_pos_hex(x, cfg.STOPPMETHODE)

        hex_str += get_16bit_hex(int(sp_anzzellen.get_value()))
        hex_str += get_16bit_hex(int(sp_kapazitaet.get_value()))
        hex_str += get_16bit_hex(int(sp_ladelimit.get_value()))
        hex_str += get_16bit_hex(int(sp_entladelimit.get_value()))
        hex_str += get_16bit_hex(int(sp_menge.get_value()))
        hex_str += get_16bit_hex(int(sp_zyklen.get_value()))

        cfg.kapazitaet[cfg.gewaehlter_ausgang] = int(sp_kapazitaet.get_value())
        cfg.ladelimit[cfg.gewaehlter_ausgang] = int(sp_ladelimit.get_value())
        cfg.entladelimit[cfg.gewaehlter_ausgang] = int(sp_entladelimit.get_value())
        cfg.menge[cfg.gewaehlter_ausgang] = int(sp_menge.get_value())
        cfg.zyklen[cfg.gewaehlter_ausgang] = int(sp_zyklen.get_value())

        #Kommando u08 Akkutyp u08 program u08 lade_mode u08 strom_mode u08 stop_mode
        #u16 zellenzahl u16 capacity u16 i_lade u16 i_entl u16 menge u16 zyklenzahl

        cfg.command_abort = False #reset

        akkumatik_command(hex_str)

        if retval == -3: #Additionally start
            time.sleep(1.0) #needs somehow, else the threads gets out of order possibly

            if cfg.gewaehlter_ausgang == 1:
                akkumatik_command("44")
            else:
                akkumatik_command("48")

#}}}

##########################################}}}
if __name__ == '__main__': #{{{
##########################################
    if len(sys.argv) > 1 and (sys.argv[1] == "-h" or sys.argv[1] == "--help"):
        print """Usage:

    -c      Continue with collecting serial data
    -n      Begin from scratch
    -h      Print this."""
        sys.exit()

    ##########################################
    #Variablen

    cfg.threadlock = thread.allocate_lock()

    #     Entweter laufenden programm (wobei das sendet ja erst nach start) oder
    #     halt unabhaengig die dialog dinger speichern
    #     Alternativ ok = starten! dann sollte das ganze synchronisiert sein...
    #
    #     ^^^^ (Was jetzt auch der Fal ist......)
    #


    cfg.exe_dir = sys.path[0].replace('\\',"/")

    #Defaults
    cfg.picture_exe = '/usr/local/bin/qiv'
    if platform.system() == "Windows":
        cfg.serial_port = 'COM1'
    else:
        cfg.serial_port = '/dev/ttyS0'

    #e.g for windoofs \'s  (TODO: should not be needed here however)
    cfg.tmp_dir = tempfile.gettempdir().replace("\\","/") + "/remote-akkumatik"
    cfg.chart_dir = cfg.tmp_dir

    if os.path.exists(cfg.exe_dir + "/config.txt"):
        fh = open_file(cfg.exe_dir + "/config.txt", "r")

        for line in fh.readlines():
            if len(line.strip()) < 5:
                continue
            split = line.split("=", 1)
            if split[0].strip().lower()[0] == "#":
                continue
            elif split[0].strip().lower() == "viewer":
                cfg.picture_exe = split[1].strip().replace("\\","/") #windows hm...
            elif split[0].strip().lower() == "cfg.serial_port":
                cfg.serial_port = split[1].strip()
            elif split[0].strip().lower() == "chart_path":
                cfg.chart_dir = split[1].strip().replace("\\","/")
            elif split[0].strip().lower() == "tmp_path":
                cfg.tmp_dir = split[1].strip().replace("\\","/")

    print "* [ Config ] ***********************************"
    print "Picture viewer: %s" % (cfg.picture_exe)
    print "Serial Port:    %s" % (cfg.serial_port)
    print "Chart Path:     %s" % (cfg.chart_dir)
    print "Tmp Path:       %s" % (cfg.tmp_dir)

    if not os.path.isdir(cfg.tmp_dir):
        try:
            os.mkdir(cfg.tmp_dir)
        except OSError, e: # Python >2.5
            if OSError.errno == errno.EEXIST:
                pass
            else:
                print "Unable to create [%s] directory" % cfg.tmp_dir, "Ending program.\n", e
                raw_input("\n\nPress the enter key to exit.")
                sys.exit()
    if not os.path.isdir(cfg.chart_dir):
        try:
            os.mkdir(cfg.chart_dir)
        except OSError, e: # Python >2.5
            if OSError.errno == errno.EEXIST:
                pass
            else:
                print "Unable to create [%s] directory" % cfg.chart_dir, "Ending program.\n", e
                raw_input("\n\nPress the enter key to exit.")
                sys.exit()


    def delete_event(widget, event, data=None):
        return False

    def destroy(widget, data=None):
        gtk.main_quit()

    def buttoncb (widget, data):

        if data == "Chart":
            filesplit(cfg.fser)
            gnuplot()
            #matplot()

        elif data == "Exit":
            gtk.main_quit()

        elif data == "Ausg":
            if cfg.gewaehlter_ausgang == 1: #toggle ausgang
                cfg.gewaehlter_ausgang = 2
                button_start.set_sensitive(False)
                button_stop.set_sensitive(False)
            else:
                cfg.gewaehlter_ausgang = 1
                button_start.set_sensitive(False)
                button_stop.set_sensitive(False)
        elif data == "Start":
            cfg.command_abort = False #reset
            if cfg.gewaehlter_ausgang == 1: #toggle ausgang
                akkumatik_command("44")
            else:
                akkumatik_command("48")

        elif data == "Stop":
            cfg.command_abort = False #reset
            if cfg.gewaehlter_ausgang == 1: #toggle ausgang
                akkumatik_command("41")
            else:
                akkumatik_command("42")

        elif data == "Akku_Settings": #{{{
            akkupara_dialog()

    def draw_pixbuf(widget, event):
        path = cfg.exe_dir + '/bilder/Display.jpg'
        pixbuf = gtk.gdk.pixbuf_new_from_file(path)
        widget.window.draw_pixbuf(widget.style.bg_gc[gtk.STATE_NORMAL], pixbuf, 0, 0, 0,0)


    cfg.gtk_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    cfg.gtk_window.set_title('Akkumatic Remote Display')
    cfg.gtk_window.set_size_request(966,168)
    cfg.gtk_window.set_default_size(966,168)
    cfg.gtk_window.set_position(gtk.WIN_POS_CENTER)

    cfg.gtk_window.connect("delete_event", delete_event)
    cfg.gtk_window.connect("destroy", destroy)
    cfg.gtk_window.set_border_width(8)

    # overall hbox
    hbox = gtk.HBox()
    cfg.gtk_window.add(hbox)
    hbox.connect('expose-event', draw_pixbuf)

    # akkumatik display label
    label = gtk.Label()
    if platform.system() == "Windows": #TODO check once if that fits...
        label.modify_font(pango.FontDescription("mono 25"))
    else:
        label.modify_font(pango.FontDescription("mono 22"))

    gfixed = gtk.Fixed()
    gfixed.put(label, 48 , 38)

    hbox.pack_start(gfixed, False, False, 0)

    label2 = gtk.Label()
    if platform.system() == "Windows": #TODO check once if that fits...
        label2.modify_font(pango.FontDescription("mono 15"))
    else:
        label2.modify_font(pango.FontDescription("mono 12"))

    label2.set_size_request(364,100)
    gfixed.put(label2, 436, 33)

    #vbox for buttons
    vbox = gtk.VBox()
    hbox.pack_end(vbox, False, False, 0)

    # hbox for radios
    hbox = gtk.HBox()
    vbox.pack_start(hbox, True, True, 0)

    # TODO nicht wirklich toll diese Radios
    r1button = gtk.RadioButton(None, None)
    r1button.connect("toggled", buttoncb , "Ausg")
    hbox.pack_start(r1button, True, True, 0)

    label_ausgang = gtk.Label("1   2")
    hbox.pack_start(label_ausgang, True, True, 0)

    r2button = gtk.RadioButton(r1button, None)
    hbox.pack_start(r2button, True, True, 0)

    if cfg.gewaehlter_ausgang == 1:
        r1button.set_active(True)
    else:
        r2button.set_active(True)

    #hbox fuer 'start/stop'
    hbox = gtk.HBox()
    vbox.pack_start(hbox, True, True, 0)

    button_start = gtk.Button("Start")
    button_start.connect("clicked", buttoncb, "Start")
    hbox.pack_start(button_start, False, True, 0)
    button_start.set_sensitive(False)

    button_stop = gtk.Button("Stop")
    button_stop.connect("clicked", buttoncb, "Stop")
    hbox.pack_end(button_stop, False, True, 0)
    button_stop.set_sensitive(False)

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

    cfg.ser = serial_setup()
    cfg.fser = serial_file_setup()

    cfg.gtk_window.show_all() # after file-open (what is needed on plotting)...

    #finally begin collecting
    gobject.timeout_add(100, read_line, (label, label2)) # some tuning around with that value possibly
    #TODO: not fast enough when data-uploading.... via memoery-thing

    gtk.main()

#}}}
#vim: set nosmartindent autoindent tabstop=8 expandtab shiftwidth=4 softtabstop=4 foldmethod=marker foldnestmax=1 :
