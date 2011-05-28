#!/usr/bin/python

def filesplit():
  line_counter = 0
  zaehler1 = 1
  zaehler2 = 1
  flag1 = False
  flag2 = False
  ausgang1_part = ""
  ausgang2_part = ""

  fhI = open('/home/calmar/akkumatik/serial-akkumatik.dat', "r")

  for line in fhI.readlines():
    line_counter += 1
    #filter out useless lines
    if line[2:10] == "00:00:00": #not begun yet
      continue

    if line[11:16] == "00000": #no volt lines
      print ("DEBUG: Volt = zero")
      continue

    if line[0:1] == "1":
      if line[2:10] == "00:00:01" and line_counter > 2: #don't write when it just begun
        fh1 = open('/home/calmar/akkumatik/Akku1-'+str(zaehler1)+'.dat', "w+")
        fh1.write(ausgang1_part)
        fh1.close()
        zaehler1 += 1
        ausgang1_part = line
      else:
        ausgang1_part += line

    elif line[0:1] == "2": #"2"
      if line[2:10] == "00:00:01" and line_counter > 2: #don't write when it just begun
        fh2 = open('/home/calmar/akkumatik/Akku2-'+str(zaehler2)+'.dat', "w+")
        fh2.write(ausgang2_part)
        fh2.close()
        zaehler2 += 1
        ausgang2_part = line
      else:
        ausgang2_part += line

  if len(ausgang1_part) > 0:
    fh1 = open('/home/calmar/akkumatik/Akku1-'+str(zaehler1)+'.dat', "w+")
    fh1.write(ausgang1_part)
    fh1.close()
  if len(ausgang2_part) > 0:
    fh2 = open('/home/calmar/akkumatik/Akku2-'+str(zaehler2)+'.dat', "w+")
    fh2.write(ausgang2_part)
    fh2.close()

  #close files
  fhI.close()


if __name__ == '__main__':
    filesplit()

