 # Xilinx FPGA symbol creator
This project aims to accelerate drawing of Xilinx FPGA schematic symbols using [pin description](https://www.xilinx.com/support/package-pinout-files/spartan-7-pkgs.html) text files provided by the manufacturer. The script generates a KiCAD Eeschema library that needs to be slightly modified to meet [KLC](https://kicad-pcb.org/libraries/klc/).

## Sample output for FPGA XC7S15 FTGB196
 ![demo](https://raw.github.com/https://github.com/wykys/xilinx-fpga-symbol-creator/master/img/demo.svg?sanitize=true)

## How to use?
```bash
# help
src/main.py -h
```
```bash
# result
usage: Xilinx FPGA symbol creator [-h] path part name

positional arguments:
  path        Xilinx text file pin description.
  part        The name under which the part will be created in the library.
  name        Marking on the schematic symbol.

optional arguments:
  -h, --help  show this help message and exit
```

``` bash
# create a library
src/main.py data/xc7s15ftgb196pkg.txt "XC7S15-FTGB196" "Spartan 7" > my_library.lib
```