# Weekly Water Inundation Mapping Using MODIS data and CNN-based method
The code in this repository is to develop and test a framework for quantifying pixel water fraction based on MODIS and ancillary data sources.
 <!-- Markdown
generate figures
 -->

Code was written in Python 3.6.3.

# Scripts lists
## 0extractAdmregion.py
* Extract city from china map
* Get the row and col num of landsat

## GetDataAttr.py
* Get row,path,date form landsat files
* Make pd.DataFrame

## GerRawData
* Move selected file to Interpretion folder
* Unzip the file and delete the zipped one
* Make data list

## InterpreteByRoi
* Do image-classfication by existing ROI based on folder
* Clip classified image
