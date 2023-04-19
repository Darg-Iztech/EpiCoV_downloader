# GISAID EpiCoV Downloader

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4323561.svg)](https://doi.org/10.5281/zenodo.4323561)

This is an updated version of GISAID downloader to retrieve all EpiCoV sequences and the table. The script utilizes Selenium to acess the GISAID website through a Firefox webdriver.

> **_WARNING:_** By using this software you agree GISAID's [Terms of Use](https://www.gisaid.org/DAA) and reaffirm your understanding of these terms.

## Installation

We provide a package file (environment.yml) to create a new environment (gisaid) using conda:

```bash
$ git clone https://github.com/poeli/EpiCoV_downloader.git
$ cd EpiCoV_downloader/
$ conda env create -f environment.yml
$ conda activate gisaid
```

:warning: Download [geckodriver](https://github.com/mozilla/geckodriver/releases) and put it in the same directory as this script.

## Example Run Command:
```bash
python gisaid_EpiCoV_downloader.py -u '<username>' -p '<password>' -o 'downloads/' -ht 'Human' -ss '2023-04-18' -se '2023-04-19' -voc 'omicron' -cg -hc -nnd
```

## Example Logs:

```txt
2023-04-19 17:09 [INFO] GISAID EpiCoV Utility v21.05.10
2023-04-19 17:09 [INFO] Opening browser...
2023-04-19 17:09 [INFO] Opening website GISAID...
2023-04-19 17:09 [INFO] GISAID Initiative
2023-04-19 17:09 [INFO] Logining to GISAID...
2023-04-19 17:09 [INFO] Navigating to EpiCoV...
2023-04-19 17:09 [INFO] Searching in EpiCoV...
2023-04-19 17:09 [INFO] Setting host...
2023-04-19 17:09 [INFO] Setting submissions start date...
2023-04-19 17:09 [INFO] Setting variant...
2023-04-19 17:09 [INFO] Selected VOC Omicron GRA (B.1.1.529+BA.*) first detected in Botswana/Hong Kong/South Africa...
2023-04-19 17:09 [INFO] Complete genome only...
2023-04-19 17:09 [INFO] High coverage only...
2023-04-19 17:10 [INFO] Selecting Total: 176 viruses...
2023-04-19 17:10 [INFO] Downloading sequences for selected genomes...
2023-04-19 17:10 [INFO] Switching to data selection iframe...
2023-04-19 17:10 [INFO] Selecting FASTA files...
2023-04-19 17:10 [INFO] Clicking download button...
2023-04-19 17:10 [INFO] Switching back to default page...
2023-04-19 17:10 [INFO] Switching to agreement iframe...
2023-04-19 17:10 [INFO] Accepting terms of use...
2023-04-19 17:10 [INFO] Clicking download button again...
2023-04-19 17:10 [INFO] Switching back to default page...
2023-04-19 17:10 [INFO] Downloaded to gisaid_hcov-19_2023_04_19_14.fasta
2023-04-19 17:10 [INFO] Completed.
```


## Usage
```bash
usage: gisaid_EpiCoV_downloader.py [-h] -u [STR] -p [STR] [-o [STR]]
                                   [-l [STR]] [-ht [STR]] [-cs [YYYY-MM-DD]]
                                   [-ce [YYYY-MM-DD]] [-ss [YYYY-MM-DD]]
                                   [-se [YYYY-MM-DD]] [-cg] [-hc] [-le]
                                   [-t [INT]] [-r [INT]] [-i [INT]] [-m]
                                   [--normal]

Download EpiCoV sequences from GISAID

optional arguments:
  -h, --help            show this help message and exit
  -u [STR], --username [STR]
                        GISAID username
  -p [STR], --password [STR]
                        GISAID password
  -o [STR], --outdir [STR]
                        Output directory
  -l [STR], --location [STR]
                        sample location
  -ht [STR], --host [STR]
                        Specify a host of the sample. Default is human.
  -cs [YYYY-MM-DD], --colstart [YYYY-MM-DD]
                        collection starts date
  -ce [YYYY-MM-DD], --colend [YYYY-MM-DD]
                        collection ends date
  -ss [YYYY-MM-DD], --substart [YYYY-MM-DD]
                        submissions start date
  -se [YYYY-MM-DD], --subend [YYYY-MM-DD]
                        submitssions end date
  -voc [STR], --variant [STR]
                        Variant of concern. One of:
                        ['', 'alpha', 'beta', 'gamma', 'delta', 'omicron']
  -cg, --complete       complete genome only
  -hc, --highcoverage   high coverage only
  -le, --lowcoverageExcl
                        low coverage excluding
  -t [INT], --timeout [INT]
                        set action timeout seconds. Default is 90 secs.
  -r [INT], --retry [INT]
                        retry how many times when the action fails. Default is
                        5 times.
  -i [INT], --interval [INT]
                        time interval between retries in second(s). Default is
                        3 seconds.
  --normal              run firefox in normal mode.
```
