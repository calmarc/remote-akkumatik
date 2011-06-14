# coding=utf-8
import Gnuplot, Gnuplot.funcutils
import os
import platform
import time
import shlex #command line splitting
import thread

#own import
import cfg
import helper

##########################################}}}
#GnuPlotting stuff{{{
##########################################

def filesplit(): #{{{
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

    cfg.file_block = True #Block (on read_line) while doing stuff here
    cfg.fser.close()

    if os.path.getsize(cfg.tmp_dir + '/serial-akkumatik.dat') < 10:
        cfg.fser = helper.open_file(cfg.tmp_dir + '/serial-akkumatik.dat', 'ab') #reopen (append) and return
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
                fh1 = helper.open_file(fname, "w+b")

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
                fh2 = helper.open_file(fname, "w+b")

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
        fh1 = helper.open_file(fname, "w+b")

        if platform.system() == "Windows":
            ausgang1_part = ausgang1_part.replace('\xff', " ")

        fh1.write(ausgang1_part)
        fh1.close()
        print "Generated:  " + "%48s" % (fname[-47:])
    if len(ausgang2_part) > 0:
        fname = cfg.tmp_dir + '/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
        fh2 = helper.open_file(fname, "w+b")

        if platform.system() == "Windows":
            ausgang2_part = ausgang2_part.replace('\xff', " ")

        fh2.write(ausgang2_part)
        print "Generated:  " + "%48s" % (fname[-47:])

#}}}

def lipo_gnuplot(line_a, rangeval, anz_z): #{{{

    """lipo gnuplot 2nd chart"""
    gpst = ""

    gpst += 'set nolabel;\n'
    gpst += 'set ytics nomirror;\n'
    gpst += 'set ylabel "mVolt Zellen (Avg)"\n'
    gpst += 'set yrange [2992:4208];\n'

    #gpst += 'set autoscale {y{|min|max|fixmin|fixmax|fix} | fix | keepfix}

    if rangeval != -1:
        gpst += 'set y2range ['+str(-1*rangeval)+':'+str(rangeval)+'];\n'
        gpst += 'set y2label "Balancer ∆";\n'
        gpst += 'set y2tics 4;\n'
        gpst += 'set my2tics 4;\n'

        gpst += "plot "

        avg_string = "("
        x = 0
        for i in range(18, len(line_a) - 1):
            avg_string += "$"+str(i+1)+"+"
            x += 1
        avg_string = avg_string[0:-1] + ")/" + str(x)

        gpst += 'wfile using 2:('+avg_string+') with lines title "mV (avg)" lw 2 lc rgbcolor "#cc3333" '

        for i in range(18, len(line_a) - 1):
            gpst += ', wfile using 2:($'+str(i+1)+'-'+ str(avg_string)+') smooth bezier with lines title "∆ '+str(i-17)+'" axes x1y2 lw 1 lc rgbcolor "#'+cfg.LIPORGB[i-18]+'"'
        gpst += ';'
    else:
        string = 'mV (avg)'
        if anz_z == -1:
            gpst += 'set yrange [0:*];\n'
            gpst += 'set ylabel "mVolt Zellen"\n'
            anz_z = 1
            string = 'mVolt'

        gpst += 'plot wfile using 2:($3/'+str(anz_z)+') with lines title "'+string+'" lw 2 lc rgbcolor "#cc3333" '

    return (gpst)

#}}}

def else_gnuplot(): #{{{

    """other than lipo gnuplot 2nd chart"""

    gpst = ""

    gpst +=  'set ylabel "mVolt Pro Zelle (Avg. von '+str(cfg.anzahl_zellen[cfg.gewaehlter_ausgang])+' Zellen)"\n'
    gpst +=  'set yrange [*:*];\n'
    gpst +=  'set ytics nomirror;\n'

    #gpst += 'set y2range [*:*];\n'
    #gpst += 'set y2label "Innerer Widerstand Ri (mOhm)";\n'
    #gpst += 'set y2tics border;\n'

    gpst += 'plot wfile using 2:3 with lines title "mVolt" lw 2 lc rgbcolor "#ff0000";'
    return gpst

