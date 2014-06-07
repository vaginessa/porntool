import argparse
import collections as cols
import itertools as it
import logging
import os.path
import random

import sqlalchemy as sql
import urwid

import porntool as pt
from porntool import clippicker
from porntool import controller
from porntool import db
from porntool import filters
from porntool import menu
from porntool import movie
from porntool import player
from porntool import rating
from porntool import reviewer
from porntool import script
from porntool import segment
from porntool import select
from porntool import tables as t
from porntool import util
from porntool import widget
from porntool.replay_porn import *


parser = argparse.ArgumentParser(
    description='Play clips for porn collection', parents=[select.parser, filters.PARSER])
parser.add_argument('files', nargs='*', help='files to play; play entire collection if omitted')
parser.add_argument('--shuffle', default=True, type=util.flexibleBoolean, help='shuffle file list')
parser.add_argument('--no-edit', action='store_true', default=False)
parser.add_argument('--update-library', action='store_true', default=False)
parser.add_argument('--extra', default='')
ARGS = parser.parse_args()


try:
    script.standardSetup()
    logging.info('****** Starting new script ********')

    cmd_line_files = [f.decode('utf-8') for f in ARGS.files]
    if ARGS.update_library:
        filepaths = movie.loadFiles(cmd_line_files, add_movie=movie.addMovie)
    else:
        filepaths = movie.queryFiles(cmd_line_files)
    logging.debug('filepaths: %s', len(filepaths))
    db.getSession().commit()
    logging.debug('%s files loaded', len(filepaths))

    all_filters = [filters.ExcludeTags(['pmv', 'cock.hero', 'compilation'])]
    all_filters.extend(filters.applyArgs(ARGS, db.getSession()))

    inventory = movie.MovieInventory(filepaths, ARGS.shuffle, all_filters)

    iinventory = inventoryFilter(inventory)

    normalratings = rating.NormalRatings(db.getSession())

    PROJECT = t.Project(id_=1, name='redhead')

    segment_tracker = select.getSegmentTrackerType(ARGS)
    clip_type = select.getClipPickerType(ARGS)
    clip_picker = clip_type(iinventory, PROJECT, normalratings, ARGS.nfiles, segment_tracker)

    FILL = widget.Status(valign='bottom')

    # bold is needed for the AdjustController
    palette = [('bold', 'default,bold', 'default', 'bold'),]
    CLIP_PLAYER = ClipPlayer(clip_picker, FILL, PROJECT, ARGS.extra, ARGS.no_edit)
    LOOP = urwid.MainLoop(
        FILL, palette=palette, unhandled_input=CLIP_PLAYER.handleKey, handle_mouse=False)
    CLIP_PLAYER.setLoop(LOOP)

    LOOP.set_alarm_in(1, CLIP_PLAYER.playNextClip)

    LOOP.run()
finally:
    script.standardCleanup()
    CLIP_PLAYER.printSkippedFiles()
    logging.info('****** End of Script *********')
