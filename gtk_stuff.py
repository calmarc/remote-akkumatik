# coding=utf-8

import pygtk
pygtk.require('2.0')
import gtk
import pango
import gobject

import os

#own import
import cfg
import helper

#
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
        fh = helper.open_file(cfg.exe_dir + "/liste_akkus.dat", "wb")
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
            fh = helper.open_file(cfg.exe_dir + "/liste_akkus.dat", "rb")
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
    return retval
