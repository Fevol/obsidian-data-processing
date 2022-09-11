import pandas as pd
import re
import os
import datetime

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from util import download_from_url, save_dataframe, generate_color_palette, draw_bar_graph

# Set the colour palette for the graph here, a minimum 2 colours is recommended
diverging_palette =   ['#2c3071', "#225182", "#1f708a", "#42928e", '#5ea990', '#a1cb90']
qualitative_palette = ['#0fb5ae', '#4046ca', '#f68511', '#de3d82', '#7e84fa', '#72e06a',
                       '#147af3', '#7326d3', '#e8c600', '#cb5d00', '#008f5d', '#bce931']

def graph_themes(configuration):
    if configuration['download'] or configuration['provided_file']:
        if configuration['download']:
            data = download_from_url(
                "https://releases.obsidian.md/stats/theme/",
                "raw-data/themes.json" if configuration['save_data'] else "").decode("utf-8")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        else:
            with open(configuration['provided_file'], 'r') as f:
                data = f.read()

                # Find if filename contains timestamp
                if re.search(r'\d{4}.?\d{2}.?\d{2}', configuration['provided_file']):
                    timestamp = re.search(r'\d{4}.?\d{2}.?\d{2}', configuration['provided_file']).group(0) + 'T00-00-00'
                else:
                    timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(configuration['provided_file'])).strftime("%Y-%m-%dT%H-%M-%S")

        # Parse json file with pandas
        df = pd.read_json(data)
        df = df.transpose().drop('id', axis=1).reset_index()
        df.columns = ['name', 'downloads']
        df = df.sort_values(by='name', ascending=True)

        # To csv with timestamp of current date
        if configuration['save_data']:
            save_dataframe(df, "processed-data/themes.csv", timestamp)
    else:
        # Get last fetched themes.json file in the raw folder
        theme_files = [f for f in os.listdir("processed-data") if re.match(r"themes_\d{4}.*\.csv", f)]
        theme_files.sort()

        if not theme_files:
            print("No themes.json file found in processed data folder")
            return
        else:
            with open(os.path.join("processed-data", theme_files[-1]), "r") as file:
                df = pd.read_csv(file)

    if configuration["chronological"] or configuration["sorted"]:
        palette = generate_color_palette(diverging_palette, len(df))

        df['age'] = df.index
        df['color'] = palette

        if configuration["chronological"]:
            draw_bar_graph(df, palette, legend=False, logarithm=configuration["logarithm"])
        if configuration["sorted"]:
            draw_bar_graph(df.sort_values(by='downloads', ascending=False).reset_index(), palette, logarithm=configuration["logarithm"])
    if configuration["difference"]:
        # Get last fetched themes.json file in the raw folder
        theme_files = [f for f in os.listdir("processed-data") if re.match(r"themes_\d{4}.*\.csv", f)]
        theme_files.sort()

        current_day = theme_files[-1].split("_")[1].split("T")[0]
        theme_files = theme_files[:-1]

        # Select only one file for each day, the latest one
        grouped_by_day = {}
        for file in theme_files:
            date = file.split("_")[1].split("T")[0]
            if date not in grouped_by_day:
                grouped_by_day[date] = [file]
            else:
                grouped_by_day[date].append(file)
        theme_files = [grouped_by_day[k][-1] for k in grouped_by_day.keys()]

        days = list(grouped_by_day.keys())
        for idx, file in enumerate(theme_files):
            diff_df = pd.read_csv(os.path.join("processed-data", file))

            # Get difference of diff_df and df on same name
            df = df.merge(diff_df, on='name', how='outer', suffixes=('', f'_{days[idx]}'))
            # df[days[idx]] = df['downloads' if idx == 0 else days[idx - 1]] - diff_df['downloads']



        intervals = []
        for idx, day in enumerate(days[:-1]):
            interval = f"[{day}, {days[idx + 1]}]"
            df[interval] = df[f'downloads_{days[idx + 1]}'] - df[f'downloads_{day}']
            intervals.append(interval)

        interval = f"[{days[-1]}, {current_day}]"
        df[interval] = df['downloads'] - df[f'downloads_{days[-1]}']
        intervals.append(interval)

        if configuration['save_data']:
            df.to_csv("processed-data/themes_diff.csv", index=False)

        plt.figure(figsize=(20, 6))

        if configuration["logarithm"]:
            plt.yscale('log')

        plt.xlim(-0.5, len(df) - .5)
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)

        # Draw graph for every interval
        for idx, interval in enumerate(intervals):
            plt.bar(df.index, df[interval].values, 1, color=qualitative_palette[idx % len(qualitative_palette)], label=interval, bottom=sum(df[intervals[:idx-1]]) if idx else None)

        # Set x-axis labels with rotation
        plt.xticks(df.index[::20], df.index.values[::20], rotation=45)

        patches = [mpatches.Patch(color=qualitative_palette[i], label=intervals[i]) for i in range(len(intervals))]
        plt.legend(handles=patches, loc='upper left')

        plt.show()


if __name__ == '__main__':
    graph_themes()