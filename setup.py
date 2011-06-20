from distutils.core import setup
import py2exe
import os
import shutil
import sys

Mydata_files = []
Mydata_files.append(('bilder', ['bilder/Display.jpg']))
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
