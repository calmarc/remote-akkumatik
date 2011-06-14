#!/usr/bin/env python
# coding=utf-8

#{{{imports
import os
import sys
import errno

import tempfile

import time
import thread

import pygtk
pygtk.require('2.0')
import gtk
import pango
import gobject


import serial
import platform

#import matplotlib.pyplot as plt

#own import
import cfg
import gtk_stuff
import helper
import ra_gnuplot

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
        f = helper.open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'ab') #reopen
        print "Not sufficient Serial Data avaiable"
        cfg.file_block = False
        return

    cfg.fser = helper.open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'rb')

    for line in cfg.fser.readlines(): #get all lines in one step
        if cfg.file_block == True:
            cfg.fser.close()
            cfg.fser = helper.open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'ab') #reopen
            cfg.file_block = False #allow further getting serial adding..

        if line[0:1] == "1":

            current_time1 = long(line[2:4]) * 60 + long(line[5:7]) * 60 + long(line[8:10]) #in seconds

            previous_line1 = line

            line_counter1 += 1

            if current_time1 < previous_time1:
                fname = cfg.tmp_dir + '/Akku1-'+ "%02i" % (file_zaehler1)+'.dat'
                fh1 = helper.open_file(fname, "wb+")

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
                fh2 = helper.open_file(fname, "wb+")

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
        fh1 = helper.open_file(fname, "wb+")

        if platform.system() == "Windows":
            ausgang1_part = ausgang1_part.replace('\xff', " ")

        fh1.write(ausgang1_part)
        fh1.close()
        print "Generated: " + "%28s" % (fname[-27:])
    if len(ausgang2_part) > 0:
        fname = cfg.tmp_dir + '/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
        fh2 = helper.open_file(fname, "wb+")

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
        cfg.fser = helper.open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'ab')
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

        cfg.atyp[cfg.gewaehlter_ausgang] = long(daten[12]) #Akkutyp
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
        f = helper.open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'ab')
    elif len(sys.argv) > 1 and (sys.argv[1] == "-n" or sys.argv[1] == "-N"):
        f = helper.open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'wb+')
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
        f = helper.open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'wb+')

    return f

#}}}

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

    #TODO put into whre needed? or before dialog calling...?
    cfg.threadlock = thread.allocate_lock()

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
        fh = helper.open_file(cfg.exe_dir + "/config.txt", "r")

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
            ra_gnuplot.gnuplot()
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
                helper.akkumatik_command("44", data)
            else:
                helper.akkumatik_command("48", data)

        elif data == "Stop":
            cfg.command_abort = False #reset
            if cfg.gewaehlter_ausgang == 1: #toggle ausgang
                helper.akkumatik_command("41", data)
            else:
                helper.akkumatik_command("42", data)

        elif data == "Akku_Settings": #{{{
            (cmd1, cmd2)  = gtk_stuff.akkupara_dialog()

            cfg.command_abort = False #reset

            # TODO: would be good when - if succeded, _all_ akku-settings get changed on the display
            helper.akkumatik_command(cmd1, "Übertragen")

            if cmd2 != "":
                time.sleep(1.0) #else threads may get out of order somehow
                helper.akkumatik_command(cmd2, "Start")

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
