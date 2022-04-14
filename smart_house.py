import cv2
from cvzone.HandTrackingModule import HandDetector
from cvzone.SerialModule import SerialObject
import pvporcupine as pvp
import pyaudio
import struct

# для чтения картинок с вебки
cap = cv2.VideoCapture(0)
# создаем детектор и ограничиваем макс. кол-во рук двумя
detector = HandDetector(detectionCon=0.8, maxHands=2)
# для взаимодействия с ардуино
arduino = SerialObject()
# слова на которые будет реагировать программа
keywords=["jarvis", "bumblebee"]
# для распознования ключевых слов в аудиофрейме
porcupine = pvp.create(
    access_key="M+nxBmCjzYc9nHkFmDeKX4lJC6GwUKJpl/UQz7COcJ0YWOxH2TtNSQ==",
    keywords=keywords,
)
# для чтения аудио с микрофона
py_audio = pyaudio.PyAudio()
audio_stream = py_audio.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length
)

values = {
    ''' 
        словарь хранящий статус дома
        door: открыта или закрыта дверь
        ledi: свет в комнате i
        i2c: уровень температуры
    '''
    "door": 0, # 0 - закрыта, 1 - открыта
    "led1": 0, # 0 - выключен, 1 - включен
    "led2": 0, # 0 - выключен, 1 - включен
    "led3": 0, # 0 - выключен, 1 - включен
    "i2c": 0, # принимает от 0 до 5
}


room_lights = {
    '''
        словарь мапающий комбинацию пальцев в пару (s, i),
        где s статус света в комнате i;
        (1, 1, 1, 0, 0) - означает что подняты большой,
        указательный и средние пальцы, а опущены остальные
    '''
    (1, 1, 0, 0, 0): (1, 1),
    (0, 1, 0, 0, 0): (0, 1),
    (1, 1, 1, 0, 0): (1, 2),
    (0, 1, 1, 0, 0): (0, 2),
    (1, 1, 0, 0, 1): (1, 3),
    (0, 1, 0, 0, 1): (0, 3),
}

while True:

    pcm = audio_stream.read(porcupine.frame_length)
    # достаем текущий аудофрейм
    audio_frame = struct.unpack_from("h" * porcupine.frame_length, pcm)
    # равен -1 если не произнесено слово из keywords
    keyword_index = porcupine.process(audio_frame)

    # если произнесено jarvis
    if keyword_index == 0:
        values["door"] = 1
    # если прознесено bumblebee
    if keyword_index == 1:
        values["door"] = 0

    # читаем изображение с вебки
    success, img = cap.read()
    # и ищем в ней руки
    hands, img = detector.findHands(img)

    if hands:
        # если видим руку то сохраняем значение в hands1
        hand1 = hands[0]
        # сохраняем количество поднятых пальцев первой руки
        fingers1 = detector.fingersUp(hand1)

        if len(hands) > 1:
            # если две руки то делаем то же самое для второй
            hand2 = hands[1]
            fingers2 = detector.fingersUp(hand2)
        else:
            hand2, fingers2 = None, None

        # если оказалось, что hand1 левая рука, то свапаем
        # hand1 и hand2 для сохранения инварианта
        # инвариант: hand1 - правая, hand2 - левая
        if hand1["type"] == "Left":
            hand1, hand2 = hand2, hand1
            fingers1, fingers2 = fingers2, fingers1

        # если пользователь показывает правую руку
        if hand1:
            # то читаем жест и обновляем соответствующее
            # значение ключа в values
            t_fingers1 = tuple(fingers1)
            if t_fingers1 in room_lights:
                light_type, room_number = room_lights[t_fingers1] 
                led_name = f"led{room_number}"
                values[led_name] = light_type

        # если пользователь показывает левую руку
        if hand2:
            # то считаем количество согнутых пальцев
            # и обновляем значение в i2c
            num_fingers2 = sum(fingers2)
            values["i2c"] = num_fingers2

    # переводим значения словаря в лист и отправляем на ардуино
    values_lists = list(values.values())
    arduino.sendData(values_lists)

    print(values_lists) # для дебага

    cv2.imshow("Image", img)
    cv2.waitKey(1)