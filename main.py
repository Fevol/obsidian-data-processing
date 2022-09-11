import releases
import themes
import plugins

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--releases', action='store_true', help='Graph releases')
    parser.add_argument('-t', '--themes', action='store_true', help='Graph themes')
    parser.add_argument('-p', '--plugins', action='store_true', help='Graph plugins')
    parser.add_argument('-a', '--all', action='store_true', help='Graph all')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-d', '--download', action='store_true', help='Fetch most recent data from GitHub, if not enabled, most recent processed data will be used')
    group.add_argument('-f', '--file', type=str, help='Provide json file to process, used to process older data, format file as XXXXXXXXX-YYYY-MM-DD.json')

    parser.add_argument('-s', '--save', action='store_true', help='Save fetched and processed data to file')

    parser.add_argument('-chr', '--chronological', action='store_true', help='Graph in chronological order (THEMES/PLUGINS/RELEASES)')
    parser.add_argument('-sort', '--sorted', action='store_true', help='Graph sorted by total downloads (THEMES/PLUGINS/RELEASES)')
    parser.add_argument('-dif', '--difference', action='store_true', help='Graph amount of downloads between all stored intervals (THEMES/PLUGINS)')
    parser.add_argument('-norm', '--normalize', action='store_true', help='Normalize release version data to 100% (RELEASES)')
    parser.add_argument('-c', '--complete', action='store_true', help='Graph all data (THEMES/PLUGINS/RELEASES)')

    parser.add_argument('-l', '--logarithm', action='store_true', help='Plot downloads on logarithmic scale')

    args = parser.parse_args()

    configuration = {
        "download": args.download,
        "provided_file": args.file,
        "save_data": args.save,
        "chronological": args.chronological or args.complete,
        "sorted": args.sorted or args.complete,
        "difference": args.difference or args.complete,
        "normalize": args.normalize or args.complete,
        'logarithm': args.logarithm
    }


    if args.themes or args.all:
        themes.graph_themes(configuration)
    if args.plugins or args.all:
        plugins.graph_plugins(configuration)
    if args.releases or args.all:
        releases.graph_releases(configuration)