

#%%
import os
import pandas as pd
#%%



import argparse
parser = argparse.ArgumentParser()
parser.add_argument("song")
parser.add_argument("scene")
args = parser.parse_args()

song = args.song
scene = args.scene
# scene = 's5'

from dotenv import load_dotenv, dotenv_values
load_dotenv()  # take environment variables from .env.
gdrive_basedir = os.getenv('base_dir')


scene_basedir = os.path.join(gdrive_basedir,"{}\scene_image_input".format(song))

# for scene in os.listdir(scene_basedir):

scene_dir = os.path.join(scene_basedir, scene)
if os.path.isdir(scene_dir):

    fns = [f for f in os.listdir(scene_dir) if f.endswith('.png')]
    prompts = [f.split('_')[0] for f in fns]
    seeds = [f.split('_')[1].strip('.png') for f in fns]



# %%

df = pd.DataFrame(
    index = range(len(fns))
)

df['fn'] = fns
df['prompt'] = prompts
df['seed'] = seeds

df

#%%

# Generate a sequence of the form
# sequence = [
#     (0,1),
#     (0,2),
#     (0,3),
#     (0,4),
#     (1,2),
#     (1,3),
#     (1,4),
#     (2,3),
#     (2,4),
#     (3,4),
# ]

num_prompts = len(df)

sequence = []
for i in range(num_prompts):
    for j in range(i+1,num_prompts):
        sequence.append((i,j))

sequence

#%%

df_out = pd.DataFrame(
index = range(len(sequence)),
columns = ['from_name', 'from_seed','to_name', 'to_seed', 'compute','duration','scene']

)

for i, (start, stop) in enumerate(sequence):
    row_from = df.loc[start]
    row_to = df.loc[stop]


    df_out.loc[i]['from_name']  = row_from['prompt']
    df_out.loc[i]['from_seed']  = row_from['seed']
    df_out.loc[i]['to_name']  = row_to['prompt']
    df_out.loc[i]['to_seed']  = row_to['seed']



df_out['compute'] = 'y'
df_out['duration'] = 5
df_out['scene'] = scene

df_out

df_out['from_seed'] = df_out['from_seed'].astype(str)
df_out['to_seed'] = df_out['to_seed'].astype(str)


fp_out = os.path.join(scene_dir, 'transitions.csv')
print("writing transitions csv to {}".format(fp_out))
df_out.to_csv(fp_out)

