set title "Akkumatik (Stefan Estner)";
set xdata time;
set datafile separator "";
set timefmt "%H:%M:%S";
set grid
#set bmargin 5
set lmargin 10
set rmargin 7
#set tmargin 5
set multiplot;


set key box
set ylabel "Laden mA / Kapazitaet mAh"
set ytics nomirror;

set y2range [-10:70];
set y2label "Grad Celsius";
set y2tics border;

set nolabel;
set xtics axis;
#set xlabel "x-Achse" -0.2:0.2;
set label "Angebotsfunktion" [85:200];

set size 1.0,0.50;
set origin 0.0,0.5;

wfile="/home/calmar/akkumatik/Akku1-1.dat";
set title "Ent-Laden";
set boxwidth 3

set yrange [-20:*];

plot \
     wfile using 2:4 with points title "mA" lw 1 lc rgbcolor "#009900" pt 1 , \
     wfile using 2:5 smooth bezier with lines title "mAh" lw 2 lc rgbcolor "#0000ff", \
     wfile using 2:8 smooth bezier with lines title "Bat C°" axes x1y2 lc rgbcolor "#cc0000" , \
     wfile using 2:18 smooth bezier with lines title "KK C°" axes x1y2 lc rgbcolor "#999999";


set nolabel;
set notitle;
set noy2range;
set noy2label;
set noy2tics;

set y2label "mA";
set y2tics border;

set y2range [0:*];
set yrange [0:*];

set ylabel "mVolt Akku"
set yrange [0:*];
set ytics mirror;

set size 1.0,0.50;
set origin 0.0,0.0;
set style fill   pattern 4 border


plot wfile using 2:3 with points title "mVolt" lc rgbcolor "#ff0000" pt 1, \
     wfile using 2:5 smooth bezier with lines title "mAh" lw 2 lc rgbcolor "#0000ff", \
     wfile using 2:4 with points title "mA" lc rgbcolor "#009900" pointtype 1 axes x1y2;

set nomultiplot;
reset
