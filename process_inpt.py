import glob
import os
import nltk
from xml.etree import ElementTree as etree
from xml.dom.minidom import parseString
from pymorphy2 import MorphAnalyzer
from tags import pymorphy_all


def format_tag(t):

    if t in pymorphy_all:
        return pymorphy_all[t]

    return '_'


def format_parse(pt):
    ana = []

    for parse in pt:
        pos = format_tag(parse.tag.POS)

        animacy = format_tag(parse.tag.animacy)
        case = format_tag(parse.tag.case)
        number = format_tag(parse.tag.number)
        gender = format_tag(parse.tag.gender)
        person = format_tag(parse.tag.person)
        aspect = format_tag(parse.tag.aspect)

        if pos == 'Nn':

            if case != 'Ac':
                animacy = '_'

            if number == 'Pl':
                gender = '_'

        elif pos == 'Vb':

            if person == '_' and number == 'Pl':
                    gender = format_tag(parse.tag.person)

        elif pos in ('Pt', 'Vp', 'Aj', 'Ap', 'Pn'):

            if number == 'Pl':
                gender = format_tag(parse.tag.gender)

        elif pos == '_':
            pos = format_tag(str(parse.tag).split(',')[0])

        if all(grammeme == '_' for grammeme in (animacy, case, number, gender, person, aspect)):
            ana += [pos]
        else:
            ana += [','.join((pos, animacy, case, number, gender, person, aspect))]

    # Если мест.-пред., то отсекаем сущ.
    for i, p in enumerate(ana):
        if p.startswith('Pd'):
            ana = ana[:i + 1] + [p for p in ana[i + 1:] if not p.startswith('Nn')]

    # Если союз, пред. или част., то отсекаем сущ., прил., мест. и межд.
    for i, p in enumerate(ana):
        if p.startswith(('Cj', 'Pp', 'Pc')):
            ana = ana[:i + 1] + [p for p in ana[i + 1:] if not p.startswith(('Nn', 'Aj', 'Pn', 'Ij'))]

    result = []
    for item in ana:
        if item not in result:
            result += [item]

    return result


def process(inpt_dir, otpt_dir):
    # Создаём директорию с выходными данными на случай, если её нет
    os.makedirs(otpt_dir, exist_ok=True)
    # Если директории со входными данными нет, тут возбуждается исключение
    os.chdir(inpt_dir)
    # Если директория есть, всё в порядке - программа начинает работу
    print('Please wait. Python is processing your data...')

    morph = MorphAnalyzer()
    files = glob.glob('*.txt')

    # Файлы с текстами обрабатываем поштучно
    for file in files:
        f = open(file, mode='r', encoding='utf-8')
        root = etree.Element('text')
        lines = f.readlines()

        for line in lines:
            p = etree.SubElement(root, 'p')

            for token in nltk.word_tokenize(line):
                # Форматируем разбор
                parse_total = morph.parse(token)
                ana = format_parse(parse_total)

                ana = ' ; '.join(ana)

                # Всё, что не является пунктуацией, - т. е. нормальные словоформы плюс токены из латинских букв
                # (тип LATN), числа (NUMB либо ROMN) и неразобранные единицы (UNKN) - заключаем в тег <w></w>
                if ana != 'PM':
                    w = etree.SubElement(p, 'w')
                    w.text = token
                    # w.set('lemma', parse.normal_form)
                    w.set('ana', ana)

                # С пунктуацией всё просто
                else:
                    pc = etree.SubElement(p, 'pc')
                    pc.text = token

        # Шагаем в выходную директорию
        os.chdir(otpt_dir)

        # Записываем в XML
        with open(file[:-3] + 'xml', mode='w', encoding='utf-8') as out:
            xml = etree.tostring(root, method='xml', encoding='utf-8')
            pretty = parseString(xml).toprettyxml(indent='  ', encoding='utf-8')
            out.write(pretty.decode())

        # Возвращаемся во входную директорию - к файлам на очереди
        os.chdir(inpt_dir)
        f.close()


if __name__ == '__main__':
    try:
        process(os.getcwd() + '\\inpt', os.getcwd() + '\\otpt')
    except FileNotFoundError:
        print('Error: source data directory missing.')
