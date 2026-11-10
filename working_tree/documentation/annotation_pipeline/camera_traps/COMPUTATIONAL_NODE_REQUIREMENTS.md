# Computational Node Requirements for Camera Trap Detection Pipeline

This document specifies computational requirements and strategies for processing camera trap detections (YOLO + SAHI + BioCLIP) on HPC clusters.

## Executive Summary

**Total data**: 243,000 images across 13 camera deployments
**Total processing time**: 45-60 minutes (GPU), 4-8 hours (CPU-only)
**Recommended approach**: Single GPU node with temporal multiplexing across cameras

## 1. Hardware Requirements

### GPU-Accelerated (Recommended)

**Minimum Specifications**:
- **GPU**: 1x NVIDIA A100 (40 GB) or RTX A6000 (48 GB)
  - YOLO inference: ~200 images/minute per GPU
  - BioCLIP classification: ~500 images/minute per GPU
  - Depth estimation: ~100 images/minute per GPU

- **CPU**: 16+ cores (for preprocessing and I/O)
- **RAM**: 64 GB
- **Storage**: 500 GB SSD (scratch for intermediate files)

**Estimated cost**: ~$8-12/hour on AWS/Azure, HPC center rates vary

### CPU-Only (Slower)

**Specifications**:
- **CPU**: 32+ cores (Intel Xeon or AMD EPYC)
- **RAM**: 128 GB
- **Storage**: 500 GB SSD

**Performance**: 10-20x slower than GPU

### Multi-GPU (High Throughput)

**For parallel processing of multiple cameras**:
- **GPU**: 4x A100/A6000
- **CPU**: 64+ cores
- **RAM**: 256 GB
- **Storage**: 1 TB SSD

**Performance**: Process all 13 cameras in parallel (~12 minutes total)

## 2. Deployment Strategy Options

### Option A: Single GPU Node (Sequential)

Process cameras one-at-a-time on a single GPU.

**Pros**:
- Simple, reliable
- Minimal resource conflicts
- Easy debugging

**Cons**:
- Slower (45-60 minutes)
- Underutilizes resources

**HPC Submission Example** (Slurm):
```bash
#!/bin/bash
#SBATCH --job-name=camera_detections
#SBATCH --gres=gpu:1         # 1 GPU
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=2:00:00       # 2 hours
#SBATCH --output=camera_detections_%j.log

# Process each camera sequentially
for campaign in "20250630_20250703" "20250804_20250828"; do
    for camera in TW01-CT02 TW02-CT01 TW04-CT03 TW06-CT04 TW06-CT05 TW07-CT05 TW09_CT02 TW09-CT05 TW11-CT06; do
        echo "Processing $camera in $campaign"
        python camera_trap_detections.py \
            --weights yolov8x.pt \
            --images "/fs/ess/PAS2136/TheWilds2025/thewilds_${campaign}/camera_traps/$camera" \
            --csv-out "/fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing/${campaign}/${camera}/detections.csv" \
            --depth-estimation \
            --gpu 0
    done
done

echo "Detections complete. Ready for metadata generation."
```

### Option B: Multi-GPU Node with Temporal Multiplexing

Use GPU batching: Process multiple image batches in parallel.

**Pros**:
- Faster (15-20 minutes)
- Efficient GPU utilization
- Single node, simple submission

**Cons**:
- Requires GPU-aware batching in code
- Higher memory demand

**HPC Submission Example**:
```bash
#!/bin/bash
#SBATCH --job-name=camera_detections_parallel
#SBATCH --gres=gpu:4         # 4 GPUs
#SBATCH --cpus-per-task=32
#SBATCH --mem=256G
#SBATCH --time=1:00:00
#SBATCH --output=camera_detections_%j.log

# Process with 4 GPUs in parallel
python camera_trap_detections_batch.py \
    --batch-size 4 \
    --num-gpus 4 \
    --base-dir /fs/ess/PAS2136/TheWilds2025 \
    --output-root /fs/ess/PAS2136/TheWilds2025/processing_output
```

### Option C: Job Array (Multiple Nodes)

Submit separate jobs for each camera, process in parallel.

**Pros**:
- Maximum parallelism
- Can use multiple nodes
- Scales well

**Cons**:
- Requires resource coordination
- More complex submission logic

