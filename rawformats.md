
### Format 1

```
Filename:	Stare_91_20220210_00.hpl
System ID:	91
Number of gates:	4
Range gate length (m):	48.0
Gate length (pts):	16
Pulses/ray:	40000
No. of rays in file:	1
Scan type:	Stare
Focus range:	65535
Start time:	20220210 00:01:42.66
Resolution (m/s):	0.0382
Altitude of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)
i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates
****
0.02823611   0.00  90.00 -0.01 0.20
  0 1.9110 0.978410 -1.216295E-6
  1 -0.0764 1.014059  7.943521E-7
  2 -0.3058 1.013439  7.629040E-7
  3 -0.1911 1.012520  7.154071E-7
 ```

### Format 2

* `Instrument spectral width` in the header separator.
* Second data line has a column not mentioned in the header

Example:
Warsaw 2022-10-17


```
Filename:	Stare_213_20221212_03.hpl
System ID:	213
Number of gates:	4
Range gate length (m):	30.0
Gate length (pts):	10
Pulses/ray:	10000
No. of rays in file:	1
Scan type:	Stare
Focus range:	65535
Start time:	20221212 03:00:23.51
Resolution (m/s):	0.0382
Altitude of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)
i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates
**** Instrument spectral width = 7.796967
3.00625556 359.99  90.01 -0.01 -0.40
  0 0.0382 1.119961  6.755712E-6 0.0382
  1 -3.0576 1.003456  1.948850E-7 0.0382
  2 -0.8791 1.074483  4.209366E-6 2.7519
  3 -0.9555 1.164848  9.342642E-6 5.8095
```

### Format with Spectral width in header
eg. Soverato 2021-06-23

```
Filename:	Stare_194_20210623_18.hpl
System ID:	194
Number of gates:	4
Range gate length (m):	30.0
Gate length (pts):	20
Pulses/ray:	10000
No. of rays in file:	1
Scan type:	Stare
Focus range:	65535
Start time:	20210623 18:00:36.35
Resolution (m/s):	0.0764
Range of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1) Spectral Width
i3,1x,f6.4,1x,f8.6,1x,e12.6,1x,f6.4 - repeat for no. gates
**** Instrument spectral width = 5.656623
18.00980278  89.98  90.00 -0.01 -0.40
  0 -0.3822 1.303008  1.706415E-5 0.0764
  1 -27.2894 1.034719  1.957962E-6 0.0764
  2 -0.2293 1.257610  1.455869E-5 6.5739
  3 -0.2293 1.402832  2.283024E-5 6.1917
```
