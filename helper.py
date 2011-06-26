# coding=utf-8
# Copyright (c) 2010, Marco Candrian
""" Helper/Utility stuff """

import sys
import thread
import time
import serial
import gtk

#own import
import cfg

def open_file(file_name, mode):
    """Open a file."""

    try:
        the_file = open(file_name, mode)
    except(IOError), err:
        tmp = "Unable to open the file " + file_name + '\n'
        tmp += str(err) + '\n'
        tmp += "Ending program.\n"
        print (tmp)
        sys.exit()
    else:
        return the_file


#command stuff
def get_pos_hex(string, konst_arr):
    """ hm """

    position = konst_arr.index(string)
    string = "%02x" % (position)
    #Well, just return %02i would work too on values <10
    final_str = ""
    for item in string:
        final_str += chr(int("30", 16) + int(item, 16))
    return final_str

def get_16bit_hex(integer):
    """ calculate the stuff Akkumatik wants """
    #integer to hex
    string = "%04x" % (integer)
    #switch around hi and low byte
    string = string[2:] + string[0:2]
    # add 0x30 (48) to those hex-digits and add that finally to the string
    final_str = ""
    for item in string:
        final_str += chr(int("30", 16) + int(item, 16))
    return final_str

#command sending (queued in thread (quasi (TODO) at least))
def akkumatik_command(string, what):
    """ Send a Command to the Akkumatik """

    #TODO tname possibly last of str_tuple..
    def command_thread(tname, str_tuple): #{{{
        """ thread each single command """

        (com_str, what) = str_tuple
        #TODO make it how it *should be* instead of that here...
        cfg.THREADLOCK.acquire()

        if cfg.COMMAND_ABORT == True: #skip on further soon to arrive commands
            cfg.THREADLOCK.release()
            return

        cfg.COMMAND_WAIT = True
        try:
            cfg.SER.write(com_str)
        except serial.SerialException, err:
            tmp = "%s" % err
            tmp += ":" + com_str + ", "+ what
            print (tmp)
            cfg.FLOG.write(tmp)
            gtk_stuff.message_dialog(None, tmp)

        okk = False
        i = 0
        #Status
        label_txt = "[%s]: " % (what)
        cfg.LABEL_STATUS.show()
        cfg.LABEL_STATUS.set_text(label_txt)
        while gtk.events_pending():
            gtk.main_iteration()
        while i < 49:
            time.sleep(0.1)
            label_txt += "."
            cfg.LABEL_STATUS.set_text(label_txt)
            while gtk.events_pending():
                gtk.main_iteration()
            i += 1
            #put on True before sending. - here waiting for False
            if cfg.COMMAND_WAIT == False:
                okk = True
                #Status
                label_txt += " OK"
                cfg.EVENT_BOX_LSTATUS.modify_bg(gtk.STATE_NORMAL, \
                        cfg.EVENT_BOX_LSTATUS.get_colormap().alloc_color("#66cc66"))
                cfg.LABEL_STATUS.set_text(label_txt)
                while gtk.events_pending():
                    gtk.main_iteration()
                time.sleep(2.0)
                break

        if okk == False:
            cfg.COMMAND_ABORT = True #skip on further soon to arrive commands
            #Status
            cfg.EVENT_BOX_LSTATUS.modify_bg(gtk.STATE_NORMAL, \
                    cfg.EVENT_BOX_LSTATUS.get_colormap().alloc_color("#cc6666"))
            label_txt += " Failed"
            cfg.LABEL_STATUS.set_text(label_txt)
            while gtk.events_pending():
                gtk.main_iteration()
            time.sleep(2.0)
        cfg.THREADLOCK.release()

        cfg.EVENT_BOX_LSTATUS.modify_bg(gtk.STATE_NORMAL, \
                cfg.EVENT_BOX_LSTATUS.get_colormap().alloc_color("#cccccc"))
        cfg.LABEL_STATUS.hide()

    #}}}

    checksum = 2
    for item in string:
        checksum ^= ord(item)

    checksum ^= 64 #dummy checksum byte itself to checksum...

    #try:
    thread.start_new_thread(command_thread, (what, (chr(2) + string +\
            chr(checksum) + chr(3), what)))
    #except:
    #    print "Error: unable to start thread"

# vim: set nosi ai ts=8 et shiftwidth=4 sts=4 fdm=marker foldnestmax=1 :
