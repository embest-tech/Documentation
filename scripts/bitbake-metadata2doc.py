#! /usr/bin/env python

import os
import re
import sys
import pickle

def info(fmt, *args):
    print(fmt % args)

def warn(fmt, *args):
    sys.stderr.write(('WARNING: ' + fmt + '\n') % args)

def error(fmt, *args):
    sys.stderr.write(('ERROR: ' + fmt + '\n') % args)

def tabularize(lines, spacing=2):
    def format_border(widths):
        return spc.join([ '=' * width for width in widths ])

    def format_header(header, widths, spc):
        border = format_border(widths)
        header = spc.join(map(lambda col, width: col.ljust(width),
                              header, widths))
        return '\n'.join([border, header, border])

    def sort_by_col(lines, col):
        return sorted(lines, key=lambda l: l[col])

    def format_body(lines, widths, spc):
        def format_line (line):
            return spc.join(map(lambda col, width: col.ljust(width),
                                line, widths))
        return "\n".join(map(format_line, sort_by_col(lines, 0)))

    spc = ' ' * spacing
    if lines:
        col_widths = map(lambda col: apply(max, map(len, col)),
                         apply(zip, lines))
        return '\n'.join([format_header(lines[0], col_widths, spc),
                          format_body(lines[1:], col_widths, spc),
                          format_border(col_widths)]) + \
               '\n'
    else:
        return ""

def describe(items):
    text = ''
    for item in items:
        text += ''.join(['* ', '**', item[0], '**: ', item[1], '\n'])
    return text

def is_in_soc_family(soc, soc_family):
    return soc in soc_family.split(':')

def is_compatible_machine(soc_family, compatible_machine_re):
    socs = soc_family.split(':')
    compatible_machine_pattern = re.compile(compatible_machine_re)
    for soc in socs:
        if compatible_machine_pattern.match(soc):
            return True
    return False

def format_version(version):
    version = str(version)
    if 'gitAUTOINC' in version:
        return 'git'
    else:
        ## remove <x> in case versions are in the <x>:<y> format
        comma_prefix = re.compile('\\d+:(.*)')
        match = comma_prefix.match(version)
        if match:
            return match.groups()[0]
        else:
            return version

def write_inc_file(out_dir, file, text):
    out_file = os.path.join(out_dir, file)
    info('Writing %s' % out_file)
    out_fd = open(out_file, 'w')
    out_fd.write(text)
    out_fd.close()

def write_tabular(out_dir, file, header, body):
    table = [header] + body
    write_inc_file(out_dir, file, tabularize([header] + body))

def write_table_by_recipe(out_dir, file, recipe, header, data):
    body = []
    for board in data.keys():
        recipe_data = data[board]['recipes'][recipe]
        body += [[board, recipe_data['recipe'], recipe_data['version']]]
    write_tabular(out_dir, file, header, body)

def write_linux_table(data, out_dir):
    write_table_by_recipe(out_dir,
                          'linux-default.inc',
                          'virtual/kernel',
                          ['Board', 'Kernel Provider', 'Kernel Version'],
                          data)

def write_u_boot_table(data, out_dir):
    ## Pick only boards whose bootloader is U-Boot
    uboot_data = {}
    for board, board_data in data.items():
        ## The default IMAGE_BOOTLOADER is u-boot, as set by image_types_fsl.bbclass
        if not board_data['image-bootloader'] or \
           board_data['image-bootloader'] == 'u-boot':
            uboot_data[board] = board_data
    write_table_by_recipe(out_dir,
                          'u-boot-default.inc',
                          'virtual/bootloader',
                          ['Board', 'U-Boot Provider', 'U-Boot Version'],
                          uboot_data)

def write_barebox_table(data, out_dir):
    boards = filter(lambda board: data[board]['recipes'].has_key('barebox') and \
                                  (data[board]['image-bootloader'] == 'barebox' or \
                                   data[board]['recipes']['virtual/bootloader']['recipe'] == 'barebox'),
                    data.keys())
    boards_data = {}
    for board in boards:
        boards_data[board] = data[board]
    write_table_by_recipe(out_dir,
                          'barebox-mainline.inc',
                          'barebox',
                          ['Board', 'Barebox Provider', 'Barebox Version'],
                          boards_data)

def write_fsl_community_bsp_supported_kernels(data, out_dir):
    kernels = []
    kernel_recipes = [] # just to keep track of recipes already collected
    for board, board_data in data.items():
        kernel = board_data['recipes']['virtual/kernel']
        recipe = kernel['recipe']
        if (kernel['layer'] in ['meta-fsl-arm', 'meta-fsl-arm-extra']) and \
            recipe not in kernel_recipes:
            kernels += [[recipe, kernel['description']]]
            kernel_recipes.append(recipe)
    write_inc_file(out_dir, 'fsl-community-bsp-supported-kernels.inc', describe(kernels))


