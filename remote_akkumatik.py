#!/usr/bin/env python
# coding=utf-8
""" remote akkumatik program for Stefan Estners Akkumatik """

import os
import sys
import errno

import tempfile

import time
import thread

import pygtk
pygtk.require('2.0')
import gtk
import gobject

import serial
import platform

#own import
import cfg
import gtk_stuff
import helper

##########################################
#Serial + output stuff{{{
##########################################
def output_data(output, label, output2, label2): #{{{
    """ print the stuff to the display """

    label.set_markup('<span foreground="#444444">'+ output + '</span>')
    label2.set_markup('<span foreground="#339933">'+ output2 + '</span>')
    while gtk.events_pending():
        gtk.main_iteration()

#}}}
def read_line(labels): #{{{
    """Read serial data (called via interval via 
    gobject.timeout_add) and print it to display"""

    if cfg.file_block == True:
        print "* [Debug] ********************* Blocked serial input"
        return True

    try:
        lin = cfg.ser.readline()
    except serial.SerialException, err:
        print "%s" % err
        return True

    daten = lin.split('\xff')

    ################*################
    #Clean/check lines before writing or so

    yeswrite = True

    #handle command-acknowledged string
    if len(daten[0]) > 1:
        while lin[0:2] == "A1": #more Ack.. can be there
            lin = lin[5:]
            daten[0] = daten[0][-1:] #last digit only (Ausgang) wird kaum gehen
            cfg.command_wait = False # Kommando kam an

    if lin[:1] == "#" or len(daten[0]) != 1 or len(daten) < 19:
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
    except  ValueError, err:
        print "%s" % err
        print "Should not happen, but reopening file anyway"
        cfg.fser = helper.open_file(cfg.tmp_dir+'/serial-akkumatik.dat', 'ab')
        return True


    if (daten[0] == "1" and cfg.gewaehlter_ausgang == 1) \
            or (daten[0] == "2" and cfg.gewaehlter_ausgang == 2):
        ausgang = str(long(daten[0][-1:])) #Ausgang
        zeit = daten[1] #Stunden Minuten Sekunden
        lade_v = long(daten[2])/1000.0 #Akkuspannung mV
        lade_v = "%6.3fV" % (lade_v) #format into string
        ampere = long(daten[3]) #Strom A
        if ampere >= 1000 or ampere <= -1000:
            ampere = "%+.2fA" % (ampere/1000.0)
        else:
            ampere = "%imA" % (ampere)

        amph = long(daten[4])/1000.0 #Ladungsmenge amph
        vers_u = long(daten[5])/1000.0 #Versorungsspannung mV
        rimohm_baldelta = long(daten[6]) #akku-unnen mOhm
        c_bat = long(daten[7]) #Akkutemperatur
        tmp_zellen = long(daten[8]) #Zellenzahl / bei Stop -> 'Fehlercode'
        if tmp_zellen < 50:
            cfg.anzahl_zellen[long(ausgang)] = tmp_zellen

        phase = long(daten[9]) #Ladephase 0-stop ...
        if phase == 0:
            cfg.button_start.set_sensitive(True)
            cfg.button_stop.set_sensitive(False)
        else:
            if phase == 10: #Pause
                cfg.button_start.set_sensitive(True)
            else:
                cfg.button_start.set_sensitive(False)
            cfg.button_stop.set_sensitive(True)

        #TODO 'beim Formieren' also sonst immer 0? dann output2 anpassen
        zyklus = long(daten[10]) #Zyklus
        #sp = long(daten[11]) #Aktive Akkuspeicher

        cfg.atyp[cfg.gewaehlter_ausgang] = long(daten[12]) #Akkutyp
        atyp_str = cfg.AKKU_TYP[long(daten[12])] #Akkutyp

        cfg.prg[cfg.gewaehlter_ausgang] = long(daten[13]) #Programm
        prg_str = cfg.AMPROGRAMM[long(daten[13])] #Programm

        try:
            cfg.lart[cfg.gewaehlter_ausgang] = long(daten[14]) #Ladeart
            lart_str = cfg.LADEART[long(daten[14])] #Ladeart
        except IndexError, err:
            print "%s" % err
            print "-> %i" % long(daten[14])
            time.sleep(10)
            sys.exit()

        cfg.stromw[cfg.gewaehlter_ausgang] = long(daten[15]) #stromwahl
        stromw_str = cfg.STROMWAHL[long(daten[15])] #stromwahl

        cfg.stoppm[cfg.gewaehlter_ausgang] = long(daten[16]) #stromwahl
        stoppm_str = cfg.STOPPMETHODE[long(daten[16])] #stromwahl

        c_kk = long(daten[17]) #KK Celsius

        tmp_a = []
        for cell in daten[18:-1]:
            try:
                tmp_a.append(long(cell))
            except IndexError:
                print "00:00:00 to long error"
                print daten
                print "----------------------"

        balance_delta = -1
        if len(tmp_a) > 0:
            balance_delta = max(tmp_a) - min(tmp_a)

        if phase == 0: #dann 'Fehlercode' zwangsweise ...?
            if tmp_zellen >= 54: # FEHLER
                output = cfg.FEHLERCODE[tmp_zellen - 50]
                output_data(output, labels[0], "", label[1])
                return True

            if tmp_zellen >= 50: #'gute' codes
                phasedesc = "%-11s" % (cfg.FEHLERCODE[tmp_zellen - 50])
                ausgang = ""
                lade_v = ""

            else:
                phasedesc = "?????" # should never happen possibly

        # 51 VOLL   Ladevorgang wurde korrekt beendet, Akku ist voll geladen
        # 52 LEER   Entladevorgang wurde korrekt beendet, Akku ist leer
        # TODO: 52 od 51 + "x..." FERTIG Lipo-Lagerprogramm wurde korrekt 
        #         beendet, Akku ist fertig zum Lagern
        # TODO: 52 od 51 + "x ": ? MENGE  Vorgang wurde durch eingestelltes 
        #        Mengenlimit beendet
        # 50 STOP Vorgang wurde manuell (vorzeitig) beendet
        # FEHLER Vorgang wurde fehlerhaft beendet

        elif phase == 10:
            phasedesc = " PAUSE    "
            lade_v = ""
        else:
            if phase >= 1 and phase <= 5:
                tmp = "L"
            elif phase >= 7 and phase <= 9:
                tmp = "E"
                phase = "-"

            phasedesc = atyp_str[0:1] + tmp + str(phase)

        #< stunde dann Minunte:Sekunden, sonst Stunde:Minuten
        if zeit[0:2] == "00":
            zeit = zeit [3:]
        else:
            zeit = zeit [:-3]

        #label print
        rimohm_baldelta = "Ri:%03i" % (rimohm_baldelta)
        #TODO:  more elgegant...
        if cfg.atyp[cfg.gewaehlter_ausgang] == 5: #LiPo
            if len(daten) > 19:
                rimohm_baldelta = "∆%2imV " % (balance_delta)
            else:
                rimohm_baldelta = "∆..mV "
            cfg.menge[cfg.gewaehlter_ausgang] = 0
            lart_str = "[LiPo]"
            stromw_str = "[LiPo]"
            stoppm_str = "[LiPo]"


        output ="%s%s %s %s\n%-7s   %+6.3fAh" % (ausgang, phasedesc, lade_v, \
                zeit, ampere, amph)

        zykll = str(cfg.zyklen[cfg.gewaehlter_ausgang])
        if zykll == "0":
            zykll = "-"

        output2 ="%ix%s %2i° %s Z:%1i/%s\n" % \
                (cfg.anzahl_zellen[cfg.gewaehlter_ausgang], atyp_str, c_bat,\
                rimohm_baldelta, zyklus, zykll)
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
        output2 +="Menge:%smAh VerU:%5.2fV %2i°KK\n" % (menge_str, vers_u, c_kk)

        output_data(output, labels[0], output2, labels[1])

    return True

