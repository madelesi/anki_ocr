from pathlib import Path
import sys
import pytesseract
from PIL import Image
import random
import genanki
import os

img_file_extensions = ['.png', '.jpg']


def main(img_dir_name=None, deck_name=None, ocr=False):
    if len(sys.argv) > 1:  # In other words, if arguments included from command-line
        img_dir_name, deck_name = get_arguments()

    # Get path object for images folder
    img_path_object = Path(img_dir_name)

    # Group images to Q,A pairs
    q_a_pairs = pair_images(img_path_object)

    # Initialize deck
    deck_id = random.randrange(1 << 30, 1 << 31)
    media_files = []
    my_deck = genanki.Deck(deck_id, deck_name)

    # convert Q, A image pair to text(through OCR), and add to deck
    if ocr:
        q_a_text_pairs = convert_q_a_pairs(q_a_pairs)
        add_tuples_anki_deck(my_deck, q_a_text_pairs)

    if not ocr:
        # We have to store all media files in a list to add to our package.
        for q_path, a_path in q_a_pairs:
            media_files.append(str(q_path.absolute()))
            media_files.append(str(a_path.absolute()))
        add_tuples_anki_deck(my_deck, q_a_pairs, media=True)

    # Package deck to output file
    my_package = genanki.Package(my_deck)
    my_package.media_files = media_files
    my_package.write_to_file(f'{deck_name}.apkg')
    print(f'conversion complete, packaged to {deck_name}.apkg')


def get_arguments():
    # Verify Correct number of arguments and return them
    try:
        img_dir_name = sys.argv[1]
        deck_name = sys.argv[2]
    except IndexError:
        raise ValueError('Usage: python anki_ocr_py img_directory deck_name')
    return img_dir_name, deck_name


def convert_q_a_pairs(q_a_pairs):
    q_a_text_pairs = []
    for q, a in q_a_pairs:
        q_a_text_pair = image_to_text(q), image_to_text(a)
        q_a_text_pairs.append(q_a_text_pair)
    return q_a_text_pairs


def add_tuples_anki_deck(anki_deck, tuples_list, media=False):
    if not media:
        for q_text, a_text in tuples_list:
            add_note_anki_deck(anki_deck, q_text, a_text)
    if media:
        for q_file, a_file in tuples_list:
            add_img_note_anki_deck(anki_deck, q_file, a_file)


def pair_images(img_path_object):
    # Make Sure all files in directory are images (JPEG/PNG)
    img_list = []
    for img in img_path_object.glob('*'):
        if img.suffix not in img_file_extensions:
            raise ValueError(
                'All files in image directory must be PNG/JPEG format')
        img_list.append(img)

    # Sort img_list
    img_list.sort(key=os.path.getmtime)

    # Verify an even number of images to create pairs
    if len(img_list) % 2 != 0:
        raise ValueError('Number of images must be even(multiple of 2)')
    q_a_pairs = list_to_tuples(img_list, 2)
    return q_a_pairs


def list_to_tuples(list_to_pair, pair_length):
    # Create N copies of the same iterator
    it = [iter(list_to_pair)] * pair_length
    # Unpack the copies of the iterator, and pass them as parameters to zip
    return list(zip(*it))


def image_to_text(filename):
    text = pytesseract.image_to_string(Image.open(filename))
    return text


def add_note_anki_deck(deck, q_text, a_text):
    # Basic anki note model
    model_id = random.randrange(1 << 30, 1 << 31)
    my_model = genanki.Model(
        model_id,
        'Simple Model',
        fields=[
            {'name': 'Question'},
            {'name': 'Answer'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{Question}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
            },
        ])

    my_note = genanki.Note(model=my_model, fields=[q_text, a_text])
    deck.add_note(my_note)
    print(f'just added note with q_text: {q_text}, a_text: {a_text}')


def add_img_note_anki_deck(deck, q_file, a_file):
    model_id = random.randrange(1 << 30, 1 << 31)
    my_model = genanki.Model(
        model_id,
        'Simple Model with Media',
        fields=[
            {'name': 'QuestionImage'},
            {'name': 'AnswerImage'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{QuestionImage}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{AnswerImage}}',
            },
        ])
    my_note = genanki.Note(model=my_model, fields=[f"<img src={q_file.name}>", f"<img src={a_file.name}>"])
    deck.add_note(my_note)
    print(f'Added note with q_img: {q_file.name}, a_img: {a_file.name}')


if __name__ == '__main__':
    main()