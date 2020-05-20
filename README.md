# Polar Codes #
This is a library and simulation tool for a Forward Error Correcting (FEC)
scheme named "Polar Codes". A very promising group of codes that have low
encoding and decoding latency with high BLER-performance.

## Installation
This should be straight forward, given that you have a recent compiler (GCC).

You need to clone the repo with the `--recursive` option to ensure that the `pybind11` submodule is checked out as well.
`git clone --recursive`

### Dependencies
Before compiling this project the following packages need to be installed
on your system:

### Debian/Ubuntu
- doxygen
- libcppunit-dev
- libtclap-dev
- libssl-dev

### The install commands
```
mkdir build
cd build
cmake ..
make -j<cputhreads>
make install
```

## Basic usage
In `build/bin`
```
./pctest  # Run a set of C++ tests
./pcsim   # Run C++ simulations
```

## Python interface usage
With `import pypolar` you can use the Encoders, Decoders, Puncturers and Detectors with Python3. Also, you can use `pypolar.frozen_bits` to get a suitable frozen bit set for polar codes.


## Library description #
The library is split into four independent modules:

- An encoder,
- a decoder,
- error detection for list decoding and
- a code constructor

Their respective base classes are purely virtual, so every algorithm
implementation can be called via the base object's functions. This allows for
easy testing as you can throw any algorithm at a general performance tester
without having to modify the testers code in any way.
