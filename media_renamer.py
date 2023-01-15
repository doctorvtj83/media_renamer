import argparse

class Renamer:
    def __init__(self,path):
        self.path = path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = 'MediaRenamer',
        description='Renaming media files in a given directory',
    )

    parser.add_argument('-p','--path',required=True)

    args = parser.parse_args()

    R = Renamer(args.path)