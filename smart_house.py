import cv2
import pvporcupine as pvp
import pyaudio
import struct
import face_recognition as fr
import dlib
import os
from cvzone.HandTrackingModule import HandDetector
from cvzone.SerialModule import SerialObject


def main():

    print(dlib.DLIB_USE_CUDA)  # проверить работает ли гпу
    cap = cv2.VideoCapture(0)  # для чтения картинок с вебки
    detector = HandDetector(detectionCon=0.8, maxHands=2)  # создаем детектор
    arduino = SerialObject()  # для взаимодействия с ардуино
    # слова на которые будет реагировать программа
    keywords = ["alexa", "bumblebee"]
    # для распознования ключевых слов в аудиофрейме
    porcupine = pvp.create(
        access_key=os.getenv("PVP_TOKEN"),
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

    known_faces_dir = "known_faces"  # директория с известными лицами
    tolerance = 0.6  # порог для определения лица
    model = "cnn"  # тип нейронки
    print("loading known faces")
    known_faces = []  # чтобы хранить известные лица
    known_names = []  # чтобы хранить имена этих лиц

    for name in os.listdir(known_faces_dir):
        for filename in os.listdir(f"{known_faces_dir}/{name}"):
            image = fr.load_image_file(f"{known_faces_dir}/{name}/{filename}")
            encoding = fr.face_encodings(image)[0]
            known_faces.append(encoding)
            known_names.append(name)

    '''
    словарь хранящий статус дома
    door: открыта или закрыта дверь
    ledi: свет в комнате i
    i2c: уровень температуры
    '''
    values = {
        "door": 0,  # 0 - закрыта, 1 - открыта
        "led1": 0,  # 0 - выключен, 1 - включен
        "led2": 0,  # 0 - выключен, 1 - включен
        "led3": 0,  # 0 - выключен, 1 - включен
        "i2c": 0,  # принимает от 0 до 5
    }

    '''
    словарь мапающий комбинацию пальцев в пару (s, i),
    где s статус света в комнате i;
    (1, 1, 1, 0, 0) - означает что подняты большой,
    указательный и средние пальцы, а опущены остальные
    '''
    room_lights = {
        (1, 1, 0, 0, 0): (1, 1),
        (0, 1, 0, 0, 0): (0, 1),
        (1, 1, 1, 0, 0): (1, 2),
        (0, 1, 1, 0, 0): (0, 2),
        (1, 1, 0, 0, 1): (1, 3),
        (0, 1, 0, 0, 1): (0, 3),
    }

    '''
    если на текущем кадре нашли известное лицо, то
    последующие n_iter кадров не будем проверять на лица.
    это поможет ускорить вычисления. а следить за кол-вом
    итераций будет переменная счетчик cur_iter
    '''
    cur_iter = n_iter = 100
    match = False

    while True:
        if cur_iter <= n_iter:
            cur_iter += 1  # увеличиваем счетчик

        _, img = cap.read()  # читаем изображение с вебки

        if cur_iter > n_iter:  # если прошло n_iter итераций
            locations = fr.face_locations(
                img, model=model)  # находим лица в кадре
            encodings = fr.face_encodings(
                img, locations)  # вытаскиваем фичи из лиц
            for face_encoding, _ in zip(encodings, locations):
                results = fr.compare_faces(
                    known_faces, face_encoding, tolerance)
                match = None
                if True in results:  # если нашли известное лицо
                    # находим имя этого лица
                    match = known_names[results.index(True)]
                    cur_iter = 0  # обнуляем счетчик
                    print(f"Match found: {match}")

            if not match:  # если не нашли знакомое лицо, то не выполняем ничего
                cv2.imshow("Image", img)
                cv2.waitKey(1)
                continue

        # достаем текущий аудофрейм
        pcm = audio_stream.read(porcupine.frame_length)
        audio_frame = struct.unpack_from("h" * porcupine.frame_length, pcm)
        # равен -1 если не произнесено слово из keywords
        keyword_index = porcupine.process(audio_frame)

        if keyword_index == 0:  # если произнесено jarvis
            values["door"] = 1
        if keyword_index == 1:  # если прознесено bumblebee
            values["door"] = 0

        hands, img = detector.findHands(img)  # ищем руки в текущем кадре

        if hands:
            hand1 = hands[0]  # если видим руку, то сохраняем его в hands1
            # и сохраняем пальцы первой руки
            fingers1 = detector.fingersUp(hand1)

            if len(hands) > 1:  # если две руки, то делаем то же самое для второй
                hand2 = hands[1]
                fingers2 = detector.fingersUp(hand2)
            else:
                hand2, fingers2 = None, None

            # если оказалось, что hand1 левая рука, то свапаем
            # hand1 и hand2 для сохранения инварианта;
            # инвариант: hand1 - правая, hand2 - левая
            if hand1["type"] == "Left":
                hand1, hand2 = hand2, hand1
                fingers1, fingers2 = fingers2, fingers1

            if hand1:  # если пользователь показывает правую руку
                # то читаем жест и обновляем соответствующее
                # значение ключа ledi в values
                t_fingers1 = tuple(fingers1)
                if t_fingers1 in room_lights:
                    light_type, room_number = room_lights[t_fingers1]
                    led_name = f"led{room_number}"
                    values[led_name] = light_type

            if hand2:  # если пользователь показывает левую руку
                # то считаем количество согнутых пальцев
                # и обновляем значение в i2c
                num_fingers2 = sum(fingers2)
                values["i2c"] = num_fingers2

        # переводим значения словаря в лист и отправляем на ардуино
        values_lists = list(values.values())
        arduino.sendData(values_lists)

        print(values_lists)  # для дебага

        cv2.imshow("Image", img)
        cv2.waitKey(1)


if __name__ == "__main__":
    main()
