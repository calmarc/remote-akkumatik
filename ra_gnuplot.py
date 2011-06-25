# coding=utf-8
# Copyright (c) 2010, Marco Candrian
""" print charts via gnuplot """

import Gnuplot, Gnuplot.funcutils
import os
import platform
import time
import shlex #command line splitting
import thread

#own import
import cfg
import helper
import gtk_stuff

##########################################}}}
#GnuPlotting stuff{{{
##########################################

def filesplit(): #{{{
    """Create files for gnuplot"""

    line_counter2 = 0
    file_zaehler1 = 1
    file_zaehler2 = 1
    ausgang1_part = ""
    ausgang2_part = ""
    current_time1 = 0
    previous_time1 = 0

    tmp = "\n* [Serial Splitting] ********************************************"
    print (tmp)
    cfg.FLOG.write(tmp + '\n')

    for fil in os.listdir(cfg.TMP_DIR):
        if len(fil) == 12 and fil[0:4] == "Akku":
            os.remove(cfg.TMP_DIR + "/" + fil)

    cfg.FILE_BLOCK = True #Block (on read_line) while doing stuff here
    cfg.FSER.close()

    if os.path.getsize(cfg.TMP_DIR + '/serial-akkumatik.dat') < 10:
        #reopen (append) and return
        cfg.FSER = helper.open_file(cfg.TMP_DIR+'/serial-akkumatik.dat', 'ab')
        tmp = "Not sufficient Serial Data avaiable"
        print (tmp)
        cfg.FLOG.write(tmp + '\n')
        cfg.FILE_BLOCK = False
        gtk_stuff.message_dialog(cfg.GTK_WINDOW, tmp)
        return

    cfg.FSER = helper.open_file(cfg.TMP_DIR + '/serial-akkumatik.dat', 'rb')

    for line in cfg.FSER.readlines(): #get all lines in one step
        if cfg.FILE_BLOCK == True:
            cfg.FSER.close()
            #reopen
            cfg.FSER = helper.open_file(cfg.TMP_DIR+'/serial-akkumatik.dat', \
                    'ab')
            cfg.FILE_BLOCK = False #allow further getting serial adding..

        if line[0:1] == "1":

            current_time1 = int(line[2:4]) * 60 + int(line[5:7]) * 60 +\
                    int(line[8:10]) #in seconds


            if current_time1 < previous_time1:
                fname = cfg.TMP_DIR+'/Akku1-'+ "%02i" % (file_zaehler1)+'.dat'
                fh1 = helper.open_file(fname, "w+b")

                if platform.system() == "Windows":
                    ausgang1_part = ausgang1_part.replace('\xff', " ")

                fh1.write(ausgang1_part)
                fh1.close()

                tmp = "Generated:  " + "%48s" % (fname[-47:])
                print (tmp)
                cfg.FLOG.write(tmp + '\n')

                cfg.FILE_BLOCK = False
                file_zaehler1 += 1
                ausgang1_part = line
            else:
                ausgang1_part += line

            previous_time1 = current_time1

        elif line[0:1] == "2": #"2"

            #current_time2 = int(line[2:4]) * 60 + int(line[5:7])\
            #        * 60 + int(line[8:10]) #in seconds

            line_counter2 += 1
            #only write when did not just begun
            if line[2:10] == "00:00:01" and line_counter2 > 1:
                fname = cfg.TMP_DIR+'/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
                fh2 = helper.open_file(fname, "w+b")

                if platform.system() == "Windows":
                    ausgang2_part = ausgang2_part.replace('\xff', " ")

                fh2.write(ausgang2_part)
                fh2.close()
                tmp = "Generated:  " + "%48s" % (fname[-47:])
                print (tmp)
                cfg.FLOG.write(tmp + '\n')

                file_zaehler2 += 1
                ausgang2_part = line
                line_counter2 = 0
            else:
                ausgang2_part += line

        else:
            tmp = "\n= [Spez Line...] ========================================"
            tmp += "SPEZ: " + line
            print (tmp)
            cfg.FLOG.write(tmp + '\n')

    if len(ausgang1_part) > 0:
        fname = cfg.TMP_DIR + '/Akku1-'+ "%02i" % (file_zaehler1)+'.dat'
        fh1 = helper.open_file(fname, "w+b")

        if platform.system() == "Windows":
            ausgang1_part = ausgang1_part.replace('\xff', " ")

        fh1.write(ausgang1_part)
        fh1.close()
        tmp = "Generated:  " + "%48s" % (fname[-47:])
        print (tmp)
        cfg.FLOG.write(tmp + '\n')
    if len(ausgang2_part) > 0:
        fname = cfg.TMP_DIR + '/Akku2-'+ "%02i" % (file_zaehler2)+'.dat'
        fh2 = helper.open_file(fname, "w+b")

        if platform.system() == "Windows":
            ausgang2_part = ausgang2_part.replace('\xff', " ")

        fh2.write(ausgang2_part)
        tmp = "Generated:  " + "%48s" % (fname[-47:])
        print (tmp)
        cfg.FLOG.write(tmp + '\n')

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
        xtmp = 0
        for i in range(18, len(line_a) - 1):
            avg_string += "$"+str(i+1)+"+"
            xtmp += 1
        avg_string = avg_string[0:-1] + ")/" + str(xtmp)

        gpst += 'wfile using 2:('+avg_string+') with lines title "mV (avg)"\
                lw 2 lc rgbcolor "#cc3333" '

        for i in range(18, len(line_a) - 1):
            gpst += ', wfile using 2:($'+str(i+1)+'-'+ str(avg_string)+')\
                    smooth bezier with lines title "∆ '+str(i-17)+'"\
                    axes x1y2 lw 1 lc rgbcolor "#'+cfg.LIPORGB[i-18]+'"'
        gpst += ';'
    else:
        string = 'mV (avg)'
        if anz_z == -1:
            gpst += 'set yrange [0:*];\n'
            gpst += 'set ylabel "mVolt Zellen"\n'
            anz_z = 1
            string = 'mVolt'

        gpst += 'plot wfile using 2:($3/'+str(anz_z)+') with lines\
                title "'+string+'" lw 2 lc rgbcolor "#cc3333" '

    return (gpst)