def write_userspace_pkg(data, out_dir):
    pkgs = {'gstreamer': [],
            'libdrm': [],
            'udev': []}
    for board, board_data in data.items():
        for pkg in pkgs.keys():
            versions = pkgs[pkg]
            version = board_data['recipes'][pkg]['version']
            if version not in versions:
                pkgs[pkg].append(version)

    ## Check if all the versions are the same for each package
    multiple_versions = []
    for pkg, versions in pkgs.items():
        if len(versions) > 1:
            multiple_versions.append((pkg, versions))
    for pkg, vs in multiple_versions:
        error('multiple versions have been found for %s: %s' % (pkg, ', '.join(map(str, vs))))
    if multiple_versions:
        sys.exit(1)

    ## Check if packages are available for all SoCs:
    pkg_board_restriction = False
    for pkg in pkgs:
        for board_data in data.values():
            compatible_machine = board_data['recipes'][pkg]['compatible-machine']
            if compatible_machine:
                pkg_board_restriction = True
                error('Package %s has restrictions with regard to boards: COMPATIBLE_MACHINE=%s' % (pkg, compatible_machine))
    if pkg_board_restriction:
        sys.exit(1)

    ## Finaly write the table
    write_tabular(out_dir,
                  'userspace-pkg.inc',
                  ['Package', 'Board/SoC Family', 'Version'],
                  [ [pkg, 'All', format_version(version[0])] for pkg, version in pkgs.items() ])


def write_soc_pkg(data, out_dir):
    socs = {'mx28': [],
            'mx5': [],
            'mx6': [],
            'vf60': []}
    pkgs = ['imx-test',
            'gst-fsl-plugin',
            'libfslcodec',
            'libfslparser',
            'imx-vpu',
            'imx-lib',
            'firmware-imx',
            'mxsldr',
            'gpu-viv-g2d',
            'xf86-video-imxfb-vivante',
            'gpu-viv-bin-mx6q',
            'directfb',
            'directfb-examples',
            'xf86-video-imxfb',
            'amd-gpu-bin-mx51',
            'libz160',
            'amd-gpu-x11-bin-mx51',
            'libfslvpuwrap',
            'fsl-alsa-plugins',
            'gstreamer1.0-plugins-imx',
            'imx-uuc',
            'libmcc',
            'mqxboot']
    ## Fill the socs dictionary
    for board, board_data in data.items():
        soc_family = board_data['soc-family']
        for soc in socs.keys():
            if is_in_soc_family(soc, soc_family):
                socs[soc].append(board)
    ## Check if the same board is not in multiple SoCs
    boards_socs = {}
    board_in_multiple_socs = False
    for soc, boards in socs.items():
        for board in boards:
            if boards_socs.has_key(board):
                board_in_multiple_socs = True
                error('Board %s has been found in both %s and %s SoCs' % (board, boards_socs[board], soc))
            else:
                boards_socs[board] = soc
    if board_in_multiple_socs:
        sys.exit()

    ## Use the most frequent package versions among boards of the same
    ## SoC, in case of different versions for the same package
    pkgs_socs_versions = {}
    for pkg in pkgs:
        for soc, boards in socs.items():
            pkg_versions = {}
            for board in boards:
                recipe = data[board]['recipes'][pkg]
                compatible_machine = recipe['compatible-machine']
                if not compatible_machine or \
                   (compatible_machine and \
                    is_compatible_machine(data[board]['soc-family'], compatible_machine)):
                    pkg_versions[board] = recipe['version']
                else:
                    ## The package is not for that board
                    pkg_versions[board] = -1

            versions = pkg_versions.values()
            versions_histogram = {}
            for version in versions:
                if versions_histogram.has_key(version):
                    versions_histogram[version] += 1
                else:
                    versions_histogram[version] = 1
            versions_freq = versions_histogram.values()
            most_freq = max(versions_freq)
            ## More than one "most frequent" version?
            if versions_freq.count(most_freq) > 1:
                error('The most frequent versions (%s) for %s are equally distributed among boards of SoC %s.  Cannot determine which one to use.' % \
                          ([ ver for ver, count in versions_histogram.items() if count == most_freq ],
                           pkg,
                           soc))
                sys.exit(1)
            else:
                pkg_version = None
                for version, count in versions_histogram.items():
                    if count == most_freq:
                        pkg_version = version
                        break
                pkgs_socs_versions[(pkg, soc)] = pkg_version

    ## Build up the table body
    body = []
    soc_names = sorted(socs.keys())
    for pkg in pkgs:
        versions = [ pkgs_socs_versions[(pkg, soc)] for soc in soc_names ]
        def replace_noversions(versions):
            new_versions = []
            for v in versions:
                if v == -1:
                    new_versions.append('-')
                else:
                    new_versions.append(format_version(v))
            return new_versions
        body.append([pkg] + replace_noversions(versions))

    ## Finally write the table
    write_tabular(out_dir,
                  'soc-pkg.inc',
                  ['Package name'] + soc_names,
                  body)


def usage(exit_code=None):
    print 'Usage: %s <data file> <output dir>' % (os.path.basename(sys.argv[0]),)
    if exit_code:
        sys.exit(exit_code)


if '-h' in sys.argv or '-help' in sys.argv or '--help' in sys.argv:
    usage(0)

if len(sys.argv) < 2:
    usage(1)

data_file = sys.argv[1]
out_dir = sys.argv[2]

data_fd = open(data_file, 'r')
data = pickle.load(data_fd)
data_fd.close()

try:
    os.mkdir(out_dir)
except:
    if not os.path.isdir(out_dir):
        sys.stderr.write('A file named %s already exists. Aborting.' % out_dir)
        sys.exit(1)
    else:
        pass # if a directory already exists, it's ok

write_linux_table(data, out_dir)
write_u_boot_table(data, out_dir)
write_barebox_table(data, out_dir)
write_fsl_community_bsp_supported_kernels(data, out_dir)
write_userspace_pkg(data, out_dir)
write_soc_pkg(data, out_dir)