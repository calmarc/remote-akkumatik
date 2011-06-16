# coding=utf-8
""" graphical stuff (GTK) """

import pygtk
pygtk.require('2.0')
import gtk
import pango

import os
import platform
import time

#own import
import cfg
import helper
import ra_gnuplot
#import ra_matplot

##########################################
# Main Window{{{
##########################################
def main_window():
    """ main window (display) """
    def delete_event(widget, event, data=None):
        """ Delete Event """
        return False

    def destroy(widget, data=None):
        """ Detroy """
        gtk.main_quit()

    def buttoncb (widget, data):
        """ callback function from the main display buttons """

        if data == "Chart":
            ra_gnuplot.gnuplot()
            #ra_matplot.matplot()

        elif data == "Exit":
            gtk.main_quit()

        elif data == "Ausg":
            if cfg.GEWAEHLTER_AUSGANG == 1: #toggle ausgang
                cfg.GEWAEHLTER_AUSGANG = 2
                cfg.BUTTON_START.set_sensitive(False)
                cfg.BUTTON_STOP.set_sensitive(False)
            else:
                cfg.GEWAEHLTER_AUSGANG = 1
                cfg.BUTTON_START.set_sensitive(False)
                cfg.BUTTON_STOP.set_sensitive(False)
        elif data == "Start":
            cfg.COMMAND_ABORT = False #reset
            if cfg.GEWAEHLTER_AUSGANG == 1: #toggle ausgang
                #data = something like "Start"
                helper.akkumatik_command("44", data)
            else:
                helper.akkumatik_command("48", data)

        elif data == "Stop":
            cfg.COMMAND_ABORT = False #reset
            if cfg.GEWAEHLTER_AUSGANG == 1: #toggle ausgang
                helper.akkumatik_command("41", data)
            else:
                helper.akkumatik_command("42", data)

        elif data == "Akku_Settings":
            (cmd1, cmd2) = akkupara_dialog()
            if not cmd1:
                return

            cfg.COMMAND_ABORT = False #reset

            helper.akkumatik_command(cmd1, "Übertragen")

            if cmd2 != "":
                time.sleep(1.0) #else threads may get out of order somehow
                helper.akkumatik_command(cmd2, "Start")

    def draw_pixbuf(widget, event):
        """ add the picture to the window """
        path = cfg.EXE_DIR + '/bilder/Display.jpg'
        pixbuf = gtk.gdk.pixbuf_new_from_file(path)
        widget.window.draw_pixbuf(widget.style.bg_gc[gtk.STATE_NORMAL], \
                pixbuf, 0, 0, 0,0)

    cfg.GTK_WINDOW = gtk.Window(gtk.WINDOW_TOPLEVEL)
    cfg.GTK_WINDOW.set_title('Akkumatic Remote Display')
    cfg.GTK_WINDOW.set_size_request(966, 168)
    cfg.GTK_WINDOW.set_default_size(966, 168)
    cfg.GTK_WINDOW.set_position(gtk.WIN_POS_CENTER)

    cfg.GTK_WINDOW.connect("delete_event", delete_event)
    cfg.GTK_WINDOW.connect("destroy", destroy)
    cfg.GTK_WINDOW.set_border_width(8)

    # overall hbox
    hbox = gtk.HBox()
    cfg.GTK_WINDOW.add(hbox)
    hbox.connect('expose-event', draw_pixbuf)

    # akkumatik display label
    label = gtk.Label()
    if platform.system() == "Windows": #TODO check once if that fits...
        label.modify_font(pango.FontDescription("mono 25"))
    else:
        label.modify_font(pango.FontDescription("mono 22"))

    label.set_size_request(370, 92)
    label.set_alignment(0, 0)
    label.set_justify(gtk.JUSTIFY_LEFT)

    gfixed = gtk.Fixed()
    hbox.pack_start(gfixed, True, True, 0)

    gfixed.put(label, 48 , 36)

    label2 = gtk.Label()
    if platform.system() == "Windows": #TODO check once if that fits...
        label2.modify_font(pango.FontDescription("mono bold 15"))
    else:
        label2.modify_font(pango.FontDescription("mono bold 12"))

    label2.set_size_request(364, 100)
    label2.set_alignment(0, 0)
    label2.set_justify(gtk.JUSTIFY_LEFT)
    gfixed.put(label2, 440, 33)

    cfg.LABEL_STATUS = gtk.Label()
    if platform.system() == "Windows": #TODO check once if that fits...
        cfg.LABEL_STATUS.modify_font(pango.FontDescription("mono bold 15"))
    else:
        cfg.LABEL_STATUS.modify_font(pango.FontDescription("mono bold 12"))

    cfg.LABEL_STATUS.set_size_request(774, 22)
    cfg.LABEL_STATUS.set_alignment(0, 0)
    cfg.LABEL_STATUS.set_justify(gtk.JUSTIFY_LEFT)
    cfg.EVENT_BOX_LSTATUS = gtk.EventBox()
    cfg.EVENT_BOX_LSTATUS.add(cfg.LABEL_STATUS)
    cfg.EVENT_BOX_LSTATUS.modify_bg(gtk.STATE_NORMAL, \
            cfg.EVENT_BOX_LSTATUS.get_colormap().alloc_color("#aaaaaa"))

    gfixed.put(cfg.EVENT_BOX_LSTATUS, 36, 136)

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

    if cfg.GEWAEHLTER_AUSGANG == 1:
        r1button.set_active(True)
    else:
        r2button.set_active(True)

    #hbox fuer 'start/stop'
    hbox = gtk.HBox()
    vbox.pack_start(hbox, True, True, 0)

    cfg.BUTTON_START = gtk.Button("Start")
    cfg.BUTTON_START.connect("clicked", buttoncb, "Start")
    hbox.pack_start(cfg.BUTTON_START, False, True, 0)
    cfg.BUTTON_START.set_sensitive(False)

    cfg.BUTTON_STOP = gtk.Button("Stop")
    cfg.BUTTON_STOP.connect("clicked", buttoncb, "Stop")
    hbox.pack_end(cfg.BUTTON_STOP, False, True, 0)
    cfg.BUTTON_STOP.set_sensitive(False)

    vbox.pack_start(gtk.HSeparator(), False, True, 5)

    button = gtk.Button("Akku Para")
    button.connect("clicked", buttoncb, "Akku_Settings")
    vbox.pack_start(button, False, True, 0)

    button = gtk.Button("Chart")
    button.connect("clicked", buttoncb, "Chart")
    vbox.pack_start(button, False, True, 0)

    button = gtk.Button("Exit")
    button.set_size_request(98, 20)
    button.connect("clicked", buttoncb, "Exit")
    vbox.pack_end(button, False, True, 0)

    vbox.pack_end(gtk.HSeparator(), False, True, 5)

    # after file-open (what is needed on plotting)... hm?
    cfg.GTK_WINDOW.show_all()
    cfg.LABEL_STATUS.hide()

    return (label, label2)

