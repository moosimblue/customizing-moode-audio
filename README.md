# customizing-moode-audio

## Power LED
- /boot/firmware/config.txt
```
# RGB
# blue
gpio=25=op,dh,pu
dtoverlay=gpio-poweroff,gpiopin=25,active_low
# green
gpio=8=op,dl
# red
dtparam=act_led_gpio=1,act_led_trigger=mmc1
```
- pinout
| RPi Pin | GPIO | RGB |
|---|---|---|
| 20 | GND | GND(-) |
| 22 | 25 | B |
| 24 | 8 | G |
| 26 | 7 | R |

![RGB LED](https://www.ic114.com/IMAGE/PRODUCT/IMAGE1/hs-rgb-module-zy.jpg)

## Rotary Encoder
- pinout
| RPi Pin | GPIO | Rotary Encoder |
|---|---|---|
| 01 | 3.3V | Vcc |
| 09 | GND  | GND |
| 11 | 17   | SW  |
| 13 | 27   | A(DT) |
| 15 | 22   | B(CLK) |

![Rotary Encoder](https://how2electronics.com/wp-content/uploads/2019/03/Rotary-Encoder-2.jpg)
