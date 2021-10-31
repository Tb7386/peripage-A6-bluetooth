# Chiness copy of Peripage A6: Direct printing via Bluetooth Low Energy 

**This scripts enables printing on chiness copy of Peripage A6. We aim mostly at Linux here, but due to the use of Python this script should be portable to any environment supported by [PyBluez](https://github.com/pybluez/pybluez)**

## Introduction
Chiness copy of Peripage A6 (buy on Aliexpress https://fr.aliexpress.com/item/1005003351851277.html?spm=a2g0s.9042311.0.0.2b904c4dRWJyPA) is an inexpensive portable thermo printer. It provides by Bluetooth Low Energy. This script only print text.

Usable : python3 ./ppa6-print.py MAC_ADDRESS -t TEXT_TO_PRINT
MAC_ADDRESS : format 00:00:00:00:00:00

In reverse engineering, I analyzed that:

Trame is composed by

|   Header    | data lenght | ?? |       DATA     | CRC8 | end of line 

| 51:78:XX:00 |     05      | 00 | 82:7f:7f:7e:82 | 60   |     ff     


Header XX :
   - bf : Print 384 dot
   - a1 : move forward paper (eg: data=01:00 => 1 dot forward)


Print data (eg 82 -> 1000 0010) :
  - bit[0] : 1 = Black, 0 = White
  - bit[2-7] : number of dot

## ToDo

Print multilines text
