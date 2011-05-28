#!/usr/bin/python

import Gnuplot, Gnuplot.funcutils


def gnuplot():

  g = Gnuplot.Gnuplot(debug=1)

  g('set terminal wxt')
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
  #set yrange [-3000:3000];
  g('set ytics nomirror;')

  g('set y2range [-10:70];')
  g('set y2label "Grad Celsius";')
  g('set y2tics border;')

  g('set nolabel;')

  g('set size 1.0,0.50;')

  g('set origin 0.0,0.5;')
  g('wfile="/home/calmar/akkumatik/Akku1-1.dat";')
  g('set title "Ent-Laden";')

  g('plot \
       wfile using 2:4 with lines title "mA" lw 2 lc rgbcolor "#009900" , \
       wfile using 2:5 with lines title "mAh" lw 2 lc rgbcolor "#0000ff", \
       wfile using 2:8 smooth bezier with lines title "Bat C" axes x1y2 lc rgbcolor "#cc0000" , \
       wfile using 2:18 smooth bezier with lines title "KK C" axes x1y2 lc rgbcolor "#999999";')


  g('set nolabel;')
  g('set notitle;')
  g('set noy2range;')
  g('set noy2label;')
  g('set noy2tics;')

  g('set ylabel "mVolt Akku"')
  g('set yrange [*:*];')

  g('set ytics mirror;')
  g('set origin 0.0,0.0;')
  g('plot wfile using 2:3 with lines title "mVolt" lw 1 lc rgbcolor "#ff0000";')

  g('set nomultiplot;')
  raw_input('Please press return to continue...\n')



if __name__ == '__main__':
    gnuplot()
