ti# -*- coding: utf-8 -*-
"""
This script:
    - Do image-classfication by existing ROI based on folder
    - Clip classified image

Reference:
    - http://www.machinalis.com/blog/python-for-geospatial-data-processing/
@author: mao
"""

import numpy as np
import os
import glob
from subprocess import call

from osgeo import gdal
from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier

from matplotlib import pyplot as plt

def create_mask_from_vector(vector_data_path, cols, rows, geo_transform,
                            projection, target_value=1):
    """Rasterize the given vector (wrapper for gdal.RasterizeLayer)."""
    data_source = gdal.OpenEx(vector_data_path, gdal.OF_VECTOR)
    layer = data_source.GetLayer(0)
    driver = gdal.GetDriverByName('MEM')  # In memory dataset
    target_ds = driver.Create('', cols, rows, 1, gdal.GDT_UInt16)
    target_ds.SetGeoTransform(geo_transform)
    target_ds.SetProjection(projection)
    gdal.RasterizeLayer(target_ds, [1], layer, burn_values=[target_value])
    return target_ds


def vectors_to_raster(file_paths, rows, cols, geo_transform, projection):
    """Rasterize the vectors in the given directory in a single image."""
    labeled_pixels = np.zeros((rows, cols))
    for i, path in enumerate(file_paths):
        label = i+1
        ds = create_mask_from_vector(path, cols, rows, geo_transform,
                                     projection, target_value=label)
        band = ds.GetRasterBand(1)
        labeled_pixels += band.ReadAsArray()
        ds = None
    return labeled_pixels


def write_geotiff(fname, data, geo_transform, projection):
    """Create a GeoTIFF file with the given data."""
    driver = gdal.GetDriverByName('GTiff')
    rows, cols = data.shape
    dataset = driver.Create(fname, cols, rows, 1, gdal.GDT_Byte)
    dataset.SetGeoTransform(geo_transform)
    dataset.SetProjection(projection)
    band = dataset.GetRasterBand(1)
    band.WriteArray(data)
    dataset = None  # Close the file

class Rasterfolder:
    def __init__(self, folderpath):
       self.path = folderpath
       self.folder = os.path.basename(folderpath)
       self.filetifs = glob.glob(os.path.join(folderpath,'*.TIF'))
       self.landsat = self.folder[0:3]

    def bandfilter(self,filetifs,band):
        def isband(arg):
            tif = arg[0]
            band = arg[1]
            res0 = True in [(('B'+b) in tif[-7:]) for b in band]
            res1 = True in [(('B'+b+'0') in tif[-7:]) for b in band]
            return (res0 or res1)
        arg = [y for y in zip(filetifs,[band for x in range(len(filetifs))])]
        ft_arg = list(filter(isband, arg))
        ft = [x[0] for x in ft_arg]
        return ft

    def filefilter(self):
        landsat = self.landsat
        if landsat == 'LC8':
            band  = '234567'
            self.filetifs = self.bandfilter(self.filetifs,band)
        if landsat == 'LT5':
            band = '123457'
            self.filetifs = self.bandfilter(self.filetifs,band)
        if landsat == 'LE7':
            band = '123457'
            self.filetifs = self.bandfilter(self.filetifs,band)

class Classifyfolder(Rasterfolder):
    def __init__(self,filepath):
        super(Classifyfolder, self).__init__(filepath)
        self.filefilter()

    def readgeo(self,tif):
        ras = gdal.Open(tif,gdal.GA_ReadOnly)
        geo_transform = ras.GetGeoTransform()
        proj = ras.GetProjectionRef()
        ras = None
        return (geo_transform,proj)

    def readtifs(self):
        bands_data = []
        for tif in self.filetifs:
            ras = gdal.Open(tif,gdal.GA_ReadOnly)
            for b in range(1, ras.RasterCount+1):
                band = ras.GetRasterBand(b)
                bands_data.append(band.ReadAsArray())
            ras = None
        self.data = np.dstack(bands_data)
        self.rows, self.cols, self.n_bands = self.data.shape
        self.geo_transform,self.proj = self.readgeo(tif)

    def GetTrainingSamples(self):
        self.classes = ['w','nw']
        files = ['w.shp','nw.shp']
        shapefiles = [os.path.join(self.path, f) for f in files]
        labeled_pixels = vectors_to_raster(shapefiles, self.rows, self.cols, self.geo_transform, self.proj)
        is_train = np.nonzero(labeled_pixels)
        self.training_labels = labeled_pixels[is_train]
        self.training_samples = self.data[is_train]

    def Training(self):
        classifier = RandomForestClassifier(n_jobs=-1)
        classifier.fit(self.training_samples, self.training_labels)
        n_samples = self.rows*self.cols
        flat_pixels = self.data.reshape((n_samples, self.n_bands))
        result = classifier.predict(flat_pixels)
        self.classification = result.reshape((self.rows, self.cols))

    def PlotRes(self):
        f = plt.figure()
        f.add_subplot(1, 2, 2)
        r = self.data[:,:,3]
        g = self.data[:,:,4]
        b = self.data[:,:,2]
        rgb = np.dstack([r,g,b])
        f.add_subplot(1, 2, 1)
        plt.imshow(rgb/255)
        f.add_subplot(1, 2, 2)
        plt.imshow(self.classification)

    def Evaluate(self):
        files = ['w.shp','nw.shp']
        shapefiles = [os.path.join(self.path, f) for f in files]
        verification_pixels = vectors_to_raster(shapefiles, self.rows, self.cols,self.geo_transform, self.proj)
        for_verification = np.nonzero(verification_pixels)
        verification_labels = verification_pixels[for_verification]
        predicted_labels = self.classification[for_verification]
        print("Confussion matrix:\n%s" % metrics.confusion_matrix(verification_labels, predicted_labels))
        target_names = ['Class %s' % s for s in self.classes]
        print("Classification report:\n%s" % metrics.classification_report(verification_labels, predicted_labels,target_names=target_names))
        print("Classification accuracy: %f" %metrics.accuracy_score(verification_labels, predicted_labels))

    def writeclass(self):
        fname = os.path.join(self.path,'class.tif')
        write_geotiff(fname, self.classification, self.geo_transform, self.proj)

    def ClipByMask(self):
        mask = os.path.join(self.path,'clip.shp')
        file = os.path.join(self.path,'class.tif')
        outname = os.path.join(self.path,self.folder+'_class.tif')
        call('gdalwarp -cutline '+mask+' '+'-crop_to_cutline '+file+' '+outname+' -overwrite')

def processfolder(filepath):
    cf=Classifyfolder(filepath)
    cf.readtifs()
    cf.GetTrainingSamples()
    cf.Training()
    #cf.PlotRes()
    cf.Evaluate()
    cf.writeclass()
    cf.ClipByMask()

if __name__ == '__main__':
    path = r'C:\Users\dell\Desktop\0331'
    dirs = os.listdir(path)
    while dirs != []:
        processfolder(os.path.join(path,dirs[0]))
        print(dirs[0]+' done!')
        dirs.pop(0)
