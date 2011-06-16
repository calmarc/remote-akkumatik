# coding=utf-8
""" Config (globals... *shrug*) stuff """

##########################################
#Konstanten

AKKU_TYP = ["NiCd", "NiMH", "Blei", "Bgel", "LiIo", "LiPo", "LiFe", "Uixx"]
AMPROGRAMM = ["Laden", "Entladen", "E+L", "L+E", "(L)E+L", \
        "(E)L+E", "Sender", "Lagern"]
LADEART = ["Konst", "Puls", "Reflex", "LiPo Fast"]
STROMWAHL = ["Auto", "Limit", "Fest", "Ext. Wiederstand"]
STOPPMETHODE = ["Lademenge", "Gradient", "Delta-Peak-1", "Delta-Peak-2", \
        "Delta-Peak-3"]
FEHLERCODE = [ "Akku Stop", "Akku Voll", "Akku Leer", "", "Fehler Timeout", \
        "Fehler Lade-Menge", "Fehler Akku zu Heiss", \
        "Fehler Versorgungsspannung", "Fehler Akkuspannung", \
        "Fehler Zellenspannung", "Fehler Alarmeingang", "Fehler Stromregler", \
        "Fehler Polung/Kurzschluss", "Fehler Regelfenster", \
        "Fehler Messfenster", "Fehler Temperatur", "Fehler Tempsens", \
        "Fehler Hardware"]
LIPORGB = ["3399ff", "55ff00", "ff9922", "3311cc", "123456", "ff0000", \
        "3388cc", "cc8833", "88cc33", "ffff00", "ff00ff", "00ffff"]

# wird ueberschrieben vom laufenden programm
# item 0 is bogus and not used - only 1 and 2 (Ausgaenge)
#
ATYP = [0, 0, 0]
PRG = [0, 0, 0]
LART = [0, 0, 0]
STROMW = [0, 0, 0]
STOPPM = [0, 0, 0]

# gespeichert vom dialog
KAPAZITAET = [0, 0, 0]
LADELIMIT = [0, 0, 0]
ENTLADELIMIT = [0, 0, 0]
MENGE = [0, 0, 0]
ZYKLEN = [0, 0, 0]
ANZAHL_ZELLEN = [0, 0, 0] # defautls to 0 (on restarts + errorcode (>=50)

# while scanning the serial data to compare..
OLDTIME = ["", "", ""]

# which output is selected
GEWAEHLTER_AUSGANG = 1

# some helper Flags
FILE_BLOCK = False
# threads are waiting when True on command acknowledge text
COMMAND_WAIT = False
COMMAND_ABORT = False #indicates missed commands - skip next ones

# thread helper thing
THREADLOCK = None

#path stuff
EXE_DIR = ""
PICTURE_EXE = ""
TMP_DIR = ""
CHART_DIR = ""

#main gtk windows
GTK_WINDOW = None
# could be transfered from main-window to read_line.. together with labels..
BUTTON_START = None
BUTTON_STOP = None
LABEL_STATUS = None
EVENT_BOX_LSTATUS = None

#serial connection and file to write it
SERIAL_PORT = ""
SER = None
FSER = None
