import glob
import os
import re
from lxml import etree
from pymorphy2 import MorphAnalyzer


def tokenise(r):
    """
    Токенизатор проще некуда: выдаёт все непробельные и непустые последовательности, разделённые любыми символами
    типа не-alphanumeric. При этом не разделяет последовательности по дефису (плащ-палатка) и нижнему подчёркиванию.
    Вместо собственной функции можно было бы использовать встроенный модуль pymorphy2.tokenizers (работает абсолютно
    так же), однако тамошняя функция - не генератор, а следовательно, работает медленнее
    """
    regex = re.compile(r'([^\w_-])')

    for t in regex.split(r):
        if t and not t.isspace():
            yield t


def set_ana(w, t):

    if ',' in t:
        typ = t[:t.index(',')]

        if ' ' in t:
            sub = t[t.index(',') + 1:t.index(' ')]
            ana = t[t.index(' ') + 1:]
        else:
            sub = t[t.index(',') + 1:]
            ana = ''

    else:
        typ = t[:]
        sub = ''
        ana = ''

    w.set('type', typ)
    if sub:
        w.set('subtype', sub)
    if ana:
        w.set('ana', ana)


if __name__ == '__main__':
    try:
        inpt_dir = os.getcwd() + '\\inpt'
        otpt_dir = os.getcwd() + '\\otpt'

        # Создаём директорию с выходными данными на случай, если её нет
        if not os.path.exists(otpt_dir):
            os.makedirs(otpt_dir)

        # Если директории со входными данными нет, тут возбуждается исключение
        os.chdir(inpt_dir)

        # Если директория есть, всё в порядке - программа начинает работу
        print('Please wait. Python is processing your data...')
        morph = MorphAnalyzer()
        files = glob.glob('*.txt')

        # Файлы с текстами обрабатываем поштучно
        for file in files:
            f = open(file, mode='r', encoding='utf-8')
            raw = f.read()
            root = etree.Element('TEI')

            # Сюда пойдёт метатекстовая информация. Пока только не очень понятно, какая
            header = etree.SubElement(root, 'teiHeader')

            # Приступаем к обработке текста
            text = etree.SubElement(root, 'text')

            for token in tokenise(raw):
                # Берём разбор с наибольшим значением score (where applicable)
                parse = morph.parse(token)[0]
                tag = str(parse.tag)

                # Всё, что не является пунктуацией, - т. е. нормальные словоформы плюс токены из латинских букв
                # (тип LATN), числа (NUMB либо ROMN) и неразобранные единицы (UNKN) - заключаем в тег <w></w>.
                # Часть речи записываем в атрибут type, в subtype и ana - соответственно граммемы (или нечто вроде)
                # классифицирующих и словоизменительных категорий (опять же, where applicable).
                # NB! Это решение *временное*: поиск по граммемам работает, но хромает на обе ноги.
                # Потом надо реализовать через feature structures
                if not tag.startswith('PNCT'):
                    word = etree.SubElement(text, 'w')
                    word.text = token
                    word.set('lemma', parse.normal_form)
                    set_ana(word, tag)

                # С пунктуацией всё просто
                else:
                    pc = etree.SubElement(text, 'pc')
                    pc.text = token

            # Шагаем в выходную директорию
            os.chdir(otpt_dir)

            # Записываем в XML. С декларацией; когда окончательно определимся метаданными и составом тегов,
            # сгенерируем схему DTD (?) и добавим DOCTYPE
            with open(file[:-3] + 'xml', mode='w', encoding='utf-8') as out:
                xml = etree.tostring(root, method='xml', encoding='utf-8', xml_declaration=True, pretty_print=True)
                out.write(xml.decode())

            # Возвращаемся во входную директорию
            os.chdir(inpt_dir)

            f.close()

    except FileNotFoundError:
        print('Error: source data directory missing.')
