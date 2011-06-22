#!/usr/bin/env python
# coding=utf-8
# Copyright (c) 2010, Marco Candrian
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
def generate_output_strs(daten): #{{{
    """Create the strings for the Display (labels) """

    try:
        ausgang = str(int(daten[0][-1:])) #Ausgang
        zeit = daten[1] #Stunden Minuten Sekunden
        lade_v = int(daten[2])/1000.0 #Akkuspannung mV
        lade_v = "%6.3fV" % (lade_v) #format into string
        ampere = int(daten[3]) #Strom A
        if ampere >= 1000 or ampere <= -1000:
            ampere = "%+.2fA" % (ampere/1000.0)
        else:
            ampere = "%imA" % (ampere)

        amph = int(daten[4])/1000.0 #Ladungsmenge amph
        vers_u = int(daten[5])/1000.0 #Versorungsspannung mV
        rimohm_baldelta = int(daten[6]) #akku-unnen mOhm
        c_bat = int(daten[7]) #Akkutemperatur
        tmp_zellen = int(daten[8]) #Zellenzahl / bei Stop -> 'Fehlercode'
    except ValueError, err:
        tmp = "Should really not happen. Please report this line to the maintainer\n"
        tmp += "(generate_output_strs) ValueError: %s\n" % str(err)
        tmp += ", ".join([str(x) for x in daten])
        tmp += "\n"
        print (tmp)
        cfg.FLOG.write(tmp)
        gtk_stuff.message_dialog(cfg.GTK_WINDOW, tmp)

    if tmp_zellen < 50:
        cfg.ANZAHL_ZELLEN[int(ausgang)] = tmp_zellen

    phase = int(daten[9]) #Ladephase 0-stop ...
    if phase == 0:
        cfg.BUTTON_START.set_sensitive(True)
        cfg.BUTTON_STOP.set_sensitive(False)
    else:
        if phase == 10: #Pause
            cfg.BUTTON_START.set_sensitive(True)
        else:
            cfg.BUTTON_START.set_sensitive(False)
        cfg.BUTTON_STOP.set_sensitive(True)

    #TODO 'beim Formieren' also sonst immer 0? dann output2 anpassen
    zyklus = int(daten[10]) #Zyklus
    #sp = int(daten[11]) #Aktive Akkuspeicher

    cfg.ATYP[cfg.GEWAEHLTER_AUSGANG] = int(daten[12]) #Akkutyp
    atyp_str = cfg.AKKU_TYP[int(daten[12])] #Akkutyp

    cfg.PRG[cfg.GEWAEHLTER_AUSGANG] = int(daten[13]) #Programm
    prg_str = cfg.AMPROGRAMM[int(daten[13])] #Programm

    try:
        cfg.LART[cfg.GEWAEHLTER_AUSGANG] = int(daten[14]) #Ladeart
        lart_str = cfg.LADEART[int(daten[14])] #Ladeart
    except IndexError, err:
        tmp = "%s\n" % err
        tmo += "-> %i\n\n" % int(daten[14])
        print (tmp)
        cfg.FLOG.write(tmp)
        gtk_stuff.message_dialog(cfg.GTK_WINDOW, tmp)
        time.sleep(5)
        sys.exit()

    cfg.STROMW[cfg.GEWAEHLTER_AUSGANG] = int(daten[15]) #stromwahl
    stromw_str = cfg.STROMWAHL[int(daten[15])] #stromwahl

    cfg.STOPPM[cfg.GEWAEHLTER_AUSGANG] = int(daten[16]) #stromwahl
    stoppm_str = cfg.STOPPMETHODE[int(daten[16])] #stromwahl

    c_kk = int(daten[17]) #KK Celsius

    tmp_a = []
    for cell in daten[18:-1]:
        try:
            tmp_a.append(int(cell))
        except IndexError:
            tmp = "00:00:00 to long error\n"
            tmp += daten + '\n'
            tmp +=  "----------------------\n\n"
            print (tmp)
            cfg.FLOG.write(tmp)
            gtk_stuff.message_dialog(cfg.GTK_WINDOW, tmp)

    balance_delta = -1
    if len(tmp_a) > 0:
        balance_delta = max(tmp_a) - min(tmp_a)

    if phase == 0: #dann 'Fehlercode' zwangsweise ...?
        if tmp_zellen >= 54: # FEHLER
            output = cfg.FEHLERCODE[tmp_zellen - 50]
            return (output, "")

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
    if cfg.ATYP[cfg.GEWAEHLTER_AUSGANG] == 5: #LiPo
        if len(daten) > 19:
            rimohm_baldelta = "∆%2imV " % (balance_delta)
        else:
            rimohm_baldelta = "∆..mV "
        cfg.MENGE[cfg.GEWAEHLTER_AUSGANG] = 0
        lart_str = "[LiPo]"
        stoppm_str = "[LiPo]"

    output ="%s%s %s %s\n%-7s   %+6.3fAh" % (ausgang, phasedesc, lade_v, \
            zeit, ampere, amph)

    zykll = str(cfg.ZYKLEN[cfg.GEWAEHLTER_AUSGANG])
    if zykll == "0":
        zykll = "-"

    output2 ="%ix%s %2i° %s Z:%1i/%s\n" % \
            (cfg.ANZAHL_ZELLEN[cfg.GEWAEHLTER_AUSGANG], atyp_str, c_bat,\
            rimohm_baldelta, zyklus, zykll)
    output2 +="%s %s %s %s\n" % (prg_str, lart_str, stromw_str, stoppm_str)

    kapa = str(cfg.KAPAZITAET[cfg.GEWAEHLTER_AUSGANG])
    llimit = str(cfg.LADELIMIT[cfg.GEWAEHLTER_AUSGANG])
    entll = str( cfg.ENTLADELIMIT[cfg.GEWAEHLTER_AUSGANG])
    menge_str = str(cfg.MENGE[cfg.GEWAEHLTER_AUSGANG])
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

    return (output, output2)