#}}}

def else_gnuplot(): #{{{
    """other than lipo gnuplot 2nd chart"""

    gpst = ""

    gpst +=  'set ylabel "mVolt Pro Zelle (Avg. von '+\
            str(cfg.ANZAHL_ZELLEN[cfg.GEWAEHLTER_AUSGANG])+' Zellen)"\n'
    gpst +=  'set yrange [*:*];\n'
    gpst +=  'set ytics nomirror;\n'

    #gpst += 'set y2range [*:*];\n'
    #gpst += 'set y2label "Innerer Widerstand Ri (mOhm)";\n'
    #gpst += 'set y2tics border;\n'

    gpst += 'plot wfile using 2:3 with lines title "mVolt"\
            lw 2 lc rgbcolor "#ff0000";'
    return gpst

#}}}

def nixx_gnuplot(): #{{{
    """NiCd and NiMH gnuplot 2nd chart"""

    gpst = ""

    gpst +=  'set ylabel "mVolt Pro Zelle (Avg. von '+\
            str(cfg.ANZAHL_ZELLEN[cfg.GEWAEHLTER_AUSGANG])+' Zellen)"\n'
    gpst +=  'set ytics nomirror;\n'

    gpst += 'set y2range [*:*];\n'
    gpst += 'set y2label "Innerer Widerstand Ri (mOhm)";\n'
    gpst += 'set y2tics border;\n'

    #e.g on restarts + anz-zellen >=50 (errorstuff)
    if cfg.ANZAHL_ZELLEN[cfg.GEWAEHLTER_AUSGANG] == 0:
        gpst +=  'set yrange [*:*];\n'
        divisor = "1"
    else:
        gpst +=  'set yrange [600:1899];\n'
        divisor = str(cfg.ANZAHL_ZELLEN[cfg.GEWAEHLTER_AUSGANG])

    gpst += 'plot wfile using 2:($3/'+divisor+') with lines title "mVolt"\
           lw 2 lc rgbcolor "#ff0000", wfile using 2:7 with lines title "mOhm"\
            axes x1y2 lw 1 lc rgbcolor "#000044";'
    return gpst

#}}}

