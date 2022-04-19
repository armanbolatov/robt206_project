# Gesture and Keyword Control of Smart House

This repo contains the code of the ROBT 206 project work of group ❤️❤️❤️ (Aruzhan Sabyrbek, Daria Gole, Arman Bolatov).

The project report is available at [this link](https://github.com/armanbolatov/robt206_project/blob/main/robt206.pdf).

## Requirements for Python

- PyAudio
- Picovoice Porcupine
- OpenCV
- CV Zone
- Face Recognition

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