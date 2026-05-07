---
layout: default
title: "SSH:  Before we begin; Accessing the Linux, your Project (IMPACT), and creating a DTI directory"
parent: "Introduction"
nav_order: 1
---

# SSH:  Before we begin; Accessing the Linux, your Project (IMPACT), and creating a DTI directory

1. SSH Into the Linux
From your local terminal:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
```

2. Navigate to Project Impact DICOMs
```bash
cd /data/projects/STUDIES/IMPACT/fMRI/dicoms
# this will take us into the raw dicoms

ls # checking the list of participants
s0105-pilot  s1000  s1228-pilot  s1253  s1323  s1350 ...
s4427  s4436  s4446  s4449  s4459  s4482 ...
```

3. Where Will the DTI Files Go?
I created this file:
```bash
tur50045@cla19097:/data/projects/STUDIES/IMPACT$ mkdir DTI
mkdri /DTI/config ##we will put configuration txt files neccesary for DTI preprocessing here
```
* Note: All the configutation files needed for this pipeline can be found in the /config folder of this repo: https://github.com/DiffusionTensorImaging-Repos/SDN-IMPACT-DTI/tree/bd9b3a1670651fc73af3fec46001cdf099ea086b/config

