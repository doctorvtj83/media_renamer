import argparse
import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from pillow_heif import HeifImagePlugin
import geopy
from geopy.geocoders import Nominatim

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

    def get_geo(self,exif):
        for key, value in TAGS.items():
            if value == "GPSInfo":
                break
        gps_info = exif.get_ifd(key)
        return {
            GPSTAGS.get(key, key): value
            for key, value in gps_info.items()
        }

    def DMS2DD(self,dms,direction):
        dd = dms[0] + (dms[1]/60.) + (dms[2]/3600.)
        if direction in ['W','S']:
            dd = -dd
        
        return str(dd)

    def retrieve_geo_and_time_from_meta(self):
        for file in self.files:
            file["CreateTimestamp"] = False
            file["Geo"] = False
            
            if file['Type'] in ['.jpg','.jpeg','.png','.heic']:
                fp = self.path + '/' +file['Name']
                with Image.open(fp) as img:
                    exif = img.getexif()
                    if exif:
                        labeled_exif = self.get_labeled_exif(exif)
                        if 'DateTime' in labeled_exif:
                            file["CreateTimestamp"] = labeled_exif['DateTime']
                        
                        geo = self.get_geo(exif)
                        if geo:
                            file["Geo"] = geo

    def get_coordinates(self,gps_info):
        return [
            self.DMS2DD(gps_info['GPSLatitude'],gps_info['GPSLatitudeRef']),
            self.DMS2DD(gps_info['GPSLongitude'],gps_info['GPSLongitudeRef'])
            ]

    def get_location(self):
        locator = Nominatim(user_agent='myGeocoder')
        for file in self.files:
            print(file['Name'])
            file['Location'] = False
            
            if file["Geo"]:    
                coordinates = self.get_coordinates(file["Geo"])
                file['Location'] = locator.reverse(coordinates)


    def create_filename(self):
        pass   
        # 2021-10-13-14.35 - dateiname_beispiel.pdf

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = 'MediaRenamer',
        description='Renaming media files in a given directory',
    )

    parser.add_argument('-p','--path',required=True)

    args = parser.parse_args()

    R = Renamer(args.path)
    R.get_files()
    R.retrieve_geo_and_time_from_meta()
    R.get_location()

    print(R.files)