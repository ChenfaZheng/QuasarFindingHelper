<!--
 * @Date: 2021-07-19 01:47:27
 * @LastEditors: chenfa
 * @LastEditTime: 2021-07-23 22:10:09
-->
# Quasar Finding Helper

A simple script for summarizing quasar information into one picture.

Applicable to Linux os. 

## Utility

- Searching and collecting data from http://astrogeo.org/vlbi_analysis/ (using Selenium)
- Cross-matching name and gain redshift from http://www.gaoran.ru/english/as/ac_vlbi/ocars.txt
- Summarizing quasar information into one picture.

## Usage

- Download source code and extract it into a certain path, e.g., `~/QuasarFindingHelper`. Then `cd` into it.
- Put the .xlsx file into `~/QuasarFindingHelper` directory (the same directory as `QuasarFindingHelper.py`).
- Run with `python QuasarFindingHelper.py` for default (range [0, row_number)), or specify start and end id by `python QuasarFindingHelper.py <start_id> <end_id>` (range [start_id, end_id), use `-1` for default)

## Dependences

### Python Libs

```python
import os
import sys
import wget

import pandas as pd 
import numpy as np 

import matplotlib.pyplot as plt 
from PIL import Image
from astropy.coordinates import FK5
from astropy.coordinates import SkyCoord

from urllib.error import ContentTooShortError
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
```

### Others

- https://github.com/mozilla/geckodriver/releases
- gostscript

## Contact

zhengcf@mail.bnu.edu.cn