**HPC Submission Example**:
```bash
#!/bin/bash
#SBATCH --job-name=camera_detections_array
#SBATCH --array=1-13              # 13 cameras
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=1:00:00
#SBATCH --output=camera_detections_%a_%j.log

# Define camera list
cameras=("TW01-CT02_20250630_20250703" "TW02-CT03_20250630_20250703" ... "TW11-CT06_20250804_20250828")

# Get current camera from array task ID
camera_key=${cameras[$((SLURM_ARRAY_TASK_ID - 1))]}
IFS='_' read -r camera_id campaign <<< "$camera_key"

python camera_trap_detections.py \
    --weights yolov8x.pt \
    --images "/fs/ess/PAS2136/TheWilds2025/thewilds_${campaign}/camera_traps/$camera_id" \
    --csv-out "/fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing/${campaign}/${camera_id}/detections.csv" \
    --depth-estimation
```

## 3. Detailed Performance Estimates

### YOLO Detection (YOLOv8X model)

| Hardware | Throughput | Time for 243k images |
|----------|-----------|-------------------|
| A100 (40GB) GPU | 200 img/min | ~20 minutes |
| RTX A6000 GPU | 180 img/min | ~23 minutes |
| CPU (32 cores) | 15 img/min | ~4 hours |
| CPU (64 cores) | 25 img/min | ~2.5 hours |

### BioCLIP Classification

| Hardware | Throughput | Time for 243k images |
|----------|-----------|-------------------|
| A100 GPU | 500 img/min | ~8 minutes |
| RTX A6000 | 450 img/min | ~9 minutes |
| V100 GPU | 300 img/min | ~14 minutes |
| CPU (32 cores) | 40 img/min | ~100 minutes |

### Combined Pipeline (Sequential)

| Component | GPU | CPU-only |
|-----------|-----|---------|
| YOLO | 20 min | 4 hours |
| BioCLIP | 8 min | 100 min |
| Depth estimation | 15 min | 2 hours |
| I/O + overhead | 5 min | 30 min |
| **Total** | **48 min** | **6.5 hours** |

## 4. Storage Requirements During Processing

### Temporary Storage

```
Processing bottleneck: Annotated images saved during detection

Input images:        ~200 GB (243k JPGs)
Annotated images:    ~500 GB (3 channels per original)
Detections CSVs:     ~1 GB (one per camera)
Intermediate files:  ~50 GB (caches, EXIF data)

Total peak: ~750 GB
```

**Solution**: Use local SSD scratch space on compute node (usually available)

```bash
# In submission script
export TMPDIR=/local_scratch/$SLURM_JOB_ID
```

### Long-term Storage

After processing, keep only Darwin Core metadata (~50 MB), archive rest:

```bash
# Delete temporary files after metadata generation
rm -rf /fs/ess/PAS2136/TheWilds2025/processing_output/intermediate_processing
rm -rf /fs/ess/PAS2136/TheWilds2025/processing_output/annotated_images
```

## 5. Software Environment Setup

### Required Packages

```bash
# In your HPC job submission script or container

# Create conda environment
conda create -n camera_traps python=3.10

# Install dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install yolov8
pip install ultralytics sahi
pip install open_clip_torch open_clip
pip install pandas numpy opencv-python scipy
pip install Pillow exifread

# Verify GPU access
python -c "import torch; print(torch.cuda.is_available())"
```

### Using Containers (Recommended)

```bash
# Singularity/Apptainer (common on HPC)
singularity pull imageomics_camera_traps.sif docker://imageomics/camera_traps:latest

singularity exec --nv imageomics_camera_traps.sif python camera_trap_detections.py ...

# Docker (if available on your HPC cluster)
docker run --gpus all -v /fs/ess/PAS2136:/project \
    imageomics/camera_traps:latest \
    python camera_trap_detections.py ...
```

## 6. Node Allocation Request Template

### For HPC Center (e.g., Ohio Supercomputer Center)

**Request Type**: GPU Compute Allocation

**Project**: TheWilds 2025 Camera Trap Survey Data Annotation

**Specifications**:

```
Resource Type:           GPU Compute Node
GPU Type:               NVIDIA A100 (40 GB) or comparable
Number of GPUs:         1 (minimum), 4 (recommended)
CPU Cores Required:     16-32 cores
Memory Required:        64 GB (minimum), 256 GB (preferred)
Storage Required:       500 GB temporary (SSD), 50 GB permanent
Estimated Total Time:   1-2 GPU-hours
Duration:              Single job/run (not sustained allocation)
```

**Justification**:
- Process 243,000 camera trap images with deep learning models
- Estimate detection boxes and species classification
- Generate Darwin Core biodiversity metadata for publication
- Cannot be parallelized cost-effectively across CPU-only nodes

### For Cloud (AWS/Azure)

**Recommended Instance Types**:

**AWS**:
- `g4dn.2xlarge` (1x T4, 8 vCPU, 32 GB RAM) - $0.75/hour
- `g4dn.12xlarge` (4x T4, 48 vCPU, 192 GB RAM) - $3.06/hour
- `p3.2xlarge` (1x V100, 8 vCPU, 61 GB RAM) - $3.06/hour
- `p3.8xlarge` (4x V100, 32 vCPU, 244 GB RAM) - $12.24/hour

**Estimated cost**: $0.75-3 for single job

**Azure**:
- `Standard_NC6s_v2` (1x Tesla P100, 6 vCPU, 112 GB) - ~$3/hour
- `Standard_NC24s_v3` (4x Tesla V100, 24 vCPU, 448 GB) - ~$12/hour

## 7. Failure Recovery

### Checkpoint Strategy

Resume processing after interruption:

```bash
# In camera_trap_detections.py, implement checkpoint saving:

checkpoint_file = f"{output_dir}/.checkpoint_{camera_id}.json"

if os.path.exists(checkpoint_file):
    with open(checkpoint_file) as f:
        checkpoint = json.load(f)
    processed_count = checkpoint['processed_count']
    print(f"Resuming from image {processed_count}")
else:
    processed_count = 0

# Process images starting from checkpoint
for i, image_path in enumerate(sorted(image_paths)[processed_count:], start=processed_count):
    # ... process image ...

    # Save checkpoint every 100 images
    if i % 100 == 0:
        with open(checkpoint_file, 'w') as f:
            json.dump({'processed_count': i, 'timestamp': datetime.now().isoformat()}, f)
```

## 8. Monitoring and Logging

### During Execution

```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Monitor disk space
watch -n 5 'df -h | grep -E "Filesystem|/fs/ess"'

# Monitor job status (Slurm)
squeue -u $USER
sacct -j <job_id> --format=JobID,JobName,Elapsed,State,ExitCode
```

### Logging Best Practices

```bash
# Capture all output
python camera_trap_detections.py ... 2>&1 | tee processing_$campaign_$camera.log

# Key metrics to log
echo "Start time: $(date)" >> detections.log
echo "Total images: $(ls $image_dir | wc -l)" >> detections.log
echo "GPU utilization (avg):" >> detections.log
nvidia-smi dmon -c 1 >> detections.log
echo "End time: $(date)" >> detections.log
```

## 9. Cost Optimization

### For Local HPC Centers

- **Off-peak scheduling**: Run jobs during off-hours (typically cheaper)
- **Node sharing**: Request fewer GPUs during off-peak
- **Batch consolidation**: Process multiple cameras in single job to reduce scheduling overhead

### For Cloud

- **Spot instances**: 70% discount, but can be interrupted
  - Use with checkpointing for fault tolerance
- **Reserved instances**: 40% discount for pre-committed usage
- **Scheduled scaling**: Run during cheap hours (nights, weekends)

**Estimated costs**:
- Single GPU node: $0.75-3/hour × 1 hour = **$0.75-3 total**
- Multi-GPU node: $3-12/hour × 0.25 hour = **$0.75-3 total**

Very cost-effective for 243k image processing!

## 10. Recommended Approach for TheWilds2025

Given typical HPC cluster constraints:

**Option**: Single GPU node, sequential camera processing

**Why**:
- Simple to manage
- Reliable (minimal dependencies)
- Reasonable time (45-60 minutes)
- Straightforward debugging
- Can resubmit if issues arise

**Submission**:
```bash
sbatch camera_detections_single_gpu.sh
```

**Expected outcome**: All 13 cameras processed, 243k detection boxes + classifications in 1 hour wall time

## Files Ready for Submission

- `camera_trap_detections.py` - Main detection script (needs GPU batching support)
- `detection_config.json` - Camera-specific parameters for all 13 deployments
- `setup_output_directories.sh` - Directory structure initialization
- Detection model checkpoint: `yolov8x.pt` (needs to be downloaded)

## Next Steps

1. **Confirm HPC access**: Which cluster will host the computation?
   - Ohio Supercomputer Center (OSC)
   - Campus cluster with GPU nodes
   - Cloud provider (AWS/Azure/GCP)

2. **Prepare environment**: Container image or conda environment

3. **Submit batch job**: Using appropriate scheduler (Slurm/PBS/SGE)

4. **Monitor execution**: Watch logs for errors or performance issues

5. **Process results**: Generate Darwin Core metadata using outputs

---

For specific HPC cluster documentation, see:
- Ohio Supercomputer Center: https://www.osc.edu/
- General Slurm docs: https://slurm.schedmd.com/
- AWS GPU instances: https://aws.amazon.com/ec2/instance-types/#accelerated_computing
