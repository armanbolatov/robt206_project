#include <LiquidCrystal_I2C.h>
#include <cvzone.h>
#include <Servo.h>

// объект для контроля мотора
Servo door_servo;
// объект с параметрами дисплея
LiquidCrystal_I2C lcd(0x27, 16, 2);
// связует питоновский serialdata с ардуино
SerialData serialData(5, 1);
// массив хранящий статус дома
int valsRec[5];

// инициализируем пины
int door = 7;
int led1 = 6;
int led2 = 5;
int led3 = 4;

// обновляет значение температуры на дисплее
void write_to_i2c(int n)
{
  lcd.init();
  lcd.clear();
  lcd.backlight();
  lcd.setCursor(2, 0);
  lcd.print("Current temperature:");
  lcd.setCursor(2, 1);
  lcd.print(n);
  lcd.print(" mode");
}

void setup()
{
  serialData.begin(9600);
  // фиксируем пины
  pinMode(led1, OUTPUT);
  pinMode(led2, OUTPUT);
  pinMode(led3, OUTPUT);
  door_servo.attach(door);
  // инициализируем текст на дисплее
  write_to_i2c(0);
}

void loop()
{
  // достаем статус дома из питоновского кода
  serialData.Get(valsRec);
  // и сохраняем в переменные
  int door_status = valsRec[0];
  int led1_status = valsRec[1];
  int led2_status = valsRec[2];
  int led3_status = valsRec[3];
  int i2c_status  = valsRec[4];
  // пишем в дисплей значение температуры
  write_to_i2c(i2c_status);
  if (door_status == 0) // если должна быть закрытой
  {
    door_servo.write(180); // вращаем мотор на 180
    delay(500);            // и ждем полсекунды
  }
  else // если должна быть открытой
  {
    door_servo.write(0); // вращаем мотор на 0
    delay(500);          // и ждем полсекунды
  }
  // обновляем статус света в комнатах
  digitalWrite(led1, led1_status);
  digitalWrite(led2, led2_status);
  digitalWrite(led3, led3_status);
}
