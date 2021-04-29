#!/usr/bin/env python3

import argparse
import curses
import json
import os
import shutil
import sys
from functools import partial

from tordl import config as cfg, engines, core
from tordl.app import App


def parse_args():
    class ArgParseFormatter(argparse.ArgumentDefaultsHelpFormatter):
        def _get_default_metavar_for_optional(self, action):
            return ''

    ap = argparse.ArgumentParser(
        description='CLI Torrent Downloader provides convenient and quick way '
                    'to search torrent magnet links (and to run associated '
                    'torrent client) via major torrent sites (ThePirateBay, '
                    'LimeTorrents, Zooqle, 1337x, GloTorrents, KickAssTorrents '
                    'by default) through command line.',
        formatter_class=ArgParseFormatter
    )
    ap.add_argument(
        'search',
        nargs='*',
        default='',
        help='Search term. All positional arguments are concatenated to one '
             'string, no need for " "'
    )
    ap.add_argument(
        '-r',
        '--revert-to-default',
        action='store_true',
        default=False,
        help='Purge all custom configuration and revert to default.'
    )
    ap.add_argument(
        '-e',
        '--search-engines',
        dest='cfg_search_engines',
        default=','.join(cfg.SEARCH_ENGINES),
        help='Search engines to be used for torrent search. Overrides the value'
             ' loaded from config in %s' % cfg.CFG_FILE
    )
    ap.add_argument(
        '-c',
        '--torrent-client-cmd',
        dest='cfg_torrent_client_cmd',
        default=cfg.TORRENT_CLIENT_CMD,
        help='Command to execute torrent client with magnet link as a parameter'
    )
    ap.add_argument(
        '-b',
        '--browser-cmd',
        dest='cfg_browser_cmd',
        default=cfg.BROWSER_CMD,
        help='Command to open torrent link in a browser.'
    )
    ap.add_argument(
        '-d',
        '--download',
        action='store_true',
        default=False,
        help='Directly download first search result, don\'t run UI.'
    )
    ap.add_argument(
        '-t',
        '--test-search-engines',
        action='store_true',
        default=False,
        help='Test all active search engines for errors.'
    )
    ap.add_argument(
        '-n',
        '--page-num-download',
        dest='cfg_page_num_download',
        default=cfg.PAGE_NUM_DOWNLOAD,
        type=int,
        help='Fetch N pages of search results from search engines.'
    )
    parsed = ap.parse_args(sys.argv[1:])
    return parsed


def mk_cfg():
    attrs = dir(cfg)
    omit = ['os']
    config = {}
    for a in attrs:
        if not a.startswith('CFG') and not a.startswith('__') and a not in omit:
            config[a.lower()] = getattr(cfg, a)

    return config


def init_cfg():
    if not os.path.exists(cfg.CFG_DIR):
        os.makedirs(cfg.CFG_DIR)

    if not os.path.exists(cfg.CFG_FILE):
        with open(cfg.CFG_FILE, 'w') as f:
            f.write(json.dumps(mk_cfg(), indent=4))

    if not os.path.exists(cfg.CFG_ENGINES_FILE):
        with open(engines.__file__) as f:
            engines_module = f.read()

        with open(cfg.CFG_ENGINES_FILE, 'w') as f:
            f.write(engines_module)

    with open(cfg.CFG_FILE) as f:
        config = json.load(f)

    for k, v in config.items():
        setattr(cfg, k.upper(), v)


def override_cfg(args):
    cfg.SEARCH_ENGINES = args.cfg_search_engines.replace(' ', '').split(',')

    omit = ('cfg_search_engines', 'tordl')
    prefix = 'cfg_'
    for k in args.__dict__:
        if k.startswith(prefix) and k not in omit:
            setattr(cfg, k.upper()[len(prefix):], getattr(args, k))


def run_curses_ui(st):
    os.environ.setdefault('ESCDELAY', '0')
    curses.wrapper(partial(App, search=st))


if __name__ == "__main__":
    parsed_args = parse_args()

    if parsed_args.revert_to_default:
        if os.path.exists(cfg.CFG_DIR):
            shutil.rmtree(cfg.CFG_DIR)
        init_cfg()
        print('Reverted to default config.')
        exit(0)

    init_cfg()
    override_cfg(parsed_args)

    if parsed_args.test_search_engines:
        core.test_search_engines()
        exit(0)

    search_term = ' '.join(parsed_args.search)

    if parsed_args.download:
        core.direct_download(search_term)
    else:
        run_curses_ui(search_term)

    exit(0)
