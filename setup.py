from distutils.core import setup
import py2exe
import os
import shutil
import sys

Mydata_files = []
for files in os.listdir('C:/Python26/gnuplot'):
	f1 = 'C:\\Python26\\gnuplot\\' + files
	if os.path.isfile(f1): # skip directories
		f2 = 'gnuplot', [f1]
		Mydata_files.append(f2)

Mydata_files.append(('bilder', ['bilder/Display.jpg']))
path= sys.path[0].replace('\\','/')
try:
	shutil.copytree("C:/Python26/gnuplot",  path+ "/dist/gnuplot/")
except:
	print ("wurde nickt kopiert... gnuplot - wohl schon da")

setup(
    name = 'Remote Akkumatik',
    description = 'Remote Akkumatik Display/Control/Chart',
    version = '0.5',

#    windows = [
    console = [
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
