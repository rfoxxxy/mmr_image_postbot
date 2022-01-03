import os
import logging

from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot, types, filters
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.types import InputFile

from config import TOKEN
from states import UploadState

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(filters.Command("create"))
async def process_create_command(message: types.Message):
    await message.reply(
        "Отправьте нужное изображение и в описание "
        "укажите наименование релиза и имя исполнителя через |\n\n"
        "<b>Например:</b> <code>Снова я напиваюсь|ИванЗоло2004</code>"
        "\n\nДля отмены используйте /cancel")
    await UploadState.uploading_photo.set()


@dp.message_handler(filters.CommandStart())
async def process_start_command(message: types.Message):
    await message.reply(
        "Привет. Используй команду /create и я сделаю изображение для поста в паблик MMR Aggregator"
    )


@dp.message_handler(filters.Command("cancel"), state="*")
async def process_cancel_command(message: types.Message, state: FSMContext):
    if not await state.get_state():
        return await message.reply("Нечего отменять...")
    else:
        await state.finish()
        return await message.reply("Успешно!")


@dp.message_handler(content_types=types.ContentTypes.PHOTO,
                    state=UploadState.uploading_photo)
async def process_photo(message: types.Message, state: FSMContext):
    input_img = 'input_' + str(message.chat.id) + '.png'
    output_img = 'output_' + str(message.chat.id) + '.png'

    await message.photo[-1].download(destination_file=input_img)

    separator = "|"
    arguments = message.caption
    if not arguments:
        return await message.reply(
            "Отправьте нужное изображение и в описание "
            "укажите наименование релиза и имя исполнителя через |\n\n"
            "<b>Например:</b> <code>Снова я напиваюсь|ИванЗоло2004</code>"
            "\n\nДля отмены используйте /cancel")
    args = arguments.split(separator)

    if len(args) < 2:
        os.remove(input_img)
        return await message.reply("Вы пропустили один аргумент")
    else:
        if os.path.isfile(input_img):
            await create_image(args[0], args[1], input_img, output_img)
            await message.reply("Отправляю изображение: " + args[0] + " - " +
                                args[1])
            await types.ChatActions.upload_document(1)
            await message.answer_document(InputFile(output_img))
        else:
            await message.reply(
                "Изображение обложки не найдено! Попробуйте отправить его заново"
            )
    os.remove(output_img)
    os.remove(input_img)
    await state.finish()


async def create_image(title: str, artist: str, inputfile: str,
                       outputfile: str):
    width = 3840
    # height = 2160
    title_font = ImageFont.truetype('Montserrat-ExtraBoldItalic.ttf', 100)
    artist_font = ImageFont.truetype('Montserrat-Black.ttf', 100)
    cover = Image.open(inputfile)
    background = Image.open('back.png')
    small_cover = cover.resize((1280, 1280), Image.ANTIALIAS)
    round_corner = circle_corner(small_cover, 20)
    background.paste(round_corner, (1280, 440), round_corner)
    draw_title = ImageDraw.Draw(background)

    title_width = draw_title.textsize(title, title_font)
    artist_width = draw_title.textsize(artist, artist_font)

    draw_title.text(((width - title_width[0]) / 2, 270),
                    title,
                    font=title_font,
                    fill=("#000000"))

    draw_title.text(((width - artist_width[0]) / 2, 160),
                    artist,
                    font=artist_font,
                    fill=('#000000'))

    background.save(outputfile)


def circle_corner(img: Image.Image, radius: int):
    circle = Image.new('L', (radius * 2, radius * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)

    img = img.convert("RGBA")
    w, h = img.size

    alpha = Image.new('L', img.size, 255)
    alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
    alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (w - radius, 0))
    alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)),
                (w - radius, h - radius))
    alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, h - radius))

    img.putalpha(alpha)
    return img


if __name__ == '__main__':
    executor.start_polling(dp)