#}}}
def read_line(labels): #{{{
    """Read serial data (called via interval via 
    gobject.timeout_add) and print it to display"""

    if cfg.FILE_BLOCK == True:
        tmp = "* [Debug] ********************* Blocked serial input\n"
        print tmp
        cfg.FLOG.write(tmp)
        return True

    try:
        lin = cfg.SER.readline()
    except serial.SerialException, err:
        tmp = "%s\n\n" % err
        print (tmp)
        cfg.FLOG.write(tmp)
        gtk_stuff.message_dialog(cfg.GTK_WINDOW, tmp)
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
            cfg.COMMAND_WAIT = False # Kommando kam an

    if lin[:1] == "#" or len(daten[0]) != 1 or len(daten) < 19 or len(daten) > 31:
        return True

    curtime = lin[2:10]

    if curtime == "00:00:00": #not begun yet
        yeswrite = False

    if curtime == cfg.OLDTIME[int(daten[0])]:
        yeswrite = False

    #if lin[11:16] == "00000": #no volt lines
        #print ("FILTER OUT: Volt has Zero value")
        #return ""

    cfg.OLDTIME[int(daten[0])] = curtime

    try:
        if yeswrite:
            cfg.FSER.write(lin)
    except  ValueError, err:
        tmp = "%s\n" % err
        tmp += "Should not happen, but reopening file anyway\n\n"
        print(tmp)
        cfg.FLOG.write(tmp)
        gtk_stuff.message_dialog(cfg.GTK_WINDOW, tmp)
        cfg.FSER = helper.open_file(cfg.TMP_DIR+'/serial-akkumatik.dat', 'ab')
        return True

    if (daten[0] == "1" and cfg.GEWAEHLTER_AUSGANG == 1) \
            or (daten[0] == "2" and cfg.GEWAEHLTER_AUSGANG == 2):
        (labstr1, labstr2) = generate_output_strs(daten)
        output_data(labstr1, labels[0], labstr2, labels[1])

    return True

#}}}
def serial_setup(): #{{{
    """ try to connect to the serial port """

    tmp = "* [ Serial Port ] ***********************************\n"
    tmp += ("Trying to open serial port '%s': " % cfg.SERIAL_PORT)
    if platform.system() == "Windows":
        #needen on comx>10 - seems to work
        cfg.SERIAL_PORT = '\\\\.\\' + cfg.SERIAL_PORT

    try:
        cfg.SER = serial.Serial(
            port=cfg.SERIAL_PORT,
            baudrate = 9600,
            parity = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            bytesize = serial.EIGHTBITS,
            xonxoff=0,
            rtscts=0,
            dsrdtr = False,
            timeout = 0.08, #some tuning around with that value possibly
            writeTimeout = 2.0)

        if platform.system() != "Windows":
            cfg.SER.open()

        cfg.SER.isOpen()
        tmp += "OK\n"

    except serial.SerialException, err:
        tmp += "Failed\n"

        tmp += "Program abort: \"%s\"\n" % err
        time.sleep(3)
        cfg.FLOG.write(tmp)
        cfg.FLOG.close()
        sys.exit()

    cfg.FLOG.write(tmp)
    return cfg.SER

