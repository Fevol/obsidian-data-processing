import pandas as pd
import re
import os
import datetime
import json
import numpy as np
import seaborn as sns

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from util import download_from_url, save_dataframe, generate_color_palette, draw_bar_graph


def graph_bar_chart(df, linux_downloads, windows_downloads, mac_downloads):
    ind = np.arange(len(linux_downloads))
    sns.set(style="whitegrid")

    plt.bar(ind, linux_downloads, 0.6, color='#d24413', label='linux')
    plt.bar(ind, windows_downloads, 0.6, color='#0072cb', label='windows', bottom=linux_downloads)
    plt.bar(ind, mac_downloads, 0.6, color='#06cb98', label='mac', bottom=linux_downloads + windows_downloads)

    # Get unique version values
    versions = df['version'].unique()
    plt.xlim(-0.5, len(versions) - .5)

    # Set x-axis labels with rotation
    plt.xticks(ind, versions, rotation=45)

    patches = [mpatches.Patch(color='#d24413', label="Linux"),
               mpatches.Patch(color='#0072cb', label="Windows"),
               mpatches.Patch(color='#06cb98', label="MacOS")]

    plt.legend(handles=patches, loc='upper left')
    plt.show()


def graph_releases(configuration):
    if configuration['download'] or configuration['provided_file']:
        if configuration['download']:
            data = download_from_url(
                "https://api.github.com/repos/obsidianmd/obsidian-releases/releases",
                "raw-data/releases.json" if configuration['save_data'] else "")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        else:
            with open(configuration['provided_file'], 'r') as f:
                data = f.read()

                # Find if filename contains timestamp
                if re.search(r'\d{4}.?\d{2}.?\d{2}', configuration['provided_file']):
                    timestamp = re.search(r'\d{4}.?\d{2}.?\d{2}', configuration['provided_file']).group(0) + 'T00-00-00'
                else:
                    timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(configuration['provided_file'])).strftime(
                        "%Y-%m-%dT%H-%M-%S")

        entries = []
        for release in data:
            version = release['name']

            # Turn 0.12.4 to 0.12.04 if last digit is single number
            version = '.'.join([s.zfill(2) if s != '0' else '0' for s in version.split('.')])

            created_at = release['created_at']
            # Convert 2022-07-26T18:40:50Z datetime to epoch
            created_at = datetime.datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ').timestamp()

            for i, asset in enumerate(release['assets']):
                file_type = asset['browser_download_url'].split('/')[-1]
                file_type = file_type[re.search(r"\d+.\d+.\d+", file_type).end()+1:]

                operation_system = ''
                if(file_type.endswith('asar.gz')):
                    continue
                elif (file_type.endswith('dmg')):
                    operation_system = 'mac'
                elif (file_type.endswith('exe')):
                    operation_system = 'windows'
                else:
                    operation_system = 'linux'

                downloads = asset['download_count']
                entries.append([version, operation_system, downloads, file_type, created_at])
        df = pd.DataFrame(entries, columns=['version', 'os', 'downloads', 'type', 'created_at'])

        # To csv with timestamp of current date
        if configuration['save_data']:
            save_dataframe(df, "processed-data/releases.csv", timestamp)
    else:
        # Get last fetched releases.json file in the raw folder
        theme_files = [f for f in os.listdir("processed-data") if re.match(r"releases_\d{4}.*\.csv", f)]
        theme_files.sort()

        if not theme_files:
            print("No releases.json file found in processed data folder")
            return
        else:
            with open(os.path.join("processed-data", theme_files[-1]), "r") as file:
                df = pd.read_csv(file)

    df = df.groupby(['version', 'created_at', 'os']).sum().reset_index()

    # Filter versions with less than 10000 downloads
    df = df.groupby('version').filter(lambda x: x['downloads'].sum() > 10000)


    new_rows = []
    for version in df['version'].unique():
        df_version = df[df['version'] == version]
        for operation_system in ['mac', 'windows', 'linux']:
            if df_version[df_version['os'] == operation_system].empty:
                new_rows.append([version, operation_system, 0, 0])
    df = df.append(new_rows, ignore_index=True)

    # Sort by version and os
    df = df.sort_values(by=['version', 'os'])

    if configuration['save_data']:
        df.to_csv(os.path.join("processed-data", f"releases_versions.csv"), index=False)


    if configuration["chronological"]:
        plt.figure(figsize=(20, 6))
        if configuration["logarithm"]:
            plt.yscale('log')

        linux_downloads = df[df['os'] == 'linux']['downloads'].values
        windows_downloads = df[df['os'] == 'windows']['downloads'].values
        mac_downloads = df[df['os'] == 'mac']['downloads'].values
        graph_bar_chart(df, linux_downloads, windows_downloads, mac_downloads)

    if configuration["normalize"] or configuration["sorted"]:
        total_downloads = df.groupby('version').sum()['downloads'].values
        if configuration["normalize"]:
            plt.figure(figsize=(20, 6))

            linux_downloads = 100 * df[df['os'] == 'linux']['downloads'].values / total_downloads
            windows_downloads = 100 * df[df['os'] == 'windows']['downloads'].values / total_downloads
            mac_downloads = 100 * df[df['os'] == 'mac']['downloads'].values / total_downloads
            plt.ylim(0, 100)
            plt.gca().yaxis.set_major_formatter(plt.FuncFormatter('{}%'.format))
            graph_bar_chart(df, linux_downloads, windows_downloads, mac_downloads)

        if configuration["sorted"]:
            plt.figure(figsize=(20, 6))
            if configuration["logarithm"]:
                plt.yscale('log')

            # Group by versions and sort by total downloads
            versions = df.groupby('version').sum().sort_values(by='downloads', ascending=False)
            df['total_downloads'] = df['version'].map(versions['downloads'])
            df = df.sort_values(by=['total_downloads', 'os'], ascending=False)

            # Sort original df by the sorted versions


            linux_downloads = df[df['os'] == 'linux']['downloads'].values
            windows_downloads = df[df['os'] == 'windows']['downloads'].values
            mac_downloads = df[df['os'] == 'mac']['downloads'].values
            graph_bar_chart(df, linux_downloads, windows_downloads, mac_downloads)

if __name__ == '__main__':
    graph_releases({
        'chronological': False,
        'normalize': False,
        'sorted': True
    })
