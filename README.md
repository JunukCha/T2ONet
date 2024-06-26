# Learning by Planning: Language-Guided Global Image Editing

## Instroduction
This is the Pytorch implementation for paper "Learning by Planning: Language-Guided Global Image Editing".

## Dependency

- Pytorch >= 1.0.0
- opencv-python 
- panopticapi
- pycocotools
- easydict
- tensorboardX
- tensorflow<2.0.0
- tabulate
- dominate
- kornia



## Installation

- Clone this repo

  ```shell
  git clone https://github.com/JunukCha/T2ONet.git --recursive
  ```

- Install the submodule `pyutils/edgeconnect` according to its [README](https://github.com/jshi31/edge-connect/tree/1f2658e3b190de47b86b9e25ff39227ed90d5f26).

  The critical thing is to download pre-trained model.

## Dataset

All the working directory for the following commands are project root.

### MIT-Adobe FiveKReq

- Download the fiveK image
  Download from [Google Drive](https://drive.google.com/file/d/1nv6cTObVK8JIokQYffOxj61TDgC7L9rT/view?usp=share_link)
  and unzip the file to `data/FiveK/images` in order to keep the data structure show in the [file tree](https://github.com/jshi31/T2ONet/tree/master/data/FiveK#file-tree).

- Test the dataloader by running
```shell
PYTHONPATH='.' python datasets/FiveKdataset.py
```

### GIER
Go to [GIER webpage](https://sites.google.com/view/gierdataset#h.ajpnfea0glk9), download the following files:
- Download the GIER images into `data/GIER/images`
- Download the GIER mask into `data/GIER/masks`
- Download the GIER feature to `data/GIER/features`

Finally, the data structure should be the same as the [file tree](https://github.com/jshi31/T2ONet/tree/master/data/GIER#file-tree).

Test the data loader by running 
```shell
PYTHONPATH='.' python datasets/GIERdataset.py
```



## Plan Action Sequences

#### FiveK

Generate action sequence using operation planning

```shell
PYTHONPATH='.' CUDA_VISIBLE_DEVICES=0 python preprocess/gen_greedy_seqs_FiveK.py
```

Or download the sequence from [Google Drive](https://drive.google.com/file/d/1sZzLykDeEB9a3oTQ6UN8hzfMcxHVeqvZ/view?usp=share_link) and unzip it to `output/actions_set_1`


#### GIER

Generate action sequence using operation planning (**currenty has error**)

```shell
PYTHONPATH='.' CUDA_VISIBLE_DEVICES=0 python preprocess/gen_greedy_seqs_GIER.py
```

Or download the sequence from [Google Drive](https://drive.google.com/file/d/1sZzLykDeEB9a3oTQ6UN8hzfMcxHVeqvZ/view?usp=share_link) and unzip it to `output/GIER_actions_set_1`

## T2ONet

### FiveK Train

```shell
PYTHONPATH='.' CUDA_VISIBLE_DEVICES=0 python experiments/t2onet/train_seq2seqL1.py --batch_size 64 --print_every 50 --checkpoint_every 1000 --num_iter 10000 --trial 2
```

### FiveK Test

```shell
PYTHONPATH='.' CUDA_VISIBLE_DEVICES=0 python experiments/t2onet/test_seq2seqL1.py --print_every 100 --visualize_every 100  --visualize 0 --is_train 0 --trial 1 
```

select the trial number indicates which model you will use. To test our provided model, first download it from [Google Drive](https://drive.google.com/file/d/1CCFOK8HJz7_sXw5Ih4A3Hit1S3UowO3j/view?usp=sharing) and unzip it to `output/FiveK_trial_1/seq2seqL1_model`

and set the trial argument as 1 in the testing model.

To visualize the result, set visualize argument as 1, and the result will be in `FiveK_trial_1/test/web`

### GIER Train

```shell
PYTHONPATH='.' CUDA_VISIBLE_DEVICES=0 python experiments/t2onet/train_GIER_seq2seqL1.py  --dataset GIER --session 3 --batch_size 64 --data_mode global+shapeAlign --print_every 100 --checkpoint_every 1000 --num_iter 20000 --trial 1 
```

### GIER Test

```shell
PYTHONPATH='.' CUDA_VISIBLE_DEVICES=0 python experiments/t2onet/test_GIER_seq2seqL1.py  --dataset GIER --session 3 --data_mode global+shapeAlign --print_every 20 --visualize_every 5 --visualize 0 --trial 7
```

To test our provided model, first download it from [Google Drive](https://drive.google.com/file/d/1ms0CHe5DQt3AbDPIh2tBRFvuUWwugbh9/view?usp=share_link) and unzip it to `output/GIER_trial_7/seq2seqL1_model`

and set the trial argument as 7 in the testing model.
