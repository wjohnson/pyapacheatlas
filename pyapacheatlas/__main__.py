import argparse
import configparser

if __name__ == "__main__":
    """
    This is an experimental feature that will allow users to make the excel
    template directly from the CLI rather than instantiating an ExcelReader
    in the Python shell.

    Use `--config` to provide a config.ini file with a `[DEFAULT]` section
    header and specify any customizations. See `ExcelReader.make_template`
    for list of possible parameters / configuration settings.
    """
    from .readers import ExcelConfiguration, ExcelReader
    from . import __version__
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--make-template",
        help="Indicates where the excel template should be created")
    parser.add_argument(
        "-c", "--config",
        help="The location of the configuration file")
    parser.add_argument(
        "-cs", "--config-section",
        help="The config file's section header to be used. Defaults to DEFAULT",
        default="DEFAULT")
    parser.add_argument(
        "-de", "--include-deprecated",
        help="Include deprecated tabs in the excel template",
        action="store_true"
    )
    parser.add_argument(
        "--version",
        help="Display the version of your PyApacheAtlas package",
        action="store_true")
    args = parser.parse_args()

    config = {}
    if args.version:
        print(__version__)
        exit(0)

    template_config = {}
    if args.config:
        config = configparser.ConfigParser()
        config.read(args.config)
        if args.config_section not in config:
            raise RuntimeError(
                f"In your config.ini, please specify a {args.config_section} section or update your --config-section parameter.")
        template_config = config[args.config_section]
    
    if args.include_deprecated:
        template_config["include_deprecated"] = args.include_deprecated

    if args.make_template:
        ExcelReader.make_template(args.make_template, **template_config)
        print(f"Template successfully written to {args.make_template}")
