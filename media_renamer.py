import argparse
import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from pillow_heif import HeifImagePlugin
import geopy
from geopy.geocoders import Nominatim
from datetime import datetime as dt
import platform
import pandas as pd
import time

class Renamer:
    def __init__(self,path):
        self.path = path
        self.target_tags = set(['GPSLatitude','GPSLatitudeRef','GPSLongitude','GPSLongitudeRef'])
        self.dateformat = '%Y:%m:%d %H:%M:%S'

    def get_files(self):
        self.files = [ {'Name': el, 'Type' : os.path.splitext(el)[1].lower()} for el in os.listdir(self.path)]
        print(f"{len(self.files)} files found in directory")
        self.no_files = len(self.files)
        print("")

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
        print("Retrieving Creation date and location")
        i = 0
        for file in self.files:
            i+=1
            print(f"File {i}/{self.no_files}",end='\r')
            file["CreateTimestamp"] = False
            file["Geo"] = False
            
            if file['Type'] in ['.jpg','.jpeg','.png','.heic']:
                fp = self.path + '/' +file['Name']
                with Image.open(fp) as img:
                    exif = img.getexif()
                    if exif:
                        labeled_exif = self.get_labeled_exif(exif)
                        if 'DateTime' in labeled_exif:
                            file["CreateTimestamp"] = dt.strptime(labeled_exif['DateTime'],self.dateformat)
                        
                        geo = self.get_geo(exif)
                        if geo:
                            file["Geo"] = geo
        
        print("")
        print("")

    def get_coordinates(self,gps_info):
        return [
            self.DMS2DD(gps_info['GPSLatitude'],gps_info['GPSLatitudeRef']),
            self.DMS2DD(gps_info['GPSLongitude'],gps_info['GPSLongitudeRef'])
            ]

    def get_location(self):
        locator = Nominatim(user_agent='myGeocoder')
        for file in self.files:
            file['Location'] = False
            file['City'] = False
            file['County'] = False
            
            if file["Geo"]:
                if self.target_tags.issubset(set(file['Geo'].keys())):
                    coordinates = self.get_coordinates(file["Geo"])
                    try:
                        loc = locator.reverse(coordinates)
                        file['Location'] = str(loc).replace(",","").replace(" ","_")
                        if 'address' in loc.raw:
                            if 'city' in loc.raw['address']:
                                file['City'] = loc.raw['address']['city']

                            if 'county' in loc.raw['address']:
                                file['County'] = loc.raw['address']['county']
                            
                        time.sleep(1)
                    except:
                        print(f"Request timeout for {file['Name']}")


    def file_create_date(self,path_to_file):
        if platform.system() == 'Windows':
            return os.path.getctime(path_to_file)
        else:
            stat = os.stat(path_to_file)
            try:
                return stat.st_birthtime
            except AttributeError:
                # We're probably on Linux. No easy way to get creation dates here,
                # so we'll settle for when its content was last modified.
                return stat.st_mtime

    def create_date_from_files(self):
        print("Creating remaining dates from filesystem")
        i = 0
        for file in self.files:
            i += 1
            print(f"File {i}/{self.no_files}",end='\r')
            fp = self.path + '/' +file['Name']
            if not file["CreateTimestamp"]:
                file["CreateTimestamp"] = dt.fromtimestamp(self.file_create_date(fp))

        print("")
        print("")

    def create_filename(self):
        for file in self.files:
            file["New_Name"] = False
            if file["CreateTimestamp"]:
                cd = file["CreateTimestamp"]
                new_name = f"{cd.year}-{cd.month}-{cd.day}-{cd.hour}.{cd.minute} - "
                if file['Type'] in ['.jpg','.jpeg','.png','.heic']:
                    if file['Location']:
                        new_name = new_name + file['Location']
                    else:
                        new_name = new_name + "Foto"
                    
                    file["New_Name"] = new_name + file['Type']
                
                elif file['Type'] in ['.mov','.mp4','.mp4','.m4v']:
                    new_name = new_name + 'Film'
                    file["New_Name"] = new_name + file['Type']

        # 2021-10-13-14.35 - dateiname_beispiel.pdf
    def rename_files(self):
        for f in self.files:
            if f["New_Name"]:
                old = self.path + '/' + f['Name']
                new = self.path + '/' + f["New_Name"]
                os.rename(old,new)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = 'MediaRenamer',
        description='Renaming media files in a given directory',
    )

    parser.add_argument('-p','--path',required=True)
    parser.add_argument('--dry_run',default='True',required=False)
    parser.add_argument('--results',default='./output',required=False)

    args = parser.parse_args()

    R = Renamer(args.path)
    R.get_files()
    R.retrieve_geo_and_time_from_meta()
    R.get_location()
    R.create_date_from_files()
    R.create_filename()

    if args.dry_run == 'True':
        df = pd.DataFrame.from_records(R.files)
        fp = args.results + '.csv'
        df.to_csv(fp)
    else:
        print("Renaming files")
        print("")
        R.rename_files()

print("Program Finished")