def get_balancer_range(fhan): #{{{
    """ calculate balancer range max-min """

    bmin = 0
    bmax = 0
    rangeval = 0
    for  ltmp in fhan.readlines():
        if ltmp[0] == "#":
            continue

        line_a = ltmp.split("\xff")
        avg = 0
        div = 0.0
        for i in range(18, len(line_a) - 1): #average
            avg += int(line_a[i])
            div += 1

        if div > 0.0:
            avg /= float(div)
        else:
            continue


        for val in line_a[18:-1]: # get min and max
            if (int(val) - avg) < bmin:
                bmin = int(val) - avg
            elif (int(val) - avg) > bmax:
                bmax = int(val) - avg

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

    gpl = Gnuplot.Gnuplot(debug=0)

    qiv_files = ""
    dir_list = os.listdir(cfg.TMP_DIR)
    dir_list.sort()
    tmp = "\n* [Gnu-Plotting] ************************************************"
    print (tmp)
    cfg.FLOG.write(tmp + '\n')

    for fname in dir_list:
        if fname[0:4] == "Akku" and fname[4:6] == str(cfg.GEWAEHLTER_AUSGANG)+\
                "-" and fname [8:12] == ".dat":
            qiv_files += cfg.CHART_DIR + "/" + fname[:-4] + ".png "

            fhan = helper.open_file(cfg.TMP_DIR + "/" + fname, "r")
            while True: #ignore other than real data lines
                lin = fhan.readline()
                if lin[0] != "#":
                    break
            fhan.close()
            if platform.system() == "Windows":
                line_a = lin.split(" ")
            else:
                line_a = lin.split("\xff")

            phasenr = int(line_a[9])
            atyp_i = int(line_a[12])

            #titel stuff
            atyp_str = cfg.AKKU_TYP[int(line_a[12])] #Akkutyp
            prg_str = cfg.AMPROGRAMM[int(line_a[13])] #Programm
            lart_str = cfg.LADEART[int(line_a[14])] #Ladeart
            stromw_str = cfg.STROMWAHL[int(line_a[15])] #stromwahl
            stoppm_str = cfg.STOPPMETHODE[int(line_a[16])] #stromwahl
            #Stop >= 50?
            anz_zellen = int(line_a[8]) #Zellenzahl / bei Stop -> 'Fehlercode'
            anz_z = anz_zellen
            if anz_zellen >= 40: # not really needed there in the title anyway.
                anz_z_str = ""
                anz_z = -1 #unknown
            else:
                anz_z_str = str(anz_zellen) + "x"

            titel_plus = " ["+anz_z_str+atyp_str+", "+prg_str+", "+lart_str+", " \
                    +stromw_str+", "+stoppm_str+"] - "
            titel_little = " ["+anz_z_str+atyp_str+"] - "

            rangeval = -1 # stays like that when no balancer attached
            #lipo -> Balancer graph TODO what when no balancer?
            if atyp_i == 5 and len(line_a) > 19:
                fhan = helper.open_file(cfg.TMP_DIR + "/" + fname, "r")
                rangeval = get_balancer_range(fhan)
                fhan.close()

            if phasenr >= 1 and phasenr <= 5:
                titel = "LADEN" + titel_plus
                gpl('set yrange [0:*];')
            elif phasenr >= 7 and phasenr < 9:
                titel = "ENTLADEN" + titel_little
                gpl('set yrange [*:0];')
            elif phasenr == 10:
                titel = "PAUSE - Entladespannung erreicht" + titel_little
                gpl('set yrange [*:*];')
            elif phasenr == 0:
                titel = "STOP (Erhaltungladung)" + titel_plus
                gpl('set yrange [*:*];')
            else:
                titel = "Unbekannte Phase <"+str(phasenr)+">" + titel_plus
                gpl('set yrange [*:*];')

            gpl('set terminal png size 1280, 1024;')
            #gnuplot does not like MS-Windoof's \
            gpl('set output "' + (cfg.CHART_DIR).replace('\\','/') +\
            "/" + fname[:-4] + '.png"')

            gpl('set xdata time;')

            if platform.system() == "Windows":
                gpl("set datafile separator ' ';")
            else:
                gpl("set datafile separator '\xff';")

            gpl('set timefmt "%H:%M:%S";')
            gpl('set grid')

            #set bmargin 5
            gpl('set lmargin 10')
            gpl('set rmargin 10')
            #set tmargin 5

            gpl('set multiplot;')

            gpl('set key box')
            gpl('set ylabel "Laden mA / Kapazitaet mAh"')
            gpl('set ytics nomirror;')

            gpl('set y2range [-10:70];')
            gpl('set y2label "Grad Celsius";')
            gpl('set y2tics border;')

            gpl('set nolabel;')
            gpl('set xtics axis;')

            gpl('set size 1.0,0.45;')
            gpl('set origin 0.0,0.5;')


            #gnuplot does not like MS-Windoof's \
            gpl('wfile="' + cfg.TMP_DIR.replace('\\', '/') + "/" + fname + '";')
            gpl('set title "Akkumatik - ' + titel + ' (' + fname + ')";')


            gpl('plot \
                wfile using 2:4 with lines title "mA" lw 2 lc rgbcolor\
                "#009900" , \
                wfile using 2:5 smooth bezier with lines title "mAh" lw\
                2 lc rgbcolor "#0000ff", \
                wfile using 2:8 smooth bezier with lines title "Bat C"\
                axes x1y2 lc rgbcolor "#cc0000" , \
                wfile using 2:18 smooth bezier with lines title "KK C"\
                axes x1y2 lc rgbcolor "#222222";')

            gpl('set nolabel;')
            gpl('set notitle;')

            gpl('set size 1.0,0.45;')
            gpl('set origin 0.0,0.0;')

            if atyp_i == 5:
                gpl(lipo_gnuplot(line_a, rangeval, anz_z))
            elif atyp_i == 0 or atyp_i == 1:
                gpl(nixx_gnuplot())
            else:
                gpl(else_gnuplot())

            gpl('set nomultiplot;')
            gpl('reset')
            tmp = "Generated:  "+"%44s" % (cfg.CHART_DIR + "/"+\
                    fname[-27:-4])+".png"
            print (tmp)
            cfg.FLOG.write(tmp + '\n')
        else:
            continue

    if len(qiv_files) > 0:
        time.sleep(1.8) #sonst finded qiv (noch) nichts allenfalls
        args = shlex.split(qiv_files)
        arguments = ' '.join(str(n) for n in args)
        if platform.system() == "Windows":
            for xtmp in args:
                # os.startfile(xtmp)
                thread.start_new_thread(os.startfile,(xtmp,))
                break #one is enough for eg. irfanview
        else:
            thread.start_new_thread(os.system,(cfg.PICTURE_EXE+' '+arguments,))

#}}}
# vim: set nosi ai ts=8 et shiftwidth=4 sts=4 fdm=marker foldnestmax=1 :
