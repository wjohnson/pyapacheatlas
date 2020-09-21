import configparser
import os

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("./samples/migrateADC/config.ini")

    folders = [
        config["Default"]["RootFolder"], config["Default"]["EntitiesFolder"],
        config["Default"]["EntitiesRemapped"], config["Default"]["GlossaryFolder"],
        config["Default"]["GlossaryRemapped"], config["Default"]["RelationshipsFolder"],
        config["Default"]["RelationshipsRemapped"]
    ]
    for folder in folders:
        if not os.path.exists(folder):
            os.mkdir(folder)
        else:
            print(f"{folder} exists already.")
    