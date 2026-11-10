# Summary of Files by Location and Modality


## Bioacoustics
TW05-SM01: 144 files

TW06-SM03: 77 files

TW07-SM02: 12 files

TW08-SM04: 78 files

* missing metadata?


## Camera traps
TW01-CT02: 10,431 files (1 folder + 10,429 images)
- last datetime: NSCF0002_250702065002_0439 (2025-07-02 06:50:02)

TW02-CT03: 63 files (1 folder + 62 images)
- video files AVI, check settings on this
- last datetime: 2025-07-01 00:34:45

TW03-CT01: 8,952 files (10 folders with a total of 8,952 images)
- last datetime: NSCF0001_250702010401_0984 (2025-07-02 01:04:01)

TW04-CT04: 895 files (1 folder + 894 images)
- last datetime: 2025-07-03 18:11:17


* All except the CT04 ran out of battery, need to adjust the settings to avoid this in the future.

## Drones
20250701_parrotanafi_1: 3 metadata, 4 video files

20250703_parrotanafi_1: 3 video files

20250703_parrotanafi_2: 3 video files

20250703_parrotanafi_4: 3 video files

20250703_parrotanafi_5: 2 metadata, 5 video files

* missing metadata for 1, 2, 4 from 7/3


## Next steps:
Make sure all metadata files are there.
Upload to HF to share with collaborators and for backup. 
- make sure ABC has access to Imageomics HF 
- instructions to upload: https://hackmd.io/qimNd-RLTxS5B4ZDYL4Xiw

### HF instructions:
#### Allocate a node to process the files, otherwise it can make a really long time
```bash
salloc --nodes=1 --ntasks-per-node=1 --cpus-per-task=28 --gres=gpu:1 --time=03:00:00 --account=<account>
```
Check your allocated node:
```bash
squeue -u $USER
```
Then SSH into the node:
```bash
ssh <node_name>
```
make sure you are logged in to HF:
```bash
huggingface-cli whoami
```
If you are not logged in, run:
```bash
huggingface-cli login
```
Navigate to the directory where the files are located, e.g.:
```bash
cd <archive>/thewilds_20250630/camera_traps
```

#### You need to manually create the subdirectories in the HF repo before uploading the files.
You can do this by uploading the metadata file.

#### Run command to upload directory to HF
base command:
```bash
huggingface-cli upload <username>/<repo_name> <path_to_directory_in_OSC> <path_to_directory_in_HF> --repo-type=dataset
```
example:
```bash
huggingface-cli upload imageomics/thewilds_cameratraps thewilds_20250630/camera_traps/TW02-CT03/SD03_20250630_20250703 TW02-CT03/SD03_20250630_20250703 --repo-type=dataset
```
3. check the upload status on HF website, it can take a while depending on the size of the files and your internet connection.

TW01-CT02/SD02_20250630_20250703/images

huggingface-cli upload imageomics/thewilds_cameratraps TW01-CT02/SD02_20250630_20250703/images/chunk4 TW01-CT02/SD02_20250630_20250703/images --repo-type=dataset

huggingface-cli upload imageomics/thewilds_cameratraps TW03-CT01/SD01_20250630_20250703 TW03-CT01/SD01_20250630_20250703 --repo-type=dataset



## Process data
### document all processing in NatureLabs repo (python scripts, jupyter notebooks, etc)
1. Process acoustic data to ID birds and other species. Ask Kitzes lab how to tie this to biodiversity metrics. One place to start is just number of different species in each location.
2. Process camera trap data to ID photos and videos containing animals. Use Megadetector for initial filtering, then manually review. BioClip can help ID species.
3. Process drone data to track animals in the videos. Use OWL to track animals in the videos, then manually review. BioClip can help ID species.

## Plans for next deployments
- suggestion: put camera traps in more open areas
