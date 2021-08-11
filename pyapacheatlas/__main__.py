import argparse
import configparser

if __name__ == "__main__":
    from .readers import ExcelConfiguration, ExcelReader
    from . import __version__
    parser = argparse.ArgumentParser()
    parser.add_argument("--make-template", help="Indicates where the excel template should be created")
    parser.add_argument("-c", "--config", help="The location of the configuration file")
    parser.add_argument("--version", help="Display the version of your PyApacheAtlas package",action="store_true")
    args = parser.parse_args()

    config = None
    if args.version:
        print(__version__)
        exit(0)
    
    if args.config:
        config = configparser.ConfigParser()
        config.read(args.config)

    if args.make_template:
        print('Made it here')
        ExcelReader.make_template(args.make_template)
