import sys
import numpy as np
from androguard.core.bytecodes.apk import APK
from PIL import Image

def get_bytes(apk: APK, file_type: str) -> bytes:
    assert file_type in {".dex", ".so", ".xml"}
    for f in apk.get_files():
        if f.endswith(file_type):
            yield apk.get_file(f)

def generate_png(apk: APK, filename: str, file_type: str):
    assert file_type in {".dex", ".so", ".xml"}
    stream = bytes()
    for s in get_bytes(apk, file_type):
        stream += s
    current_len = len(stream)
    image = Image.frombytes(mode='L', size=(1, current_len), data=stream)
    image = image.resize((1, 128*128), resample=Image.BILINEAR)
    filename = filename.split('.')[0]
    image.save(f"{filename}{file_type}.png")

    return image

def generate_color_image(apk, filename):
    dex_img = generate_png(apk, filename, '.dex')
    xml_img = generate_png(apk, filename, '.xml')
    try:
        so_img  = generate_png(apk, filename, '.so')
    except:
        so_img = np.zeros(dex_img.shape)
    dex_img, so_img, xml_img = np.array(dex_img), np.array(so_img), np.array(xml_img)
    H, W = dex_img.shape
    image = np.zeros((H, W, 3))
    image[:, :, 0] = dex_img
    image[:, :, 1] = so_img
    image[:, :, 2] = xml_img
    filename = filename.split('.')[0]
    color_image = Image.fromarray(image.astype(np.uint8))
    color_image.save(f"{filename}.color.png")
    

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise Exception("[!] Usage: python3 apk2images.py APK")
    else:
        filename = sys.argv[1]
    try:
        apk = APK(filename)
        generate_color_image(apk, filename)
        print(f"Images successfully generated from {filename}")
    except Exception as e:
        print("[!] An exception occured with: {}".format(filename))
        print("Exception: {}".format(e))