#%%
import os
import re
import numpy as np
import pandas as pd
# %%

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("song")
parser.add_argument("scene")
parser.add_argument("num_output_rows")
args = parser.parse_args()

song = args.song
scene = args.scene
num_output_rows = int(args.num_output_rows)

# song = 'spacetrain'
# scene = 'tram_liftoff'
# num_output_rows = 10

from dotenv import load_dotenv, dotenv_values
load_dotenv()  # take environment variables from .env.
gdrive_basedir = os.getenv('base_dir')
# gdrive_basedir = r'G:\.shortcut-targets-by-id\1Dpm6bJCMAI1nDoB2f80urmBCJqeVQN8W\AI-Art Kyle'

input_basedir = os.path.join(gdrive_basedir, '{}\scenes'.format(song))

#TODO: Rename this 'folder'
folder = os.path.join(input_basedir, scene)

# folder = os.path.join(gdrive_basedir,r'elationstation\transitions' )

if not os.path.exists(folder):
    raise ValueError("did not find input scene folder")

folder_rev = os.path.join(folder, 'rev')

#%%

fn = 'input_data.xlsx'
fp = os.path.join(gdrive_basedir, fn)
df = pd.read_excel(fp, sheet_name='transitions_{}'.format(song), index_col=0)


df = df.where(df['scene'] == scene).dropna(how='all')
# df = df.dropna(subset=['start'])


# %%
import re

from utils import transition_fn_from_transition_row, clip_names_from_transition_row


# for fn in fns:
#     get_clips(fp)



c1s = []
c2s = []
for idx, row in df.iterrows():

    fn = transition_fn_from_transition_row(row)
    c1, c2 = clip_names_from_transition_row(row)

    df.loc[idx, 'c1'] = c1
    df.loc[idx, 'c2'] = c2
    df.loc[idx, 'fn'] = fn

    # break

# print(df)
df
#%%

set(df['c1']) == set(df['c2']) 
#%%

all_cs = list(set([*df['c1'], *df['c2']]))

all_cs

#%%%




seeds= list(set())

c_id = list(range(len(all_cs)))

seed_lookup = pd.Series(all_cs, index=c_id)
seed_lookup.name ='seed_str'
seed_lookup

#%%

# idx_lookup = seed_lookup.reset_index()
idx_lookup = seed_lookup.reset_index().set_index('seed_str')['index']
idx_lookup


# %%


num_videos = len(seed_lookup)

def find_next_idx(cur_idx):
    
    valid_idxs = [i for i in range(num_videos) if i != cur_idx]
    next_idx = np.random.randint(0,num_videos-1)
    next_idx = valid_idxs[next_idx]
    return next_idx

cur_idx = 0

transition_idxs = []

df_transitions = pd.DataFrame(columns = ['idx_1','idx_2'], index = list(range(num_output_rows)))

trans_names_forward = df['c1'] + df['c2']
trans_names_forward = trans_names_forward.values
trans_names_rev = df['c2'] + df['c1']
trans_names_rev = trans_names_rev.values

for i in df_transitions.index:  

    found_match = False

    for j in range(1000):
        next_idx = find_next_idx(cur_idx)

        cur_name = seed_lookup[cur_idx]
        next_name = seed_lookup[next_idx]

        checkstr = cur_name + next_name
        if checkstr in trans_names_forward or checkstr in trans_names_rev:
            found_match = True
            break


    print(found_match)
    df_transitions['idx_1'][i] = cur_idx
    df_transitions['idx_2'][i] = next_idx

    cur_idx=next_idx


df_transitions
    
#%%

vals = df[['c1', 'c2']].values

vals = [(f, t) for f, t in vals]

# print(vals)
reverse = []
from_seed = []
to_seed = []

for transition_index, row in df_transitions.iterrows():


    # pass
    idx_tup = (seed_lookup[row['idx_1']], seed_lookup[row['idx_2']])


    # idx_tup = (seed_lookup[i] for i in idx_tup)


    if idx_tup in vals:
        reverse.append(False)
        from_seed.append(idx_tup[0])
        to_seed.append(idx_tup[1])
    else:
        reverse.append(True)
        from_seed.append(idx_tup[1])
        to_seed.append(idx_tup[0])




#     # df_transitions.loc[transition_index][['idx_1', 'c2']] = idx_tup
df_transitions['reverse'] = reverse
df_transitions['from_seed'] = from_seed
df_transitions['to_seed'] = to_seed


df_transitions





# %%
df_transitions["fn"]=df_transitions['from_seed']+ ' to ' +df_transitions['to_seed']+'.mp4'


# output_folder = [folder_rev if reverse else folder for reverse in df_transitions['reverse']]
input_folder = ['transitions_rev' if reverse else 'transitions' for reverse in df_transitions['reverse']]


input_basedir = os.path.join(gdrive_basedir, song)


# output_folder = ['rev' if re]

df_transitions['output_folder'] = input_folder


df_transitions['fp_out'] = input_basedir + '\\' + df_transitions['output_folder'] + '\\' +  df_transitions['fn']



df_transitions['fp_out'].values

# df_transitions.to_csv('transitions.csv')


#%%

df_transitions['fp_out'].values

# %%

df_exist = df_transitions['fp_out'].apply(os.path.exists)
df_not_exist =df_transitions.where(df_exist == False).dropna(how='all')

#TODO: move file exist checks to original for loop, such that it can keep trying to make a valid superscene with partial transitions. 
if len(df_not_exist):
    print("Files not existing:  ")
    raise ValueError(df_not_exist[['output_folder', 'fn']])


# %%


df_transitions['fp_out']  = df_transitions['fp_out'].str.replace('\\','/', regex=False)
#%%
# df_transitions['fp_out'].groupby('index').apply("\nfile ".join)

# out_txt = 'file ' + "\nfile ".join("\"" + df_transitions['fp_out'].str.replace(' ', '\ ') + '\"')
out_txt = 'file ' + "\nfile ".join(df_transitions['fp_out'].str.replace(' ', '\ '))

# out_txt = out_txt.replace(' ', '\ ')

with open('videos.txt', 'w') as f:
    f.write(out_txt)

import shutil

shutil.move('videos.txt', os.path.join(folder, 'videos.txt'))
# %%