#}}}

def nixx_gnuplot(): #{{{

    """NiCd and NiMH gnuplot 2nd chart"""

    gpst = ""

    gpst +=  'set ylabel "mVolt Pro Zelle (Avg. von '+str(cfg.anzahl_zellen[cfg.gewaehlter_ausgang])+' Zellen)"\n'
    gpst +=  'set ytics nomirror;\n'

    gpst += 'set y2range [*:*];\n'
    gpst += 'set y2label "Innerer Widerstand Ri (mOhm)";\n'
    gpst += 'set y2tics border;\n'

    if cfg.anzahl_zellen[cfg.gewaehlter_ausgang] == 0: #e.g on restarts + anz-zellen >=50 (errorstuff)
        gpst +=  'set yrange [*:*];\n'
        divisor = "1"
    else:
        gpst +=  'set yrange [600:1899];\n'
        divisor = str(cfg.anzahl_zellen[cfg.gewaehlter_ausgang])

    gpst += 'plot wfile using 2:($3/'+divisor+') with lines title "mVolt" lw 2 lc rgbcolor "#ff0000", \
                wfile using 2:7 with lines title "mOhm" axes x1y2 lw 1 lc rgbcolor "#000044";'
    return gpst

#}}}

def get_balancer_range(f): #{{{

    bmin = 0
    bmax = 0
    rangeval = 0
    for  l in f.readlines():
        if l[0] == "#":
            continue

        line_a = l.split("\xff")
        avg = 0
        div = 0.0
        for i in range(18, len(line_a) - 1): #average
            avg += long(line_a[i])
            div += 1

        if div > 0.0:
            avg /= float(div)
        else:
            continue


        index=17
        for val in line_a[18:-1]: # get min and max
            index += 1
            if (long(val) - avg) < bmin:
                bmin = long(val) - avg
            elif (long(val) - avg) > bmax:
                bmax = long(val) - avg

        if abs(bmin) > bmax: # get higher of limits
            rangeval = abs(bmin)
        else:
            rangeval = bmax

    if rangeval < 12:  # set range-limit minimum to 12
        rangeval = 12
    return rangeval

#}}}

