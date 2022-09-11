from coloraide import Color
import requests
import datetime
import math
import json

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def generate_color_palette(palette, color_count):
    return [c.to_string(hex=True) for c in Color.interpolate(palette).steps(color_count)]


def download_from_url(url, file_name):
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Error while downloading file from url: {url}\nMessage: {response.text}")

    content = response.json()

    while 'next' in response.links.keys():
        response = requests.get(response.links['next']['url'])
        content.extend(response.json())

    if file_name:
        split_name = file_name.split(".")
        file_name = split_name[0] + "_" + datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + "." + ".".join(split_name[1:])
        with open(file_name, "wb") as file:
            file.write(json.dumps(content).encode())

    return content


def save_dataframe(df, file_name, timestamp=datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")):
    split_name = file_name.split(".")
    file_name = split_name[0] + "_" + timestamp + "." + ".".join(split_name[1:])
    df.to_csv(file_name, index=False)


def tick_time(df):
    df['new_downloads'] = df['downloads'].apply(lambda x: np.ceil(x * random.uniform(1, min(1.01, 6 / np.log(x)))))
    return df


def draw_bar_graph(df, palette, legend=True, logarithm=False):
    plt.figure(figsize=(20, 6), dpi=200)
    plt.bar(df.index, df['downloads'], align='center', width=1, color=df['color'])

    # Set ticks every 20th index
    plt.xticks(df.index[::20], df.index.values[::20], rotation=45)
    plt.xlim(-0.5, len(df) - .5)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)

    # Optional: logarithmic scale
    if logarithm:
        plt.yscale('log')

    if legend:
        patches = []
        range_interval = 100

        # Create legend item for every range_interval
        ranges = math.ceil(len(df) / range_interval)
        for i in range(ranges)[:-1]:
            patches.append(mpatches.Patch(color=palette[math.ceil(range_interval * i + range_interval / 2)],
                                          label=f"[{range_interval * i}-{(range_interval * (i + 1)) - 1}]"))
        patches.append(mpatches.Patch(color=palette[math.ceil(((range_interval * (ranges - 1)) + len(df)) / 2)],
                                      label=f"[{range_interval * (ranges - 1)}-{len(df)}]"))

        # Add legend to upper-left corner
        plt.legend(handles=patches, loc='upper left')

    plt.show()
