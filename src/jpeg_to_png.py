import sys

from PIL import Image


def main():
    with Image.open(sys.stdin.buffer) as image:
        if image.format != "JPEG":
            raise ValueError("Ожидалось изображение в формате JPEG")

        image.convert("RGB").save(sys.stdout.buffer, format="PNG")


if __name__ == "__main__":
    main()