def gnuplot(): #{{{
    """Create charts"""

    filesplit() #delete and generate new .dat files

    g = Gnuplot.Gnuplot(debug=0)

    qiv_files = ""
    dirList=os.listdir(cfg.tmp_dir)
    dirList.sort()
    print "\n* [Gnu-Plotting] ****************************************************"
    for fname in dirList:
        if fname[0:4] == "Akku" and fname[4:6] == str(cfg.gewaehlter_ausgang) + "-" and fname [8:12] == ".dat":
            qiv_files += cfg.chart_dir + "/" + fname[:-4] + ".png "

            f = helper.open_file(cfg.tmp_dir + "/" + fname, "r")
            while True: #ignore other than real data lines
                l = f.readline()
                if l[0] != "#":
                    break
            f.close()
            if platform.system() == "Windows":
                line_a = l.split(" ")
            else:
                line_a = l.split("\xff")

            phasenr = long(line_a[9])
            atyp_i = long(line_a[12])

            #titel stuff
            atyp_str = cfg.AKKU_TYP[long(line_a[12])] #Akkutyp
            prg_str = cfg.AMPROGRAMM[long(line_a[13])] #Programm
            lart_str = cfg.LADEART[long(line_a[14])] #Ladeart
            stromw_str = cfg.STROMWAHL[long(line_a[15])] #stromwahl
            stoppm_str = cfg.STOPPMETHODE[long(line_a[16])] #stromwahl
            #Stop >= 50?
            anz_zellen = long(line_a[8]) #Zellenzahl / bei Stop -> 'Fehlercode'
            anz_z = anz_zellen
            if anz_zellen >= 40: # not really needed there in the title anyway.
                anz_z_str = ""
                anz_z = -1 #unknown
            else:
                anz_z_str = str(anz_zellen) + "x"

            titel_plus = " ["+anz_z_str+atyp_str+", "+prg_str+", "+lart_str+", "+stromw_str+", "+stoppm_str+"] - "
            titel_little = " ["+anz_z_str+atyp_str+"] - "

            rangeval = -1 # stays like that when no balancer attached
            if atyp_i == 5 and len(line_a) > 19: #lipo -> Balancer graph TODO what when no balancer?
                f = helper.open_file(cfg.tmp_dir + "/" + fname, "r")
                rangeval = get_balancer_range(f)
                f.close()

            if phasenr >= 1 and phasenr <= 5:
                titel = "LADEN" + titel_plus
                g('set yrange [0:*];')
            elif phasenr >= 7 and phasenr < 9:
                titel = "ENTLADEN" + titel_little
                g('set yrange [*:0];')
            elif phasenr == 10:
                titel = "PAUSE - Entladespannung erreicht" + titel_little
                g('set yrange [*:*];')
            elif phasenr == 0:
                titel = "STOP (Erhaltungladung)" + titel_plus
                g('set yrange [*:*];')
            else:
                titel = "Unbekannte Phase <"+str(phasenr)+">" + titel_plus
                g('set yrange [*:*];')

            g('set terminal png size 1280, 1024;')
            #gnuplot does not like MS-Windoof's \
            g('set output "' + (cfg.chart_dir).replace('\\','/') + "/" + fname[:-4] + '.png"')

            g('set xdata time;')

            if platform.system() == "Windows":
                g("set datafile separator ' ';")
            else:
                g("set datafile separator '\xff';")

            g('set timefmt "%H:%M:%S";')
            g('set grid')

            #set bmargin 5
            g('set lmargin 10')
            g('set rmargin 10')
            #set tmargin 5

            g('set multiplot;')

            g('set key box')
            g('set ylabel "Laden mA / Kapazitaet mAh"')
            g('set ytics nomirror;')

            g('set y2range [-10:70];')
            g('set y2label "Grad Celsius";')
            g('set y2tics border;')

            g('set nolabel;')
            g('set xtics axis;')

            g('set size 1.0,0.45;')
            g('set origin 0.0,0.5;')


            #gnuplot does not like MS-Windoof's \
            g('wfile="' + cfg.tmp_dir.replace('\\', '/') + "/" + fname + '";')
            g('set title "Akkumatik - ' + titel + ' (' + fname + ')";')


            g('plot \
                wfile using 2:4 with lines title "mA" lw 2 lc rgbcolor "#009900" , \
                wfile using 2:5 smooth bezier with lines title "mAh" lw 2 lc rgbcolor "#0000ff", \
                wfile using 2:8 smooth bezier with lines title "Bat C" axes x1y2 lc rgbcolor "#cc0000" , \
                wfile using 2:18 smooth bezier with lines title "KK C" axes x1y2 lc rgbcolor "#222222";')


            g('set nolabel;')
            g('set notitle;')

            g('set size 1.0,0.45;')
            g('set origin 0.0,0.0;')

            if atyp_i == 5:
                g(lipo_gnuplot(line_a, rangeval, anz_z))
            elif atyp_i == 0 or atyp_i == 1:
                g(nixx_gnuplot())
            else:
                g(else_gnuplot())

            g('set nomultiplot;')
            g('reset')
            print "Generated:  "+"%44s"%(cfg.chart_dir + "/" +fname[-27:-4])+".png"
        else:
            continue

    if len(qiv_files) > 0:
        time.sleep(1.8) #sonst finded qiv (noch) nichts allenfalls
        args = shlex.split(qiv_files)
        arguments = ' '.join(str(n) for n in args)
        if platform.system() == "Windows":
            for x in args:
                # os.startfile(x)
                thread.start_new_thread(os.startfile,(x,))
                break #one is enough for eg. irfanview
        else:
            thread.start_new_thread(os.system,(cfg.picture_exe+' '+arguments,))

#}}}

