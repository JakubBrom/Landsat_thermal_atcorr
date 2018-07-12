##Raster=group
##Band_6=raster
##Emissivity=raster
##Water_vapour_contet=number
##Gain=number 0.055376
##Offset=number 1.18
##K1=number 607.76
##K2=number 1260.56
##Surface_temperature=output raster



import gdal
import sys, os
import numpy as np
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException



def readGeo(rast):
	"""
	Function readGeo reads raster and mask files and makes Numpy array with
	the data restricted by the mask.
	Inputs:
	- rast - raster in GDAL readable format
	- mask - raster mask in GDAL readable format. Data should be 8bit integer,
	         typicaly 0 (nodata) and 1 (data). 	
	"""
	
	# raster processing
	ds = gdal.Open(rast)
	gtransf = ds.GetGeoTransform()
	prj = ds.GetProjection() 
	try:
		rast_in = gdal.Dataset.ReadAsArray(ds).astype(np.float32)
		ds = None
	except:
		raise GeoAlgorithmExecutionException('Error reading raster data. File might be too big.')
	
	return rast_in, gtransf, prj

	
def outRast(rast_out, gtransf, prj, outFile):                         
	driver = gdal.GetDriverByName("Gtiff")                                                         
	ds = driver.Create(outFile, rast_out.shape[1],rast_out.shape[0], 1, gdal.GDT_Float32)    								
	ds.SetProjection(prj)
	ds.SetGeoTransform(gtransf)
	ds.GetRasterBand(1).WriteArray(rast_out)
	ds = None

	
def sensorRadiance(band, gain, offset):
	L_lambda = gain * band + offset
	return L_lambda
	

def brightTemperature(L_lambda, K1, K2):
	T_B = K2/(np.log(K1/L_lambda + 1))
	return T_B
	

#-------------------------------------------------------------------------------
# Jimenez-Munoz & Sobrino metoda
def calcGamma(L_lambda, T_B):
	c1 = 1.19104 * 10**(8)
	c2 = 14387.7
	lambd = 11.457
	gamma = 1/(c2*L_lambda/T_B**2 * (lambd**4/c1 * L_lambda + 1/lambd))
	return gamma	


def calcDelta(gamma, L_lambda, T_B):
	delta = -1 * gamma * L_lambda + T_B
	return delta
	
	
def calcPsi(humidity):
	psi1 = 0.14714 * humidity**2 - 0.15583 * humidity + 1.1234
	psi2 = (-1.1836) * humidity**2 - 0.37607 * humidity - 0.52894
	psi3 = (-0.04554) * humidity**2 + 1.8719 * humidity - 0.39071
	return psi1, psi2, psi3
	
	
def surfTempJMS(L_lambda, emis, gamma, delta, psi1, psi2, psi3):
	Ts = gamma * (1/emis * (psi1 * L_lambda + psi2) + psi3) + delta - 273.16
	return Ts

    
#-------------------------------------------------------------------------------
# vrstvy
thermal_band, gtransf, prj = readGeo(Band_6)
emis, gtransf, prj = readGeo(Emissivity)

# mezivypocty
humidity = Water_vapour_contet
L_lambda = sensorRadiance(thermal_band, Gain, Offset)
T_B = brightTemperature(L_lambda, K1, K2)
gamma = calcGamma(L_lambda, T_B)
delta = calcDelta(gamma, L_lambda, T_B)
psi1, psi2, psi3 = calcPsi(humidity)

# teplota povrchu
Ts_JMS = surfTempJMS(L_lambda, emis, gamma, delta, psi1, psi2, psi3)

# vystupy
outRast(Ts_JMS, gtransf, prj, Surface_temperature)

