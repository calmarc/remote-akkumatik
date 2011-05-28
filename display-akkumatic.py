#!/usr/bin/env python
#vim: set fileencoding=utf-8

import serial
import sys
import pygtk
pygtk.require('2.0')
import gtk
import pango
import gobject


class akkumatik_data:

  def delete_event(self, widget, event, data=None):
      # Change FALSE to TRUE and the main window will not be destroyed
      # with a "delete_event".
      return False

  def destroy(self, widget, data=None):
      gtk.main_quit()

  def draw_pixbuf(self, widget, event):
     path = 'Display.jpg'
     pixbuf = gtk.gdk.pixbuf_new_from_file(path)
     widget.window.draw_pixbuf(widget.style.bg_gc[gtk.STATE_NORMAL], pixbuf, 0, 0, 0,0)

  def __init__(self):

      self.window = gtk.Window()
      self.window.set_title('Akkumatic Remote Display')
      self.window.set_size_request(545,168)
      self.window.set_default_size(545,168)
  
      self.window.connect("delete_event", self.delete_event)
      self.window.connect("destroy", self.destroy)
      self.window.set_border_width(10)

  
      self.hbox = gtk.HBox()
      self.window.add(self.hbox)
      self.hbox.connect('expose-event', self.draw_pixbuf)

      self.label = gtk.Label()
      self.label.modify_font(pango.FontDescription("sans 22"))

      self.hbox.pack_start(self.label, True, False, 10)
   
  
      self.window.show_all()

      gobject.timeout_add(500, self.read_line) #1 is prinzipally enough -> readline waits.

      self.ser = serial.Serial(
          port='/dev/ttyS0',
          baudrate=9600,
          parity=serial.PARITY_ODD,
          stopbits=serial.STOPBITS_TWO,
          bytesize=serial.SEVENBITS
      )

      self.ser.open()
      self.ser.isOpen()

      self.f = open('/home/calmar/akkumatik/serial-akkumatik.dat', 'w')

      self.i = 0

  def read_line(self):

      #output = "1LL2 11.9V 4:44\n +2.20A5 +0.137mAh"
      #self.i +=1
      #self.label.set_markup('<span foreground="#333333">' + str(self.i) + output + '</span>')
      #return True

      lin = self.ser.readline()
      self.f.write(lin)

      daten = lin.split('\x7f')
      if daten[0] == "1":
          ausgang = long(daten[0])
          zeit = daten[1]
          ladeV = long(daten[2])/1000.0
          mA = long(daten[3])
          mAh = long(daten[4])/1000.0
          ri = daten[6]
          cBat = long(daten[7])
          zellen = daten[8]
          phase = daten[9]
          zyklus = daten[10]
          sp = daten[11]
          watt = daten[12]
          Wh = daten[13]
          cKK = long(daten[17])

          output ="%i: %8.3fV %s\n %6imA %8.3fAh\n %4i°(B) %4i°(Kk)" % (ausgang, ladeV, zeit, mA, mAh, cBat, cKK)
          output_tty ="%i: %8.3fV %s %6imA %8.3fAh %4i°(B) %4i°(Kk)" % (ausgang, ladeV, zeit, mA, mAh, cBat, cKK)
          #output = daten[0] + ": " \
             #+ daten[1] + " " \
             #+ str(long(daten[2]) / 1000.0) + "V " \
             #+ str(long(daten[3])) + "mA" \
             #+ " Ladung:" + str(long(daten[4])) \
             #+ " Ri:" + daten[6] \
             #+ " " + str(long(daten[7])) + "C" \
             #+ "\n" \
             #+ " Zellen:" + str(long(daten[8])) \
             #+ " Phase:" + str(long(daten[9])) \
             #+ " Zyklus:" + daten[10] \
             #+ " Sp/n:" + daten[11] \
             #+ " " + daten[12] + "W " \
             #+ daten[13] + "Wh " \
             #+ daten[17] + "C    "
          #output += '\x0D'

          #terminal output

          sys.stdout.write (output_tty)
          sys.stdout.flush()

          #graphical output
          self.label.set_markup('<span foreground="#333333">'+ output + '</span>')
          while gtk.events_pending():
              gtk.main_iteration()

      return True
                     
  def main(self):
      gtk.main()


if __name__ == '__main__':
    displ = akkumatik_data()
    displ.main()
