import os
from lxml import etree


def process(inpt_dir, file):
    """
    Просто программа для проверки gold на синтаксическую вшивость
    Если что-то не парсится, то выдаётся исключение с локализацией
    """

    os.chdir(inpt_dir)
    inpt = open(file, mode='r', encoding='utf-8')

    parser = etree.XMLParser(huge_tree=True)
    etree.parse(inpt, parser)


if __name__ == '__main__':
    try:
        process(os.getcwd() + '\\temp', 'LAW_NEW.xml')
    except FileNotFoundError:
        print('Error: source file missing.')
