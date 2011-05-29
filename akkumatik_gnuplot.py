#!/usr/bin/python

import Gnuplot, Gnuplot.funcutils
import sys


def gnuplot():

  for arg in sys.argv[1:]:
    g = Gnuplot.Gnuplot(debug=1)

    #g('set terminal wxt')
    g('set terminal png size 1280, 1024;')
    g('set output "' + arg + '.png"')

    g('set title "Akkumatik (Stefan Estner)";')
    g('set xdata time;')
    g('set datafile separator "";')
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

    g('set size 1.0,0.50;')

    g('set origin 0.0,0.5;')
    g('wfile="' + arg + '";')
    g('set title "Ent-Laden";')

    g('plot \
          wfile using 2:4 with lines title "mA" lw 2 lc rgbcolor "#009900" , \
          wfile using 2:5 smooth bezier with lines title "mAh" lw 2 lc rgbcolor "#0000ff", \
          wfile using 2:8 smooth bezier with lines title "Bat C" axes x1y2 lc rgbcolor "#cc0000" , \
          wfile using 2:18 smooth bezier with lines title "KK C" axes x1y2 lc rgbcolor "#999999";')


    g('set nolabel;')
    g('set notitle;')

    g('set ylabel "mVolt Akku"')
    g('set yrange [0:*];')
    g('set ytics nomirror;')

    g('set y2range [*:*];')
    g('set y2label "Innerer Widerstand Ohm";')
    g('set y2tics border;')


    g('set size 1.0,0.50;')
    g('set origin 0.0,0.0;')

    g('plot wfile using 2:3 with lines title "mVolt" lw 1 lc rgbcolor "#ff0000", \
          wfile using 2:6 with lines title "IOhm" axes x1y2;')

    g('set nomultiplot;')

#    g('set terminal png;')
#    g('set output "' + arg + '.png"')
#    g('replot"')
    g('reset')

    #raw_input('Please press return to continue...\n')


if __name__ == '__main__':
    gnuplot()
