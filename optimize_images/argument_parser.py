# encoding: utf-8
import os
import re

from argparse import ArgumentParser
from optimize_images.constants import DEFAULT_QUALITY


def get_args():
    desc = "A command-line utility written in pure Python to reduce the file " \
           "size of images. You must explicitly pass it a path to the image " \
           "file or to the directory containing the image files to be " \
           "processed. Please note that the operation is done DESTRUCTIVELY, " \
           "by replacing the original files with the processed ones. You " \
           "definitely should duplicate the original file or folder before " \
           "using this utility, in order to be able to recover any damaged " \
           "files or any resulting images that don't have the desired quality."
    parser = ArgumentParser(description=desc)

    path_help = "The path to the image file or to the folder containing the " \
                "images to be optimized. By default, it will try to process " \
                "any images found in all of its subdirectories."
    parser.add_argument('path', nargs="?", type=str, help=path_help)

    parser.add_argument('-v', '--version', action='version',
                        version=__import__('optimize_images').__version__)

    sf_help = "Display the list of image formats currently supported by this application."
    parser.add_argument('-sf', '--supported-formats',
                        action='store_true', help=sf_help)

    parser.add_argument('-nr', '--no-recursion', action='store_true',
                        help="Don't recurse through subdirectories.")

    size_msg = "These options will be applied individually to each " \
               "image being processed. Any image that has a dimension " \
               "exceeding a specified value will be downsized as the first " \
               "optimization step. The resizing will not take effect if, " \
               "after the whole optimization process, the resulting file " \
               "size isn't any smaller than the original. These options are " \
               "disabled by default."
    size_group = parser.add_argument_group(
        'Image resizing options', description=size_msg)

    mw_help = "The maximum width (in pixels)."
    size_group.add_argument(
        '-mw', "--max-width", type=int, default=0, help=mw_help)

    mh_help = "The maximum height (in pixels)."
    size_group.add_argument(
        '-mh', "--max-height", type=int, default=0, help=mh_help)

    jpg_msg = 'The following options apply only to JPEG image files.'
    jpg_group = parser.add_argument_group(
        'JPEG specific options', description=jpg_msg)

    q_help = "The quality for JPEG files (an integer value, between 1 and " \
             "100). A lower value will reduce the image quality and the " \
             "file size. The default value is 70."
    jpg_group.add_argument(
        '-q', "--quality", type=int, default=DEFAULT_QUALITY, help=q_help)

    jpg_group.add_argument(
        '-ke',
        "--keep-exif",
        action='store_true',
        help="Keep image EXIF data (by default, EXIF data is discarded).")

    png_msg = 'The following options apply only to PNG image files.'
    png_group = parser.add_argument_group(
        'PNG specific options', description=png_msg)

    rc_help = "Reduce colors (PNG) using an adaptive color palette with " \
              "dithering. This option can have a big impact on file size, " \
              "but please note that will also affect image quality."
    png_group.add_argument(
        '-rc', "--reduce-colors", action='store_true', help=rc_help)
    mc_help = "The maximum number of colors for PNG images when using " \
              "the reduce colors (-rc) option (an integer value, between 0 " \
              "and 255). The default is 255."
    png_group.add_argument(
        '-mc', "--max-colors", type=int, default=256, help=mc_help)

    bg_help = "The background color to use when doing operations that remove " \
              "transparency, like reducing colors or converting from PNG to " \
              "JPEG (3 integer values, separated by spaces, between 0 and 255 for " \
              "Red, Green and Blue, e.g.: '255 0 0' for a pure red color). If " \
              "ommited, it will default to a white background white (255 255 255)."
    png_group.add_argument(
        '-bg', "--bg-color", type=int, nargs=3, help=bg_help)

    hbg_help = "The background color (in hexadecimal, HTML style) to use when " \
               "doing operations that remove transparency, like reducing colors " \
               "or converting from PNG to JPEG E.g.: '00FF00' for a pure green " \
               "color. If ommited, it will default to a white background white " \
               "(FFFFFF)."
    png_group.add_argument('-hbg', "--hex-bg-color", type=str, help=hbg_help)

    cb_help = "Automatically convert to JPEG format any big PNG images that " \
              "have with a large number of colors (presumably a photo or " \
              "photo-like image). It uses an algorithm to determine whether " \
              "it is a good idea to convert to JPG and automatically decide " \
              "about it. By default, when using this option, the original PNG " \
              "files will remain untouched and will be kept alongside the " \
              "optimized JPG images in their original folders. IMPORTANT: " \
              "IF A JPEG WITH THE SAME NAME ALREADY EXISTS, IT WILL BE " \
              "REPLACED BY THE JPEG FILE RESULTING FROM THIS CONVERTION."
    png_group.add_argument(
        '-cb', "--convert_big", action='store_true', help=cb_help)

    fd_help = "Force the deletion of the original PNG file when using " \
              "automatic convertion to JPEG."
    png_group.add_argument(
        '-fd', "--force-delete", action='store_true', help=fd_help)

    args = parser.parse_args()
    recursive = not args.no_recursion
    quality = args.quality

    if args.supported_formats:
        formats = ', '.join(SUPPORTED_FORMATS).strip().upper()
        msg = "These are the image formats currently supported (please " \
              "note that any files without one of these file extensions " \
              "will be ignored):"
        msg = f"\n{msg} {formats}\n\n"
        parser.exit(status=0, message=msg)

    if args.path:
        src_path = os.path.expanduser(args.path)
    else:
        msg = "\nPlease specify the path of the image or folder to process.\n\n"
        parser.exit(status=0, message=msg)

    if quality > 100 or quality < 1:
        msg = "\nPlease specify an integer quality value between 1 and 100.\n\n"
        parser.exit(status=0, message=msg)

    if args.max_width < 0 or args.max_height < 0:
        msg = "\nPlease specify image dimensions as positive integers.\n\n"
        parser.exit(status=0, message=msg)

    if args.bg_color and args.hex_bg_color:
        msg = "\nBackground color should be entered only once.\n\n"
        parser.exit(status=0, message=msg)
    elif not args.bg_color and not args.hex_bg_color:
        # By default, apply a white background
        bg_color = (255, 255, 255)
    elif args.bg_color:
        bg_color = tuple(args.bg_color)
    else:
        # Check if hexadecimal is in the expected format
        if not re.search(r'(?:[0-9a-fA-F]{3}){1,2}$', args.hex_bg_color):
            msg = "\nHexadecimal background color was not entered in the correct " \
                  "format. Please follow these examples:\n\nWhite: FFFFFF" \
                  "\nBlack: 000000\nPure Red: FF0000\n\n"
            parser.exit(status=0, message=msg)
        # convert hex to a tuple of integers (RGB)
        bg_color = tuple(
            int(args.hex_bg_color[i:i + 2], 16) for i in (0, 2, 4))

    if min(bg_color) < 0 or max(bg_color) > 255:
        msg = "\nBackground color should be entered as a sequence of 3 " \
              "integer numbers between 0 and 255 (values for Red, Green and " \
              "Blue components) separated by spaces. For instance, for a " \
              "bright red you can use: '-bg 255 0 0' or '-hbg #FF0000'.\n\n"
        parser.exit(status=0, message=msg)

    return src_path, recursive, quality, args.reduce_colors, args.max_colors, \
           args.max_width, args.max_height, args.keep_exif, args.convert_big, \
           args.force_delete, bg_color