##########################################}}}
# Akku Parameter Dialog{{{
##########################################

def akkupara_dialog(): #{{{
    """ The Akkuparameter Dialog """

    def save_akkulist():
        """ Save the current akku-list """
        fha = helper.open_file(cfg.EXE_DIR + "/liste_akkus.dat", "wb")
        for item in akkulist:
            line = ""
            for tmp in item:
                line += str(tmp)  + '\xff'
            line = line[:-1] # remove last xff
            line += "\n"
            fha.write(line)
        fha.close()

    def button_akku_cb(widget, para_dia, data=None):
        """ Either add or delete from the akkulist """
        if data == "+":
            dialog = gtk.Dialog("Name Akkuparameter ", \
                    para_dia, \
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, \
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

            label = gtk.Label("Akkuparameter Name")
            dialog.vbox.pack_start(label, True, True, 8)
            label.show()

            tbx = gtk.Entry()
            tbx.set_max_length(20)
            tbx.show()
            dialog.vbox.pack_start(tbx, True, True, 8)

            # run the dialog
            retval = dialog.run()

            if retval == -3: #OK
                txt = tbx.get_text()

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
                        int(cb_atyp.get_active()), \
                        int(cb_prog.get_active()), \
                        int(cb_lart.get_active()), \
                        int(cb_stromw.get_active()), \
                        int(cb_stoppm.get_active()), \
                        int(sp_anzzellen.get_value()), \
                        int(sp_kapazitaet.get_value()), \
                        int(sp_ladelimit.get_value()), \
                        int(sp_entladelimit.get_value()), \
                        int(sp_menge.get_value()), \
                        int(sp_zyklen.get_value())])

                #sort on 'name'
                akkulist.sort(key = lambda x: x[0].lower())

                #find new item in new ordered list
                i = 0
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

            dialog = gtk.Dialog("Akkuparameter löschen", \
                    para_dia, \
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, \
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

            active_i = cb_akkulist.get_active()

            label = gtk.Label('Akkuparameter "%s" löschen?' %\
                    (akkulist[active_i][0]))
            align = gtk.Alignment(0, 0, 0, 0)
            align.set_padding(16, 16, 8, 8)
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
        """ when the program or stromwahl changed """
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
        """ akku type callback (when changed) """
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
        """ load akkulist from harddrive """
        if os.path.exists(cfg.EXE_DIR + "/liste_akkus.dat"):
            fha = helper.open_file(cfg.EXE_DIR + "/liste_akkus.dat", "rb")
        else:
            return []

        ret = []
        for item in fha.readlines():
            tmp = item.split('\xff')
            #tmp = tmp[:-1] # remove -  last is newline
            if len(tmp) != 12:
                print "Some Error in liste_akkus.dat - is " +\
                        str(len(tmp)) + " - should be 12"
                continue

            #shoveling into r but with integer values now (besides of first)
            rtmp = []
            flag = True
            for xyx in tmp:
                if flag == True:
                    rtmp.append(str(xyx))
                    flag = False
                else:
                    rtmp.append(int(xyx))
            ret.append(rtmp)

        fha.close()
        return ret

    #######################################
    #GTK Akku parameter dialog main window
    dialog = gtk.Dialog("Akkumatik Settings Ausgang "\
            + str(cfg.GEWAEHLTER_AUSGANG), cfg.GTK_WINDOW, \
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
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

    # [atyp,prog,lart,stromw,stoppm,Zellen,Kapa,I-lade,I-entlade,Menge]
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
    cb_atyp.set_active(cfg.ATYP[cfg.GEWAEHLTER_AUSGANG])
    cb_atyp.show()
    cb_atyp.connect("changed", combo_atyp_cb, lipo_flag)

    vbox.pack_start(cb_atyp, True, True, 0)

    label = gtk.Label("Programm")
    vbox.pack_start(label, True, True, 0)
    label.show()
    cb_prog = gtk.combo_box_new_text()

    if cfg.GEWAEHLTER_AUSGANG == 1:
        for item in cfg.AMPROGRAMM:
            cb_prog.append_text(item)
    else: #no Entladen...
        cb_prog.append_text(cfg.AMPROGRAMM[0])
        cb_prog.append_text(cfg.AMPROGRAMM[6])

    cb_prog.set_active(cfg.PRG[cfg.GEWAEHLTER_AUSGANG])
    cb_prog.connect("changed", combo_prog_stromw_cb)
    cb_prog.show()
    vbox.pack_start(cb_prog, True, True, 0)

    label = gtk.Label("Ladeart")
    vbox.pack_start(label, True, True, 0)
    label.show()
    cb_lart = gtk.combo_box_new_text()
    for item in cfg.LADEART[:-1]: #exclude LiPo
        cb_lart.append_text(item)
    cb_lart.set_active(cfg.LART[cfg.GEWAEHLTER_AUSGANG])
    cb_lart.show()
    vbox.pack_start(cb_lart, True, True, 0)

    label = gtk.Label("Stromwahl")
    vbox.pack_start(label, True, True, 0)
    label.show()
    cb_stromw = gtk.combo_box_new_text()
    for item in cfg.STROMWAHL:
        cb_stromw.append_text(item)
    cb_stromw.set_active(cfg.STROMW[cfg.GEWAEHLTER_AUSGANG])
    cb_stromw.connect("changed", combo_prog_stromw_cb)
    cb_stromw.show()
    vbox.pack_start(cb_stromw, True, True, 0)

    label = gtk.Label("Stoppmethode")
    vbox.pack_start(label, True, True, 0)
    label.show()
    cb_stoppm = gtk.combo_box_new_text()
    for item in cfg.STOPPMETHODE:
        cb_stoppm.append_text(item)
    cb_stoppm.set_active(cfg.STOPPM[cfg.GEWAEHLTER_AUSGANG])
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
    adj = gtk.Adjustment(cfg.ANZAHL_ZELLEN[cfg.GEWAEHLTER_AUSGANG], \
            0.0, 30, 1, 1, 0.0)
    sp_anzzellen = gtk.SpinButton(adj, 0.0, 0)
    sp_anzzellen.set_wrap(False)
    sp_anzzellen.set_numeric(True)
    vbox.pack_start(sp_anzzellen, False, True, 0)
    sp_anzzellen.show()

    label = gtk.Label("Kapazität mAh")
    vbox.pack_start(label, True, True, 0)
    label.show()
    adj = gtk.Adjustment(cfg.KAPAZITAET[cfg.GEWAEHLTER_AUSGANG], \
            0.0, 99999, 25, 25, 0.0)
    sp_kapazitaet = gtk.SpinButton(adj, 1.0, 0)
    sp_kapazitaet.set_wrap(False)
    sp_kapazitaet.set_numeric(True)
    vbox.pack_start(sp_kapazitaet, False, True, 0)
    sp_kapazitaet.show()

    label = gtk.Label("I-Laden mA")
    vbox.pack_start(label, True, True, 0)
    label.show()
    adj = gtk.Adjustment(cfg.LADELIMIT[cfg.GEWAEHLTER_AUSGANG], \
            0.0, 9999, 25, 25, 0.0)
    sp_ladelimit = gtk.SpinButton(adj, 1.0, 0)
    sp_ladelimit.set_wrap(False)
    sp_ladelimit.set_numeric(True)
    vbox.pack_start(sp_ladelimit, False, True, 0)
    sp_ladelimit.show()

    label = gtk.Label("I-Entladen mA")
    vbox.pack_start(label, True, True, 0)
    label.show()
    adj = gtk.Adjustment(cfg.ENTLADELIMIT[cfg.GEWAEHLTER_AUSGANG], \
            0.0, 9999, 25, 25, 0.0)
    sp_entladelimit = gtk.SpinButton(adj, 1.0, 0)
    sp_entladelimit.set_wrap(False)
    sp_entladelimit.set_numeric(True)
    vbox.pack_start(sp_entladelimit, False, True, 0)

    if cfg.GEWAEHLTER_AUSGANG == 2:
        sp_entladelimit.set_sensitive(False)

    sp_entladelimit.show()

    label = gtk.Label("Menge mAh")
    vbox.pack_start(label, True, True, 0)
    label.show()
    adj = gtk.Adjustment(cfg.MENGE[cfg.GEWAEHLTER_AUSGANG], \
            0.0, 99999, 25, 25, 0.0)
    sp_menge = gtk.SpinButton(adj, 1.0, 0)
    sp_menge.set_wrap(False)
    sp_menge.set_numeric(True)
    vbox.pack_start(sp_menge, False, True, 0)
    sp_menge.show()

    label = gtk.Label("Zyklen")
    vbox.pack_start(label, True, True, 0)
    label.show()
    adj = gtk.Adjustment(cfg.ZYKLEN[cfg.GEWAEHLTER_AUSGANG], 1, 10, 1, 1, 0.0)
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

        hex_str = str(30 + cfg.GEWAEHLTER_AUSGANG) #kommando 31 or 32
        hex_str += helper.get_pos_hex(cb_atyp.get_active_text(), cfg.AKKU_TYP)
        hex_str += helper.get_pos_hex(cb_prog.get_active_text(), cfg.AMPROGRAMM)
        hex_str += helper.get_pos_hex(cb_lart.get_active_text(), cfg.LADEART)
        hex_str += \
                helper.get_pos_hex(cb_stromw.get_active_text(), cfg.STROMWAHL)

        tmp = cb_stoppm.get_active_text()
        if tmp == None: #replace lipo None need something
            tmp = cfg.STOPPMETHODE[0] #"Lademenge"
        hex_str += helper.get_pos_hex(tmp, cfg.STOPPMETHODE)

        hex_str += helper.get_16bit_hex(int(sp_anzzellen.get_value()))
        hex_str += helper.get_16bit_hex(int(sp_kapazitaet.get_value()))
        hex_str += helper.get_16bit_hex(int(sp_ladelimit.get_value()))
        hex_str += helper.get_16bit_hex(int(sp_entladelimit.get_value()))
        hex_str += helper.get_16bit_hex(int(sp_menge.get_value()))
        hex_str += helper.get_16bit_hex(int(sp_zyklen.get_value()))

        #since akkumatik is not sending this stuff from its own (yet)
        cfg.KAPAZITAET[cfg.GEWAEHLTER_AUSGANG] = int(sp_kapazitaet.get_value())
        cfg.LADELIMIT[cfg.GEWAEHLTER_AUSGANG] = int(sp_ladelimit.get_value())
        cfg.ENTLADELIMIT[cfg.GEWAEHLTER_AUSGANG] = \
                int(sp_entladelimit.get_value())
        cfg.MENGE[cfg.GEWAEHLTER_AUSGANG] = int(sp_menge.get_value())
        cfg.ZYKLEN[cfg.GEWAEHLTER_AUSGANG] = int(sp_zyklen.get_value())

        #Kommando u08 Akkutyp u08 program u08 lade_mode u08 strom_mode
        #u08 stop_mode u16 zellenzahl u16 capacity u16 i_lade u16 i_entl
        #u16 menge u16 zyklenzahl

        hex_str2 = ""
        if retval == -3: #Additionally start the thing
            if cfg.GEWAEHLTER_AUSGANG == 1:
                hex_str2 = "44"
            else:
                hex_str2 = "48"

        return (hex_str, hex_str2)

    return(None, None)
