import os
import time
import logging


from PIL import Image, ImageFilter, ImageDraw, ImageFont
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types import InputFile


from config import TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(content_types=['photo'])
async def download_photo(message: types.Message):
    photo = message.photo.pop()
    await photo.download('input_' + str(message.chat.id) + '.png')
    await message.reply("Теперь введите команду /create таким образом\n/create Наименование_релиза|Исполнители")

@dp.message_handler(commands=['start'])
async def poxui(message: types.Message):
    await message.reply("Привет. Отправь обложку релиза и я сделаю изображение для поста в паблик MMR Aggregator")

@dp.message_handler(commands=['create'])
async def process_start_command(message: types.Message, state: FSMContext):
    separator = "|"
    arguments = message.get_args()
    args = arguments.split(separator)

    if len(args) < 2:
        await message.reply("Вы пропустили один аргумент")
    else:
        time.sleep(1)
        input_img = 'input_' + str(message.chat.id) + '.png'
        output_img = 'output_' + str(message.chat.id) + '.png'
        if os.path.isfile(input_img) == True:
            createimage(args[0], args[1], input_img, output_img)
            await message.reply("Отправляю изображение: " + args[0] + " - " + args[1])
            sendfile = open(output_img, "rb")
            await bot.send_document(message.chat.id, sendfile)
            os.remove(output_img)
            os.remove(input_img)
        else:
            await message.reply("Для начала отправьте изображение обложки")


def createimage(title, artist, inputfile, outputfile):
    width = 3840
    height = 2160
    titlefont = ImageFont.truetype('Montserrat-ExtraBoldItalic.ttf', 100)
    artistfont = ImageFont.truetype('Montserrat-Black.ttf', 100)
    cover = Image.open(inputfile)
    background = Image.open('back.png')
    small_cover = cover.resize((1280,1280),Image.ANTIALIAS)
    aboba = circle_corner(small_cover,20)
    background.paste(aboba, (1280, 440), aboba)
    drawtitle = ImageDraw.Draw(background)

    titlewidth = drawtitle.textsize(title, titlefont)
    artistwidth = drawtitle.textsize(artist, artistfont)

    drawtitle.text(
        ((width-titlewidth[0])/2,270),
        title,
        font=titlefont,
        fill=("#000000")
        )

    drawtitle.text(
        ((width-artistwidth[0])/2,160),
        artist,
        font=artistfont,
        fill=('#000000')
        )
    
    background.save(outputfile)

def circle_corner(img, radii):
    circle = Image.new('L', (radii * 2, radii * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)

    img = img.convert("RGBA")
    w, h = img.size

    alpha = Image.new('L', img.size, 255)
    alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))
    alpha.paste(circle.crop((radii, 0, radii * 2, radii)), (w - radii, 0))
    alpha.paste(circle.crop((radii, radii, radii * 2, radii * 2)), (w - radii, h - radii))
    alpha.paste(circle.crop((0, radii, radii, radii * 2)), (0, h - radii))

    img.putalpha(alpha)
    return img
    




if __name__ == '__main__':
    executor.start_polling(dp)
