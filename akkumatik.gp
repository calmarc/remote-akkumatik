set title "Akkumatik (Stefan Elstner)";
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
#set yrange [-3000:3000];
set ytics nomirror;

set y2range [-10:70];
set y2label "Grad Celsius";
set y2tics border;

set nolabel;

set size 1.0,0.50;

set origin 0.0,0.5;
wfile="/home/calmar/tmpakku/Akku1-3.dat"
set title "Ent-Laden";

plot \
     wfile using 2:4 with lines title "mA" lw 2 lc rgbcolor "#009900" , \
     wfile using 2:5 with lines title "mAh" lw 2 lc rgbcolor "#0000ff", \
     wfile using 2:8 smooth bezier with lines title "Bat C°" axes x1y2 lc rgbcolor "#cc0000" , \
     wfile using 2:18 smooth bezier with lines title "KK C°" axes x1y2 lc rgbcolor "#999999";


set nolabel;
set notitle;
set noy2range;
set noy2label;
set noy2tics;

set ylabel "mVolt Akku"
set yrange [*:*];

set ytics mirror;
set origin 0.0,0.0;
plot wfile using 2:3 with lines title "mVolt" lw 1 lc rgbcolor "#ff0000";

set nomultiplot;