#}}}
def serial_file_setup(): #{{{
    """ setup the file to store the serial data into """

    if len(sys.argv) > 1 and (sys.argv[1] == "-c" or sys.argv[1] == "-C"):
        fhser = helper.open_file(cfg.TMP_DIR + '/serial-akkumatik.dat', 'ab')
        cfg.FLOG.write("%s opened (new or create binary)" % cfg.TMP_DIR + '/serial-akkumatik.dat\n')
    else:
        fhser = helper.open_file(cfg.TMP_DIR + '/serial-akkumatik.dat', 'w+b')
        cfg.FLOG.write("%s opened (new or create binary)" % cfg.TMP_DIR + '/serial-akkumatik.dat\n')

    return fhser

#}}}
##########################################}}}
if __name__ == '__main__': #{{{
##########################################
    if len(sys.argv) > 1 and (sys.argv[1] == "-h" or sys.argv[1] == "-H" or sys.argv[1] == "--help"):
        print """Usage:

    -c      Continue (add new arriving data to (potential) existing serial data)
    -h      Print this."""
        sys.exit()

    ##########################################
    #Variablen


    cfg.THREADLOCK = thread.allocate_lock()

    cfg.EXE_DIR = sys.path[0].replace('\\',"/") #TODO needed?
    if sys.path[0].endswith("\\library.zip\\gtk-2.0"):  #for py2exe
        cfg.EXE_DIR = sys.path[0][0:-20]

    cfg.TMP_DIR = tempfile.gettempdir().replace("\\","/") + "/remote-akkumatik"
    cfg.CHART_DIR = cfg.TMP_DIR

    cfg.FLOG = helper.open_file(cfg.EXE_DIR + '/log.txt', 'w')

    #Defaults
    cfg.PICTURE_EXE = '/usr/local/bin/qiv'
    if platform.system() == "Windows":
        cfg.SERIAL_PORT = 'COM1'
    else:
        cfg.SERIAL_PORT = '/dev/ttyS0'


    if os.path.exists(cfg.EXE_DIR + "/config.txt"):
        FCONF = helper.open_file(cfg.EXE_DIR + "/config.txt", "r")

        for line in FCONF.readlines():
            if len(line.strip()) < 5:
                continue
            split = line.split("=", 1)
            if split[0].strip().lower()[0] == "#":
                continue
            elif split[0].strip().lower() == "viewer":
                cfg.PICTURE_EXE = split[1].strip().replace("\\","/") #TODO:?
            elif split[0].strip().lower() == "cfg.SERIAL_PORT":
                cfg.SERIAL_PORT = split[1].strip()
            elif split[0].strip().lower() == "chart_path":
                cfg.CHART_DIR = split[1].strip().replace("\\","/")
            elif split[0].strip().lower() == "tmp_path":
                cfg.TMP_DIR = split[1].strip().replace("\\","/")

    tmp = "* [ Config ] ***********************************\n"
    tmp += "Picture viewer: %s\n" % (cfg.PICTURE_EXE)
    tmp += "Serial Port:    %s\n" % (cfg.SERIAL_PORT)
    tmp += "Chart Path:     %s\n" % (cfg.CHART_DIR)
    tmp += "Tmp Path:       %s\n\n" % (cfg.TMP_DIR)
    print tmp
    cfg.FLOG.write(tmp)

    if not os.path.isdir(cfg.TMP_DIR):
        try:
            os.mkdir(cfg.TMP_DIR)
        except OSError, errx: # Python >2.5
            if OSError.errno == errno.EEXIST:
                pass
            else:
                tmp = "Unable to create [%s] directory" \
                        % cfg.TMP_DIR, "Ending program.\n", errx
                print tmp
                cfg.FLOG.write(tmp)
                cfg.FLOG.close()
                gtk_stuff.message_dialog(None, tmp)
                time.sleep(10)
                sys.exit()
    if not os.path.isdir(cfg.CHART_DIR):
        try:
            os.mkdir(cfg.CHART_DIR)
        except OSError, errx: # Python >2.5
            if OSError.errno == errno.EEXIST:
                pass
            else:
                tmp = "Unable to create [%s] directory" \
                        % cfg.TMP_DIR, "Ending program.\n", errx
                print tmp
                cfg.FLOG.write(tmp)
                cfg.FLOG.close()
                gtk_stuff.message_dialog(None, tmp)
                time.sleep(10)
                sys.exit()

    cfg.SER = serial_setup()
    cfg.FSER = serial_file_setup()

    #TODO: why not putting label's also into cfg....
    (LABEL, LABEL2) = gtk_stuff.main_window()

    #finally begin collecting
    #TODO: faster when data-uploading via memoery-thing?
    # some tuning around with that value possibly
    gobject.timeout_add(120, read_line, (LABEL, LABEL2))

    gtk.main()
    cfg.FLOG.close()

#}}}
# vim: set nosi ai ts=8 et shiftwidth=4 sts=4 fdm=marker foldnestmax=1 :
