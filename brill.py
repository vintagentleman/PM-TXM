import os
import csv
import xml.etree.ElementTree as ET


def brilltag(gold, file):
    os.chdir(os.getcwd() + r'\otpt')
    tree = ET.parse(file)
    root = tree.getroot()

    # Словарь тут чисто для статистики
    sfbdict = {'first_break': 0, 'end_break': 0, 'regular_break': 0, 'fallback': 0, 'pc,Tr': 0}

    # Массив для фолбэков
    logmass = []

    for p in root:
        # Правильный тег первого эл-та в триграмме
        prev_ana = ""

        for numb, element in enumerate(p):

            with open(gold) as gst:
                gf = csv.reader(gst, delimiter=";")

                anamass = element.get("ana").split(" ; ")
                check = 0

                for row in gf:
                    # Если текущий элемент - однозначно терминальный ЗП, то искать с ним триграмму бессмысленно
                    if anamass[0] == "pc,Tr,_":
                        prev_ana = anamass[0]
                        check += 1
                        element.set("ana", anamass[0])
                        sfbdict["pc,Tr"] += 1
                        break
                    else:
                        # Если находимся в абсолютном начале предложения/чанка, рассматриваем левые биграммы
                        if numb == 0 or prev_ana == "pc,Tr,_":

                            # Фолбэк к pymorphy2, если текущий элемент последний в предложении
                            if numb + 1 == len(p):
                                break
                            else:
                                if row[0] in anamass and row[1] in p[numb + 1].get("ana").split(" ; "):
                                    prev_ana = row[0]
                                    check += 1
                                    element.set("ana", row[0])
                                    sfbdict["first_break"] += 1
                                    break

                        # Если текущий элемент последний в предложении, рассматриваем правые биграммы
                        elif numb == len(p) - 1:

                            if prev_ana == row[1] and row[2] in anamass:
                                prev_ana = row[2]
                                check += 1
                                element.set("ana", row[2])
                                sfbdict["end_break"] += 1
                                break

                        # В других случаях рассматриваем полноценные триграммы
                        else:
                            if row[0] == prev_ana and row[1] in anamass and row[2] in p[numb + 1].get(
                                    "ana").split(" ; "):
                                prev_ana = row[1]
                                check += 1
                                element.set("ana", row[1])
                                sfbdict["regular_break"] += 1
                                break

                # Фолбэк, если подходящей триграммы в золотом стандарте не нашлось
                if check == 0:

                    # Фиксируем триграммы, на которых случился фолбэк
                    if numb == 0:
                        logstring = "[\n" + element.text + " : " + str(anamass) + ";\n" + p[numb + 1].text + " : " + str(
                            p[numb + 1].get("ana")) + "\n]\n"
                    elif numb == len(p) - 1:
                        logstring = "[\n" + p[numb - 1].text + " : [" + str(
                            prev_ana) + "];\n" + element.text + " : " + str(anamass) + "\n]\n"
                    else:
                        logstring = "[\n" + p[numb - 1].text + " : [" + str(
                            prev_ana) + "];\n" + element.text + " : " + str(anamass) + ";\n" + p[
                                        numb + 1].text + " : [" + str(p[numb + 1].get("ana")) + "]\n]\n"

                    logmass.append(logstring)
                    prev_ana = anamass[0]
                    element.set("ana", anamass[0])
                    sfbdict["fallback"] += 1

    tree.write(file[:-4] + "_brilled.xml", encoding="utf-8")

    with open(file[:-4] + "_log_trg.txt", mode="w", encoding="utf-8") as log:
        for line in logmass:
            log.write(str(line) + "\n")
    print(sfbdict)


if __name__ == '__main__':
    try:
        brilltag("ALL_trigrams.csv", "psycholing.xml")
    except FileNotFoundError:
        print('Error: source file missing.')
