# -*- coding=utf-8 -*-
"""
This script:
    - helps to extract city from china map
    - get the row and col num of landsat

python 2.7 with arcpy
@author: mao
"""
import arcpy

arcpy.env.workspace = r'C:\Users\dell\Desktop\inundation model\training sample extraction\data\wrs2_asc_desc'
arcpy.env.overwriteOutput = True

#input city name
city_PD = [u'香港特别行政区',u'珠海市',u'佛山市',u'惠州市',u'肇庆市',u'江门市',u'中山市',u'东莞市',u'澳门特别行政区',u'深圳市',u'广州市']

city_field = u'City'
city_china = "country_China.shp" #extract from mdb
outfc = 'city_PD.shp' #output name

citynum = len(city_PD)
where_clause = '('+city_field+'='+"\'"+city_PD[0]+"\'"+')'
i=1
while i<citynum:
    where_clause = where_clause+' '+'OR'+' '+'('+city_field+'='+"\'"+city_PD[i]+"\'"+')'
    i+=1

arcpy.Select_analysis(city_china, outfc, where_clause)

globallandsat = u'wrs2_descending.shp'
outlandsat = u'landsat_PD.shp'
arcpy.Clip_analysis(globallandsat, outfc, outlandsat)
landsat_PD = []
with arcpy.da.SearchCursor(outlandsat,['ROW','PATH']) as cursor:
    for row in cursor:
        #print "ROW:"+str(row[0])+' '+'PATH:'+str(row[1])
        pathrow = (row[0],row[1])
        landsat_PD.append(pathrow)

landsat_PD.sort(key=lambda x:(x[0],-x[1]))
print landsat_PD

#[(43, 123), (43, 122), (44, 124), (44, 123), (44, 122), (44, 121), (45, 123), (45, 122), (45, 121)]
