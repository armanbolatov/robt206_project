# Gesture and Keyword Control of Smart House

This repo contains the code of the ROBT 206 project work of group #2 (Aruzhan Sabyrbek, Daria Gole, Arman Bolatov).

Project report: *to be updated*.

## Requirements for Python

- `pyaudio >= 0.2`
- `pvporcupine >= 2.1.2`
- `cv2 >= 4.5`
- `cvzone >= 1.5.6`

## Requirements for Arduino

- [LiquidCrystal_I2C](https://www.arduinolibraries.info/libraries/liquid-crystal-i2-c)
- [CV Zone](https://www.computervision.zone/courses/computer-vision-arduino-chapter-1/)


## How to use

Run `smart_house.ino` in Arduino, then from your command line:

```bash
$ git clone https://github.com/armanbolatov/robt206_project
$ cd robt206_project
$ pip install -r requirements.txt
$ python smart_house.py
```