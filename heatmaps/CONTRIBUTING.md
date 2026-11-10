# Contributing to Wilds Multimodal Data Analysis

Thank you for contributing to the analysis of multi-modal animal density data from The Wilds!

## Branch Workflow

To keep the codebase organized, we use separate branches for each sensor modality. Please follow this workflow when contributing:

### For Camera Trap Analysis
```bash
git checkout -b camera-trap-heatmaps
cd camera_trap
# Make your changes to camera trap heat map generation
```

### For Bioacoustic Analysis
```bash
git checkout -b bioacoustic-heatmaps
cd bioacoustic
# Make your changes to bioacoustic heat map generation
```

### For Drone Imagery Analysis
```bash
git checkout -b drone-heatmaps
cd drone
# Make your changes to drone heat map generation
```

### For Citizen Science Analysis
```bash
git checkout -b citizen-science-heatmaps
cd citizen_science
# Make your changes to citizen science heat map generation
```

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Imageomics/wilds_multimodal_data.git
   cd wilds_multimodal_data
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create your modality-specific branch (see above)

4. Make your changes

5. Test your code

6. Submit a pull request

## Code Structure

Each modality directory contains:
- `README.md` - Documentation specific to that modality
- `heatmap_generator.py` - Core heat map generation code

## Guidelines

- Keep modality-specific code in the appropriate directory
- Document your functions with clear docstrings
- Test your heat map generation code with sample data
- Update the modality-specific README if you add new functionality

## Questions?

If you have questions about the branch workflow or contribution process, please open an issue.
