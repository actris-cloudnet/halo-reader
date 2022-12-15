### Format [Eriswil 2022-12-14](tests/raw-files/pass/eriswil-2022-12-14-Stare_91_20221214_11.hpl)
The most common format:
```
Filename:	Stare_91_20221214_11.hpl
System ID:	91
Number of gates:	250
Range gate length (m):	48.0
Gate length (pts):	16
Pulses/ray:	20000
No. of rays in file:	1
Scan type:	Stare
Focus range:	65535
Start time:	20221214 11:00:18.99
Resolution (m/s):	0.0382
Altitude of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)
i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates
****
11.00499444   0.00  90.00 -0.01 -0.20
  0 2.5990 1.027855  1.569249E-6
  1 -0.0764 1.014089  7.960566E-7
  2 -1.0702 1.005351  3.037474E-7
  3 -0.5351 1.005545  3.168804E-7
  4 -0.8026 1.005105  2.941327E-7
  5 -0.3440 1.006821  3.970078E-7
  6 -0.5733 1.005150  3.032375E-7
```

### Format [Warsaw 2022-12-13](tests/raw-files/pass/warsaw-2022-12-13-Stare_213_20221213_04.hpl)

If include spectral width option is turned on,
each gate row has a value for `spectral width`.
However, this is not always mentioned in the header (`Data line 2`).

```
Filename:	Stare_213_20221213_04.hpl
System ID:	213
Number of gates:	333
Range gate length (m):	30.0
Gate length (pts):	10
Pulses/ray:	10000
No. of rays in file:	1
Scan type:	Stare
Focus range:	65535
Start time:	20221213 04:00:24.32
Resolution (m/s):	0.0382
Altitude of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)
i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates
**** Instrument spectral width = 7.796967
4.00648333 359.99  90.01 -0.01 -0.40
  0 -0.1147 1.155508  8.757579E-6 0.0382
  1 -2.2932 0.958382 -2.347047E-6 0.0382
  2 16.1672 1.030337  1.714464E-6 1.5670
  3 0.1529 1.100692  5.706656E-6 6.2299
  4 -0.1911 1.104814  5.961256E-6 5.8095
  5 -0.1911 1.128393  7.333278E-6 5.9624
  6 0.1911 1.170483  9.785261E-6 6.0388
```

### Format [Soverato 2021-10-01](tests/raw-files/pass/soverato-2021-10-01-VAD_194_20210624_170110.hpl)

Sometimes `spectral width` is included in the header.

```
Filename:	VAD_194_20210624_170110.hpl
System ID:	194
Number of gates:	400
Range gate length (m):	30.0
Gate length (pts):	20
Pulses/ray:	10000
No. of rays in file:	6
Scan type:	VAD
Focus range:	65535
Start time:	20210624 17:01:15.65
Resolution (m/s):	0.0764
Range of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1) Spectral Width
i3,1x,f6.4,1x,f8.6,1x,e12.6,1x,f6.4 - repeat for no. gates
**** Instrument spectral width = 5.656623
17.02071944 360.00  75.00 -0.11 -0.51
  0 -0.5351 1.238768  1.344642E-5 0.0764
  1 -26.7543 1.015366  8.665689E-7 0.0764
  2 -0.2293 1.234543  1.325509E-5 6.5739
  3 -0.3058 1.380099  2.154184E-5 6.1153
  4 -0.2293 1.376810  2.143096E-5 6.1917
  5 -0.1529 1.358591  2.048121E-5 6.1153
  6 -0.1529 1.351057  2.014977E-5 6.1153
```

### Variations

Header fields might vary between formats.
For example, `No. of rays in file` might be
replaces with `No. of waypoints in file`.
[Header grammar](src/halo_reader/grammar_header.lark)
defines currently supported header formats.

### Time overflow
Time is represented in decimal hours
i.e. hours since the beginning of the day of the measurement.
Decimal hours overflows if the measurement goes to the next day.
That is, 24.01 hours becomes 0.01 hours.
Reader fixes these such that:
`t_i += 24h if t_{-1} - t_i > 12h`.



### Incorrect raw files
Sometimes the number of gates per profiles differs from the header,
or might change in the middle of the file.
In these cases, reader raises an error.
