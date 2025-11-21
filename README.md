# 🐚 SAM-HQ Eelgrass — High-Resolution Eelgrass Segmentation

This repository contains a customized training and evaluation pipeline for **SAM-HQ (Segment Anything Model – High Quality)** applied to **high-resolution drone imagery** of West Coast eelgrass meadows (AK / BC / WA / OR).  
The project supports **RGB**, **index channels**, **GLCM texture**, and multi-channel training.

---

## 📂 Repository Structure

```text
sam-hq-eelgrass/
│
├── train/                          # Training scripts, configs, logs
│   ├── dataset/                    # Custom eelgrass dataset loader
│   ├── transforms/                 # Data augmentation
│   ├── work_dirs/                  # All logs (per site, per model)
│   └── train_rgb.py                # Example RGB training script
│
├── eval/                           # Evaluation tools
│   ├── eval_single.py              
│   └── metrics/                    # IoU, Dice, boundary IoU, etc.
│
├── utils/                          # Helper modules
│   ├── tiling/                     
│   └── image_utils.py
│
├── pretrained_checkpoint/          # (Ignored) Put SAM-HQ weights here
│   └── sam_hq_vit_l.pth  (NOT included)
│
├── requirements.txt
└── README.md
```

---

## 📦 Installation

Tested on:

- Python 3.8–3.10  
- PyTorch 2.1+  
- CUDA 11.8 / 12.x  

Install:

```bash
conda create -n samhq python=3.10 -y
conda activate samhq
pip install -r requirements.txt
```

Install SAM-HQ:

```bash
pip install git+https://github.com/SysCV/sam-hq.git
```

---

## 📥 Pretrained Weights

SAM-HQ-L (~1.2GB) is **not included** in this repo.

Place it here after downloading:

```
pretrained_checkpoint/sam_hq_vit_l.pth
```

Add your download link here:

🔗 `<your-weight-link>`

---

## 📁 Dataset Structure

```text
data/
├── BC/
│   ├── train/
│   │   ├── image/
│   │   └── index/
│   ├── valid/
│   └── test/
├── WA/
├── OR/
└── AK/
```

Tile naming format:

```
<site>_<region>_<year>_rowXX_colYY.png
```

Example:

```
BH_WA_19_row10_col50.png
```

---

## 🚀 Training

Basic RGB training:

```bash
python train/train.py \
    --data-root /path/to/data \
    --output ./train/work_dirs/rgb_run1 \
    --checkpoint ./pretrained_checkpoint/sam_hq_vit_l.pth \
    --epochs 30
```

Multi-channel example:

```bash
python train/train_multichannel.py \
    --modalities rgb index \
    --data-root /path/to/data
```

Logs saved in:

```
train/work_dirs/
```

---

## 🧪 Evaluation

```bash
python eval/eval_single.py \
    --data-root /path/to/data \
    --checkpoint ./train/work_dirs/rgb_run1/best_model.pth \
    --output ./eval/results
```

Metrics include:

- IoU  
- Dice  
- Precision / Recall  
- Boundary IoU  
- Hausdorff Distance  

---

## 📊 Tiling Pipeline (512×512, 30% Overlap)

Tiling script:

```
utils/tiling/tile_pair.py
```

Outputs:

```
image/<basename>/...
index/<basename>/...
manifest/<basename>.csv
```

---

## 📝 TODO

- [ ] Add multi-GPU (DDP) training  
- [ ] Upload pre-trained eelgrass models  
- [ ] Add visualization notebook  
- [ ] Add dataset splitter scripts  
- [ ] Publish evaluation benchmark  

---

## 📄 License

MIT License.  
Please cite this repository if used in published work.

