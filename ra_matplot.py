import matplotlib.pyplot as plt

#own import
import cfg
import helper

#def matplot():
    #plt.plot([1,2,3,4])
    #plt.ylabel('some numbers')
    #plt.show()

##########################################}}}
#Matplot stuff{{{
##########################################

def matplot():
    def hms_formatter(value, loc):
        h = value // 3600        
        m = (value - h * 3600) // 60
        s = value % 60              
        return "%02d:%02d:%02d" % (h,m,s)

    def to_sec(tstring):
        return int(tstring[:2])*3600 + int(tstring[3:5])*60 + int(tstring[6:8])

    qiv_files = ""
    dirList = os.listdir(cfg.tmp_dir)
    dirList.sort()
    print "\n* [Mat-Plotting] ****************************************************"

    ip = 0
    for fname in dirList:
        if fname[0:4] == "Akku" and fname[4:6] == str(cfg..gewaehlter_ausgang) + "-" and fname [8:12] == ".dat":
            qiv_files += cfg.chart_dir + "/" + fname[:-4] + ".png "

            f = helper.open_file(cfg.tmp_dir + "/" + fname, "r")
            while True: #ignore other than real data lines
                l = f.readline()
                break

            f.close()
            if platform.system() == "Windows":
                line_a = l.split(" ")
            else:
                line_a = l.split("\xff")

            phasenr = long(line_a[9])
            atyp = long(line_a[12])

            #titel stuff
            atyp_str = cfg.AKKU_TYP[long(line_a[12])] #Akkutyp
            prg = cfg.AMPROGRAMM[long(line_a[13])] #Programm
            lart = cfg.LADEART[long(line_a[14])] #Ladeart
            stromw = cfg.STROMWAHL[long(line_a[15])] #stromwahl
            stoppm = cfg.STOPPMETHODE[long(line_a[16])] #stromwahl
            #Stop >= 50?
            anz_zellen = long(line_a[8]) #Zellenzahl / bei Stop -> 'Fehlercode'
            if anz_zellen >= 40: # not really needed there in the title anyway.
                anz_z_str = ""
            else:
                anz_z_str = str(anz_zellen) + "x"

            titel_plus = " ["+anz_z_str+atyp_str+", "+prg+", "+lart+", "+stromw+", "+stoppm+"] - "
            titel_little = " ["+anz_z_str+atyp_str+"] - "

            #if atyp == 5 and len(line_a) > 19: #lipo -> Balancer graph TODO what when no balancer?
                #f = cfg.open_file(cfg.tmp_dir + "/" + fname, "r")
                #rangeval = cfg.get_balancer_range(f)
                #f.close()

            if phasenr >= 1 and phasenr <= 5:
                titel = "LADEN" + titel_plus
            elif phasenr >= 7 and phasenr < 9:
                titel = "ENTLADEN" + titel_little
            elif phasenr == 10:
                titel = "PAUSE - Entladespannung erreicht" + titel_little
            elif phasenr == 0:
                titel = "STOP (Erhaltungladung)" + titel_plus
            else:
                titel = "Unbekannte Phase <"+str(phasenr)+">" + titel_plus

            # file to array
            fh  = cfg.open_file(cfg.tmp_dir + "/" + fname, "r")
            total_a = []
            for thing in fh.readlines():
                if platform.system() == "Windows":
                    hm = thing.split(" ")
                else:
                    hm = thing.split("\xff")
                total_a.append(hm)
        #break
    
            t = []
            y = []
            y2 = []
            for val in total_a:
                t.append(to_sec(val[1]))
                y.append(int(val[2]))
                y2.append(int(val[3]))

            fig = plt.figure(ip)

            sp1 = fig.add_subplot(211)
            xaxis = sp1.get_xaxis()
            xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(hms_formatter))
            sp1.plot(t, y)

            sp2 = fig.add_subplot(212)
            xaxis2 = sp2.get_xaxis()
            xaxis2.set_major_formatter(matplotlib.ticker.FuncFormatter(hms_formatter))
            sp2.plot(t, y2)

            fig.canvas.draw()
            fig.show()
            ip += 1
