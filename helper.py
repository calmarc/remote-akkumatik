# coding=utf-8
#
import sys
import thread
import time

#own import
import cfg

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


#command stuff
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

#command sending (queued in thread (quasi (TODO) at least))
def akkumatik_command(string, what):

    def command_thread(tname, str_tuple): #{{{
        
        (com_str, what) = str_tuple
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
        sys.stdout.write("Waiting for Command <%s> Ack: " % (what))
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

    checksum = 2
    for x in string:
        checksum ^= ord(x)

    checksum ^= 64 #dummy checksum byte itself to checksum...

    #try:
    #thread.start_new_thread(command_thread, ("Issue_Command", chr(2) + string + chr(checksum) + chr(3), cfg.threadlock, cfg.ser))
    thread.start_new_thread(command_thread, ("Issue_Command", (chr(2) + string + chr(checksum) + chr(3), what)))
    #except:
    #    print "Error: unable to start thread"

