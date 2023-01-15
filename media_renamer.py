import argparse
import os
from PIL import Image
from PIL.ExifTags import TAGS
from pillow_heif import HeifImagePlugin

class Renamer:
    def __init__(self,path):
        self.path = path

    def get_files(self):
        self.files = [ {'Name': el, 'Type' : os.path.splitext(el)[1].lower()} for el in os.listdir(self.path)]

    def get_labeled_exif(self,exif):
        return {
        TAGS.get(key, key): value
        for key, value in exif.items()
    }

    def retrieve_datetime_from_meta(self):
        for file in self.files:
            file["CreateTimestamp"] = False
            
            if file['Type'] in ['.jpg','.jpeg','.png','.heic']:
                fp = self.path + '/' +file['Name']
                with Image.open(fp) as img:
                    exif = img.getexif()
                    if exif:
                        labeled_exif = self.get_labeled_exif(exif)
                        if 'DateTime' in labeled_exif:
                            file["CreateTimestamp"] = labeled_exif['DateTime']

        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = 'MediaRenamer',
        description='Renaming media files in a given directory',
    )

    parser.add_argument('-p','--path',required=True)

    args = parser.parse_args()

    R = Renamer(args.path)
    R.get_files()
    R.retrieve_datetime_from_meta()

    print(R.files)