from distutils.core import setup
import py2exe
import os
import shutil
import sys

Mydata_files = []
Mydata_files.append(('bilder', [
        'bilder/Ausgang.png',
        'bilder/Ausgang_hover.png',
        'bilder/Ausgang_off.png',
        'bilder/Display.png',
        'bilder/Display.png',
        'bilder/chart.png',
        'bilder/chart_hover.png',
        'bilder/para.png',
        'bilder/para_hover.png',
        'bilder/quit.png',
        'bilder/quit_hover.png',
        'bilder/recycle.png',
        'bilder/recycle_hover.png',
        'bilder/start.png',
        'bilder/start_hover.png',
        'bilder/stop.png',
        'bilder/stop_hover.png']))
Mydata_files.append(('', ['config.txt']))
Mydata_files.append(('', ['README']))

path= sys.path[0].replace('\\','/')
try:
	shutil.copytree("C:/Python26/gnuplot",  path+ "/dist/gnuplot/")
except:
	print ("wurde nickt kopiert... gnuplot - wohl schon da")

setup(
    name = 'Remote Akkumatik',
    description = 'Remote Akkumatik Display/Control/Chart',
    version = '0.5',

    windows = [
#    console = [
                  {
                      'script': 'remote_akkumatik.py',
                      'icon_resources': [(1, "ra.ico")],
                  }
              ],

    options = {
                  'py2exe': {
	 	      'dist_dir':'dist',
                      'includes': 'cairo, pango, pangocairo, atk, gobject, gio',
                  }
              },

    data_files= Mydata_files
)
# vim: set nosi ai ts=8 et shiftwidth=4 sts=4 fdm=marker foldnestmax=1 :
