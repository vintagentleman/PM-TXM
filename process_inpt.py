import os
import glob
import nltk
import csv
from collections import OrderedDict
from xml.etree import ElementTree as etree
from xml.dom.minidom import parseString
from pymorphy2 import MorphAnalyzer
from tags import pymorphy_all
import conj
import time


class Profiler(object):
    def __enter__(self):
        self._startTime = time.time()

    def __exit__(self, type, value, traceback):
        print("Elapsed time: {:.3f} sec".format(time.time() - self._startTime))


def format_tag(t):

    if t in pymorphy_all:
        return pymorphy_all[t]

    return '_'


def format_parse_list(parse_list):
    ana_list = []

    for i, parse in enumerate(parse_list):
        ana = OrderedDict()

        for j, item in enumerate(parse):
            pos = format_tag(item.tag.POS)

            if pos != '_':
                animacy = format_tag(item.tag.animacy)
                case = format_tag(item.tag.case)
                number = format_tag(item.tag.number)
                gender = format_tag(item.tag.gender)
                person = format_tag(item.tag.person)
                aspect = format_tag(item.tag.aspect)

                if pos in ('Nn', 'Pn'):
                    if case != 'Ac':
                        animacy = '_'

                    if number == 'Pl':
                        gender = '_'

                elif pos == 'Vb':
                    if person == '_' and number == 'Pl':
                        gender = '_'

                if all(grammeme == '_' for grammeme in (animacy, case, number, gender, person, aspect)):
                    ana[pos] = item.normal_form
                else:
                    ana[','.join((pos, animacy, case, number, gender, person, aspect))] = item.normal_form

            # Знаки препинания, числа, иностранные слова и прочее
            else:
                pos = format_tag(str(item.tag).split(',')[0])

                if pos == 'PM':
                    try:
                        next_word = parse_list[i + 1][0].normal_form
                        next_pair = '%s %s' % (parse_list[i + 1][0].normal_form, parse_list[i + 2][0].normal_form)

                    # Терминал, если 1) в конце предложения
                    except IndexError:
                        ana['PM,Tr,_'] = item.normal_form

                    else:
                        # Терминал, если 2) в списке, 3) перед союзами
                        if (item.normal_form in ('?', '!', ';', '(', ')', '[', ']', '//')
                                or next_word in conj.sing or next_pair in conj.doub):
                            ana['PM,Tr,_'] = item.normal_form
                        # Нетерминал, если в списке
                        elif item.normal_form in ('"', '%'):
                            ana['PM,Nt,_'] = item.normal_form
                        # If all else fails, признаём неоднозначность
                        else:
                            for tag in ('PM,Nt,Tr', 'PM,Nt,_', 'PM,Tr,_'):
                                ana[tag] = item.normal_form

                else:
                    ana[pos] = item.normal_form

        ana_list.append(ana)

    for i, ana in enumerate(ana_list):
        for j, item in enumerate(ana):
            if item.startswith(('Pd', 'Pn', 'Cj', 'Pp', 'Pc')):
                items = list(ana.items())

                # Если мест. или мест.-пред., то отсекаем сущ. и прил.-пред.
                if item.startswith(('Pd', 'Pn')):
                    new_ana = [pair for pair in items if not pair[0].startswith(('Nn', 'Ap'))]
                # Если союз, пред. или част., то отсекаем сущ., прил., мест. и межд.
                else:
                    new_ana = [pair for pair in items if not pair[0].startswith(('Nn', 'Aj', 'Ap', 'Pn', 'Ij'))]

                ana_list[i] = OrderedDict(new_ana)
                break

    return ana_list


