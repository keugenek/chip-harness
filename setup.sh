#!/usr/bin/env bash
# Ubuntu 24.04. Installs the open flow used by harness/evaluate.py.
set -euo pipefail
sudo apt-get update
sudo apt-get install -y yosys iverilog verilator build-essential cmake tcl-dev swig bison flex \
     libeigen3-dev zlib1g-dev git autoconf automake libtool python3-pip
pip install --user yowasp-yosys            # current Yosys (0.71 at time of writing); or build Yosys natively for speed
# OpenSTA (needs CUDD)
git clone --depth 1 https://github.com/ivmai/cudd.git && (cd cudd && autoreconf -fi && ./configure --prefix=/opt/cudd && make -j"$(nproc)" && sudo make install)
git clone --depth 1 https://github.com/parallaxsw/OpenSTA.git && (cd OpenSTA && mkdir -p build && cd build && cmake -DCUDD_DIR=/opt/cudd -DCMAKE_BUILD_TYPE=Release .. && make -j"$(nproc)" && sudo make install)
# Cell library: IHP SG13G2 open PDK (Apache-2.0), already vendored under pdk/. To refresh:
#   B=https://raw.githubusercontent.com/IHP-GmbH/IHP-Open-PDK/main/ihp-sg13g2/libs.ref/sg13g2_stdcell
#   curl -fLO $B/lib/sg13g2_stdcell_typ_1p20V_25C.lib && python3 harness/lib2v.py sg13g2_stdcell_typ_1p20V_25C.lib pdk/sg13g2_func.v
echo "Run:  python3 harness/evaluate.py candidates/c2_booth_dadda   (YOSYS_SYN=yowasp-yosys to use the newer Yosys)"
