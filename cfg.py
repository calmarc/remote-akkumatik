# well... actually - all around variables (also knows an 'globals' shrug)
 
##########################################
#Konstanten

AKKU_TYP = ["NiCd", "NiMH", "Blei", "Bgel", "LiIo", "LiPo", "LiFe", "Uixx"]
AMPROGRAMM = ["Laden", "Entladen", "E+L", "L+E", "(L)E+L", "(E)L+E", "Sender", "Lagern"]
LADEART = ["Konst", "Puls", "Reflex", "LiPo Fast"]
STROMWAHL = ["Auto", "Limit", "Fest", "Ext. Wiederstand"]
STOPPMETHODE = ["Lademenge", "Gradient", "Delta-Peak-1", "Delta-Peak-2", "Delta-Peak-3"]
FEHLERCODE = [ "Akku Stop", "Akku Voll", "Akku Leer", "", "Fehler Timeout", "Fehler Lade-Menge", "Fehler Akku zu Heiss", "Fehler Versorgungsspannung", "Fehler Akkuspannung", "Fehler Zellenspannung", "Fehler Alarmeingang", "Fehler Stromregler", "Fehler Polung/Kurzschluss", "Fehler Regelfenster", "Fehler Messfenster", "Fehler Temperatur", "Fehler Tempsens", "Fehler Hardware"]
LIPORGB = ["3399ff", "55ff00", "ff9922", "3311cc", "123456", "ff0000", "3388cc", "cc8833", "88cc33", "ffff00", "ff00ff", "00ffff"]

# wird ueberschrieben vom laufenden programm
# item 0 is bogus and not used - only 1 and 2 (Ausgaenge)
#
atyp = [0,0,0]
prg = [0,0,0]
lart = [0,0,0]
stromw = [0,0,0]
stoppm = [0,0,0]
# gespeichert vom dialog
kapazitaet =  [0,0,0]
ladelimit =  [0,0,0]
entladelimit =  [0,0,0]
menge =  [0,0,0]
zyklen =  [0,0,0]
anzahl_zellen = [0,0,0] # defautls to 0 (on restarts + errorcode (>=50)

# while scanning the serial data to compare..
oldtime = ["", "", ""]

# which output is selected
gewaehlter_ausgang = 1

# some helper Flags
file_block = False
command_wait = False # threads are waiting when True on command acknowledge text
command_abort = False #indicates missed commands - skip next ones

# thread helper thing
threadlock = None

#path stuff
exe_dir = ""
picture_exe = ""
tmp_dir = ""
chart_dir = ""

#main gtk windows
gtk_window = None


#serial connection and file to write it
serial_port = ""
ser = None
fser = None
