# My Markdown Blog

2016-12-17

Yet another static site generator.

## Quickstart

Requires python 3+.

    cd path/to/src
    source env/bin/activate
    python publish.py source/path/

To run locally:

    cd path/to/live
    python -m SimpleHTTPServer



## To Do

Features:

- [x] Search (Basic)
- [x] Click to open larger images
- [ ] Automatic FTP
- [ ] HTTPS
- [x] Automatically downsize images
- [ ] 

Minor Bug Fixes/Admin:

- [x] Heading duplicated on pages?
- [x] Max image height
- [x] Get working on local server (SimpleHTTPServer)
- [x] <del>Strip img tags from summary</del>Replace imgs with thumbnails
- [x] Get favicon
- [x] Make output folder configurable.
- [ ] Fix character encoding issues.
- [x] Arrange location of 'resources' relative to live path.
- [ ] Delete posts.

Maybe Do:

- [x] Only update new/changed pages.
- [ ] Include videos/music.