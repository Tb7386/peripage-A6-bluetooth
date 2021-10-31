from gattlib import GATTRequester
from PIL import Image, ImageOps, ImageFont, ImageDraw
import time
import crc8
import sys
import argparse

parser = argparse.ArgumentParser(description="Print an text to a Peripage A6 BLE")
parser.add_argument("BTMAC",help="BT MAC address of the Peripage A6")

parser.add_argument("-t", "--text",type=str, help="Text to be printed")
args = parser.parse_args()

if not args.text:
    print("ERROR: Please specfiy text with -t or --text argument")
    sys.exit(1)

# ------------------------------------------------------------------------------
# imgFromString : Convert string to binary image
# ------------------------------------------------------------------------------
def imgFromString(s):
    # Font choice
    font = ImageFont.truetype("liberation-mono/LiberationMono-Regular.ttf", 50)
    # Get size of text
    size = font.getsize_multiline(s)
    # Fix height and width
    size_x = 384 if size[0] <= 384 else size[0]
    size_y = size[1]
    # Create image
    img = Image.new("RGB", size=(size_x, size_y), color="white")
    # Draw text in image
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), s, (0, 0, 0), font=font)
    # Convert RGB image to binary image
    img = ImageOps.invert(img.convert('L'))
    img = img.convert('1')
    # Flip image to print
    #img = ImageOps.flip(img)
    #img = ImageOps.mirror(img)
    # Save image to file
    #img.save('img.png')
    return img

# ------------------------------------------------------------------------------
# binFromImg : Convert binary image to array
# ------------------------------------------------------------------------------
def binFromImg(img):
    binImg=[]
    for line in range (0,img.size[1]):
        binImg.append(''.join(format(byte, '08b') for byte in img.tobytes()[int(line*(img.size[0]/8)):int((line*(img.size[0]/8))+img.size[0]/8)]))
    return binImg

# ------------------------------------------------------------------------------
# dataCrc : Calcul hex CRC-8
# ------------------------------------------------------------------------------
def dataCrc(data):
    hash = crc8.crc8()
    hash.update(bytes.fromhex(data))
    return str(hash.hexdigest())

# ------------------------------------------------------------------------------
# binCount : Convert binary image to array
# ------------------------------------------------------------------------------
def binCount (binImg):
    trame=[]
    i=0
    #read Image line by line
    for line in binImg:
        nb_zero=0
        nb_one=0
        trame.append('')
        # Read line char by char
        for char in line:
            # Bit '0' process
            if char == '0':
                # Bit '1' before
                if nb_one!=0:
                    # Format '1' number to hex + 128 (First bit to print black)
                    trame[i]+='{:02x}'.format(128+nb_one)
                    nb_one=0
                # Max number is 127 (First bit color + 127 max  number = '0x7f')
                if nb_zero>126:
                    trame[i]+='{:02x}'.format(nb_zero)
                    nb_zero=0
                nb_zero += 1
            # Bit '1' process
            if char == '1':
                # Bit '0' before
                if nb_zero!=0:
                    # Format '0' number to hex
                    trame[i]+='{:02x}'.format(nb_zero)
                    nb_zero=0
                # Max number is 127 (First bit color + 127 max  number = '0xff')
                if nb_one>126:
                    trame[i]+='{:02x}'.format(128+nb_one)
                    nb_one=0
                nb_one += 1
        # End of trame. If '1' or '0' before process
        if nb_zero!=0:
            trame[i]+='{:02x}'.format(nb_zero)
        elif nb_one!=0:
            trame[i]+='{:02x}'.format(128+nb_one)
        i+=1
    return trame

# ------------------------------------------------------------------------------
# bleConnect : Connect to printer mac
# ------------------------------------------------------------------------------
def bleConnect(mac):
    host = mac
    req = GATTRequester(host, False)
    req.connect(True)
    # Some config trame
    req.write_by_handle(0x09, bytes([1, 0]))
    time.sleep(0.02)
    req.write_by_handle(0x000e, bytes([1, 0]))
    time.sleep(0.02)
    req.write_by_handle(0x0011, bytes([2, 0]))
    time.sleep(0.02)
    req.exchange_mtu(83)
    time.sleep(0.02)
    req.write_cmd(0x0006, bytes([18, 81, 120, 168, 0, 1, 0, 0, 0, 255, 18, 81, 120, 163, 0, 1, 0, 0, 0, 255]))
    time.sleep(0.02)
    req.write_cmd(0x0006, bytes([18, 81, 120, 187, 0, 1, 0, 1, 7, 255]))
    time.sleep(0.02)
    req.write_cmd(0x0006, bytes([18, 81, 120, 163, 0, 1, 0, 0, 0, 255]))
    time.sleep(0.2)
    return req

# ------------------------------------------------------------------------------
# printData : Print text
# ------------------------------------------------------------------------------
def printText(text,req):
    data = binCount(binFromImg(imgFromString(text)))
    for dat in data:
        # Header of trame
        head = "5178bf00"
        # Format BT trame
        trame=head + '{:02x}'.format(len(bytes.fromhex(dat)),'x') + "00" + dat + dataCrc(dat) + "ff"
        print(trame)
        i = len(trame)
        # Pull 40 bytes trames
        while i > 0:
            if i > 40:
                req.write_cmd(0x06, bytes.fromhex(trame[len(trame)-i:len(trame)-i+40]))
                i -= 40
            else:
                req.write_cmd(0x06, bytes.fromhex(trame[len(trame)-i:len(trame)]))
                i -= 40
            time.sleep(0.01)
    # 90 dp moving forward paper
    forwardPaper(90)
    return 0

# ------------------------------------------------------------------------------
# forwardPaper : Moving forward
# ------------------------------------------------------------------------------
def forwardPaper(dp):
    head = "5178a100"
    data = '{:02x}'.format(dp) + '00'
    # Format BT trame
    trame=head + '{:02x}'.format(len(bytes.fromhex(data)),'x') + "00" + data + dataCrc(data) + "ff"
    req.write_cmd(0x06, bytes.fromhex(trame))
    time.sleep(0.01)

#Start
host = args.BTMAC
if args.text:
    req = bleConnect(host)
    printText(args.text,req)
