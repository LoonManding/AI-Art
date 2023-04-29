: ${@?no positional parameters}
# https://stackoverflow.com/questions/5228345/how-can-i-reference-a-file-for-variables-using-bash
source .env

song=$1
scene=$2

reorg_files.py $song
./rev_videos.sh $song $scene
python seed_multiverse.py $song $scene
./concat_seed_uni.sh $song $scene