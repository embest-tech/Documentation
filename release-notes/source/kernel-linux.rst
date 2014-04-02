Linux Kernel
============
.. |linux_imx_version_mx6| replace:: 3.0.35_4.1.0
.. |linux_imx_version_mxs5| replace:: 2.6.35_maintain
.. |linux_fslc_version| replace:: 3.11
.. |linux_boundary_version| replace:: 3.0.35_4.1.0
.. |linux_cfa_version| replace:: 3.10
.. |linux_timesys_version_pcl052| replace:: 3.0.15
.. |linux_timesys_version_pcm052| replace:: 3.0.15
.. |linux_timesys_version_quartz| replace:: 3.0.15
.. |linux_wandboard_version| replace:: 3.0.35_4.0.0


Fsl-community-bsp supports the following sources for Linux Kernel:

.. include:: ../../scripts/extracted-data/fsl_community_bsp_supported_kernels.inc

-----------------------
Default Linux Providers
-----------------------

The following table shows the default version of Linux Kernel provided by
FSL Community BSP for each supported machine.

.. include:: ../../scripts/extracted-data/linux-default.inc


-----------
linux-fslc
-----------

linux-fslc provides the Linux Kernel |linux_fslc_version| from mainline (kernel.org)
with some backported fixes.

For the mainline kernel some boards has a very good support, although
other ones has only a basic support.

Please, see in the following table which are the main features supported
by mainline kernel for each supporte board.


.. include:: linux-fslc.inc