def process(inpt_dir, otpt_dir, gold):
    # Создаём директорию с выходными данными на случай, если её нет
    os.makedirs(otpt_dir, exist_ok=True)
    # Если директории со входными данными нет, тут возбуждается исключение
    os.chdir(inpt_dir)
    # Если директория есть, всё в порядке - программа начинает работу
    print('Please wait. Python is processing your data...')

    morph = MorphAnalyzer()
    files = glob.glob('*.txt')

    gold_file = open(gold, mode='r', encoding='utf-8', newline='')

    # Файлы с текстами обрабатываем поштучно
    for file in files:
        f = open(file, mode='r', encoding='windows-1251')
        lines = f.readlines()
        root = etree.Element('text')

        # Словарь для статистики
        stat = {'breaks on start': 0, 'breaks on end': 0, 'regular breaks': 0, 'fallbacks': 0, 'terminal <pc>\'s': 0}
        # Массив для фолбэков
        log_list = []

        for i, line in enumerate(lines):
            # Массив токенов
            line_tokens = nltk.word_tokenize(line)
            # Массив упорядоченных словарей вида {разбор: лемма}
            line_parses = format_parse_list([morph.parse(token) for token in line_tokens])

            p = etree.SubElement(root, 'p')
            p.set('n', str(i + 1))
            prev_ana = ''

            for j, ana in enumerate(line_parses):
                gold_file.seek(0)
                gold_reader = csv.reader(gold_file, delimiter=';')

                parses = list(ana.keys())
                check = False

                if parses[0].startswith('PM'):
                    elem = etree.SubElement(p, 'pc')
                else:
                    elem = etree.SubElement(p, 'w')
                elem.text = line_tokens[j]

                for row in gold_reader:

                    # Отсекаем триграммы с частотой < 4
                    if row[3] == '3':
                        break

                    # Если текущий элемент - однозначно терминальный ЗП, то искать с ним триграмму бессмысленно
                    if parses[0] == 'PM,Tr,_':
                        elem.set('ana', 'PM,Tr,_')
                        elem.set('lemma', ana['PM,Tr,_'])
                        prev_ana = 'PM,Tr,_'

                        stat['terminal <pc>\'s'] += 1
                        check = True

                    else:
                        # Если находимся в абсолютном начале предложения/чанка, рассматриваем левые биграммы
                        if j == 0 or prev_ana == 'PM,Tr,_':

                            # Фолбэк к pymorphy2, если текущий элемент последний в предложении
                            if j + 1 == len(line_parses):
                                break
                            else:
                                if row[0] in parses and row[1] in line_parses[j + 1]:
                                    elem.set('ana', row[0])
                                    elem.set('lemma', ana[row[0]])
                                    prev_ana = row[0]

                                    stat['breaks on start'] += 1
                                    check = True

                        # Если текущий элемент последний в предложении, рассматриваем правые биграммы
                        elif j + 1 == len(line_parses):
                            if prev_ana == row[1] and row[2] in parses:
                                elem.set('ana', row[2])
                                elem.set('lemma', ana[row[2]])
                                prev_ana = row[2]

                                stat['breaks on end'] += 1
                                check = True

                        # В других случаях рассматриваем полноценные триграммы
                        else:
                            if row[0] == prev_ana and row[1] in parses and row[2] in line_parses[j + 1]:
                                elem.set('ana', row[1])
                                elem.set('lemma', ana[row[1]])
                                prev_ana = row[1]

                                stat['regular breaks'] += 1
                                check = True

                    if check:
                        break

                # Фолбэк, если подходящей триграммы в золотом стандарте не нашлось
                if not check:
                    elem.set('ana', parses[0])
                    elem.set('lemma', ana[parses[0]])
                    prev_ana = parses[0]

                    # Фиксируем триграммы, на которых случился фолбэк
                    if j == 0:
                        log_data = '''\
{
    %s: %s,
    %s: %s,
};
''' % (str(line_tokens[j]), str(parses), str(line_tokens[j + 1]), str(list(line_parses[j + 1].keys())))
                    elif j + 1 == len(line_parses):
                        log_data = '''\
{
    %s: %s,
    %s: %s,
};
''' % (str(line_tokens[j - 1]), str(prev_ana), str(line_tokens[j]), str(parses))
                    else:
                        log_data = '''\
{
    %s: %s,
    %s: %s,
    %s: %s,
};
''' % (str(line_tokens[j - 1]), str(prev_ana), str(line_tokens[j]), str(parses), str(line_tokens[j + 1]), str(list(line_parses[j + 1].keys())))

                    log_list.append(log_data)
                    stat['fallbacks'] += 1

        # Шагаем в выходную директорию
        os.chdir(otpt_dir)

        # Записываем в XML
        with open(file[:-3] + 'xml', mode='w', encoding='utf-8') as out:
            xml = etree.tostring(root, method='xml', encoding='utf-8')
            pretty = parseString(xml).toprettyxml(indent='  ', encoding='utf-8')
            out.write(pretty.decode())

        # Записываем фолбэки в лог-файл
        with open(file[:-4] + '_log_trg.txt', mode='w', encoding='utf-8') as log:
            for line in log_list:
                log.write(str(line) + '\n')

        # Выдаём статистику по файлу
        print(file)
        for key in stat:
            print('    %d %s' % (stat[key], key))

        # Возвращаемся во входную директорию - к файлам на очереди
        os.chdir(inpt_dir)
        f.close()

    gold_file.close()


if __name__ == '__main__':
    try:
        with Profiler() as p:
            process(os.getcwd() + '\\inpt', os.getcwd() + '\\otpt', 'trigrams.csv')
    except FileNotFoundError:
        print('Error: source file missing.')
