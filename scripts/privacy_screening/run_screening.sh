#!/bin/bash
# Person screening for the SmartWilds HF release (MegaDetector v5a).
# Array tasks 0-3: image shards. Tasks 4-5: video halves.
#SBATCH --job-name=sw-person-screen
#SBATCH --account=<your-account>
#SBATCH --partition=gpu
#SBATCH --gpus-per-node=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --array=0-5
#SBATCH --output=logs/%A_%a.out

# Run from the screening directory: it must hold md_v5a.0.0.pt, the
# images_shard*.txt / videos.txt lists from make_lists.py, and a .venv with
# the packages listed in requirements.txt (megadetector, av, imageio-ffmpeg).
set -euo pipefail
D=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PY=$D/.venv/bin/python
cd $D
mkdir -p results
nvidia-smi -L || true

T=${SLURM_ARRAY_TASK_ID}
if [ "$T" -le 3 ]; then
  $PY -m megadetector.detection.run_detector_batch \
      $D/md_v5a.0.0.pt $D/images_shard${T}.txt $D/results/images_shard${T}.json \
      --threshold 0.1 --include_image_size --use_image_queue --loader_workers 6 \
      --checkpoint_frequency 5000 --checkpoint_path $D/results/images_shard${T}.ckpt.json \
      --allow_checkpoint_overwrite
else
  V=$((T - 4))
  $PY $D/screen_videos.py $D/videos.txt $D/results/videos_task${V}.jsonl --task $V --ntasks 2
fi
