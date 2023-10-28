
# Add missing imports 

import os
import re
import pandas as pd
import networkx as nx



def read_scene_dict(gdrive_basedir, song):
    scene_dict = pd.read_csv(os.path.join(gdrive_basedir, song, 'prompt_data', 'scene_dict.csv'), index_col=0).to_dict()['0']

    # Convert the values from strings to lists
    scene_dict = {k: v.split(',') for k,v in scene_dict.items()}

    # Remove single quotes and list brackets from each element in the list
    scene_dict = {k: [re.sub(r"['\[\]]", '', fn).strip() for fn in v] for k,v in scene_dict.items()}

    # Truncate the digits after each hyphen to 4 digits
    scene_dict = {scene: [re.sub(r'-(\d+)$', lambda m: '-' + m.group(1)[:4], fn) for fn in scene_dict[scene]] for scene in scene_dict}

    # Invert scene_dict to make a mapping from file to folder name
    file_to_scene_dict = {}
    for scene in scene_dict:
        for fn in scene_dict[scene]:
            file_to_scene_dict[fn] = scene

    return scene_dict, file_to_scene_dict


def downselect_to_scene_sequence(G, scene_sequence):
    # Remove all edges from the graph that do not connect nodes in the scene_sequence
    # Make a list of all edges in the graph
    all_edges = list(G.edges)

    # Only keep edges that connect nodes with pairs of scenes that are adjacent in the scene_sequence
    adjacent_edges = []
    for i in range(len(scene_sequence)-1):
        scene1 = scene_sequence[i]
        scene2 = scene_sequence[i+1]

        # Keep edges that connect nodes in these two scenes in either direction
        adjacent_edges.extend([(u,v) for u,v in all_edges if G.nodes[u]['scene'] == scene1 and G.nodes[v]['scene'] == scene2])
        adjacent_edges.extend([(u,v) for u,v in all_edges if G.nodes[u]['scene'] == scene2 and G.nodes[v]['scene'] == scene1])

    # Also include edges that connect nodes in the same scene
    adjacent_edges.extend([edge for edge in all_edges if G.nodes[edge[0]]['scene'] == G.nodes[edge[1]]['scene']])

    # Downselect the graph to only include these edges and their nodes
    G_sequence = G.edge_subgraph(adjacent_edges)
    
    return G_sequence


def gen_path_edges_short(G_sel, scene_sequence):
    first_scene = scene_sequence[0]
    last_scene = scene_sequence[-1]

    def most_connected_node(G_sel, scene):
        scene_nodes = [n for n in G_sel.nodes() if G_sel.nodes[n]['scene'] == scene]
        scene_G_sel = G_sel.subgraph(scene_nodes)

        # get the node with the highest degree
        node = max(scene_G_sel.degree, key=lambda x: x[1])[0]

        return node

    first_node = most_connected_node(G_sel, first_scene)
    last_node = most_connected_node(G_sel, last_scene)

    path = nx.shortest_path(G_sel, first_node, last_node)

    path_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]

    return path_edges

def construct_input_image_folder_paths(df_transitions, song_basedir, forward_c_pairs):
    df_transitions['reversed'] = [tuple(c_pair) not in forward_c_pairs for c_pair in df_transitions[['c1', 'c2']].values]
    df_transitions['input_image_folder'] = df_transitions.apply(
        lambda x: f"{x['c1']} to {x['c2']}" if not x['reversed'] else f"{x['c2']} to {x['c1']}",
        axis=1
    )
    # df_transitions['input_image_folder'] = os.path.join(song_basedir, 'transition_images', df_transitions['input_image_folder'])

    input_image_folders = [os.path.join(song_basedir, 'transition_images', folder) for folder in df_transitions['input_image_folder'].tolist()]
    df_transitions['input_image_folder'] = input_image_folders
    return df_transitions


def check_input_image_folders_exist(df_transitions):
    missing_folders = df_transitions[~df_transitions['input_image_folder'].apply(os.path.exists)]
    if not missing_folders.empty:
        print("Files not existing:  {}".format(missing_folders))
        print(missing_folders['input_image_folder'].values)
        raise ValueError()


def generate_text_for_ffmpeg(df_transitions, fps):
    out_txt = ''
    image_duration = 1/fps
    for _, row in df_transitions.iterrows():
        folder = row['input_image_folder']
        images = sorted([fn for fn in os.listdir(folder) if fn.endswith('.png')])
        if row['reversed']:
            images = images[::-1]
        images = images[:-1]
        image_fps = [os.path.join(folder, fn) for fn in images]
        image_fps = [fp.replace('\\', '/') for fp in image_fps]
        image_fps = [fp.replace(' ', '\ ') for fp in image_fps]
        for fp in image_fps:
            out_txt += f"file {fp}\nduration {image_duration}\n"

    return out_txt



def generate_output_video(fps, out_dir, output_filename):
    os.chdir(out_dir)
    os.system(f"ffmpeg -f concat -safe 0 -i videos.txt -c mjpeg -q:v 3 -r {fps} {output_filename}")
