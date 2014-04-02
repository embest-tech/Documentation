#! /bin/sh

### This script generates documentation based on metadata extracted
### out of BitBake's cache data.
###
### It basically sources setup-environment and run
### extract-bitbake-metadata.py for each given machine (if the
### MACHINES environment variable is set, uses it, otherwise find
### machine files in yocto_dir). extract-bitbake-metadata.py collects
### data from the BitBake cache for each machine and writes a file
### (doc-data.pckl, in Python's pickle format) which is eventually
### used by bitbake-metadata2doc.py to transform all the collected
### data into documentation in rst format.

# Check if running from the scripts dir
if [ "`basename $PWD`" != "scripts" ]; then
    echo "This script is expected to be run from the scripts directory" >&2
    exit 1
fi

usage() {
    local exit_code
    local output
    [ -n $1 ] && exit_code=$1
    if [ -n "$exit_code" ] && [ "$exit_code" != "0" ]; then
        output=2
    else
        output=1
    fi
    echo "Usage: `basename $0` <yocto directory>" >&$output
    [ -n "$exit_code" ] && exit $exit_code
}


[ -z "$1" ] && usage 1

if [ "$1" = "-h" ] || [ "$1" = "-help" ] || [ "$1" = "--help" ]; then
    usage 0
fi

yocto_dir="$1"
anchor="`pwd`"

machines=
if [ -n "$MACHINES" ]; then
    machines="$MACHINES"
else
    machines=`./output-machine-list $yocto_dir`
fi

marshalled_data_file=doc-data.pckl

rm -f $anchor/$marshalled_data_file

for machine in $machines; do
    cd $yocto_dir
    MACHINE=$machine . ./setup-environment build

    $anchor/extract-bitbake-metadata.py \
        $anchor/doc-data.pckl \
        virtual/kernel \
        virtual/bootloader \
        barebox \
        gstreamer \
        libdrm \
        udev xserver-xorg \
        firmware-imx \
        fsl-alsa-plugins \
        gpu-viv-bin-mx6q \
        gpu-viv-g2d \
        gst-fsl-plugin \
        imx-kobs \
        imx-lib \
        imx-test \
        libfslcodec \
        libfslparser \
        libfslvpuwrap \
        xf86-dri-vivante \
        xf86-video-imxfb-vivante
done

cd $anchor
mkdir -p extracted-data
./bitbake-metadata2doc.py $marshalled_data_file extracted-data