#}}}
def serial_setup(): #{{{
    """ try to connect to the serial port """

    print "* [ Serial Port ] ***********************************"
    sys.stdout.write("Trying to open serial port '%s': " % cfg.serial_port)
    sys.stdout.flush()
    if platform.system() == "Windows":
        #needen on comx>10 - seems to work
        cfg.serial_port = '\\\\.\\' + cfg.serial_port

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

    except serial.SerialException, err:
        sys.stdout.write("Failed\n\n")
        sys.stdout.flush()
        print "Program abort: \"%s\"" % err
        time.sleep(3)
        sys.exit()

    return cfg.ser

#}}}
def serial_file_setup(): #{{{
    """ setup the file to store the serial data into """

    if len(sys.argv) > 1 and (sys.argv[1] == "-c" or sys.argv[1] == "-C"):
        fhser = helper.open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'ab')
    elif len(sys.argv) > 1 and (sys.argv[1] == "-n" or sys.argv[1] == "-N"):
        fhser = helper.open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'w+b')
    else:
        print "\n********************************************************"
        sys.stdout.write("New collecting (3 seconds to abort (Ctrl-C)): ")
        sys.stdout.flush()
        time.sleep(1.0)
        for i in range(1, 4):
            sys.stdout.write("..." + str(i))
            sys.stdout.flush()
            time.sleep(1.0)
        sys.stdout.write("\n\n")
        sys.stdout.flush()
        fhser = helper.open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'w+b')

    return fhser

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

    cfg.exe_dir = sys.path[0].replace('\\',"/") #TODO neede?
    cfg.tmp_dir = tempfile.gettempdir().replace("\\","/") + "/remote-akkumatik"
    cfg.chart_dir = cfg.tmp_dir

    #Defaults
    cfg.picture_exe = '/usr/local/bin/qiv'
    if platform.system() == "Windows":
        cfg.serial_port = 'COM1'
    else:
        cfg.serial_port = '/dev/ttyS0'


    if os.path.exists(cfg.exe_dir + "/config.txt"):
        FCONF = helper.open_file(cfg.exe_dir + "/config.txt", "r")

        for line in FCONF.readlines():
            if len(line.strip()) < 5:
                continue
            split = line.split("=", 1)
            if split[0].strip().lower()[0] == "#":
                continue
            elif split[0].strip().lower() == "viewer":
                cfg.picture_exe = split[1].strip().replace("\\","/") #TODO:?
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
        except OSError, errx: # Python >2.5
            if OSError.errno == errno.EEXIST:
                pass
            else:
                print "Unable to create [%s] directory" \
                        % cfg.tmp_dir, "Ending program.\n", errx
                raw_input("\n\nPress the enter key to exit.")
                sys.exit()

    if not os.path.isdir(cfg.chart_dir):
        try:
            os.mkdir(cfg.chart_dir)
        except OSError, errx: # Python >2.5
            if OSError.errno == errno.EEXIST:
                pass
            else:
                print "Unable to create [%s] directory" \
                        % cfg.chart_dir, "Ending program.\n", errx
                raw_input("\n\nPress the enter key to exit.")
                sys.exit()

    cfg.ser = serial_setup()
    cfg.fser = serial_file_setup()

    #why not putting label's also into cfg....
    (LABEL, LABEL2) = gtk_stuff.main_window()

    #finally begin collecting
    #TODO: faster when data-uploading via memoery-thing?
    # some tuning around with that value possibly
    gobject.timeout_add(100, read_line, (LABEL, LABEL2))

    gtk.main()

#}}}
#vim: set nosi ai ts=8 et shiftwidth=4 sts=4 fdm=marker foldnestmax=1 :
