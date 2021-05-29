4chan-downloader
================

Python script to download all images/webms of a 4chan thread

### Download Script ###

The main script is called inb4404.py and can be called like this: `python inb4404.py [thread/filename]`

```
usage: inb4404.py [-h] [-c] [-d] [-l] [-m MLEVEL] [-n] [-q] [-o] [-r]
                  [-s SPLIT]
                  thread

Python script to download all images/webms of a 4chan thread

positional arguments:
  thread              url of the thread (or filename; one url per line)

optional arguments:
  -h, --help            show this help message and exit
  -c, --with-counter    show a counter next the the image that has been
                        downloaded
  -d, --date            show date as well
  -l, --less            show less information (supresses checking messages)
  -m MLEVEL, --mlevel MLEVEL
                        define how strictly to manage threads file (TODO)
  -n, --use-names       use thread names instead of the thread ids
                        (...4chan.org/board/thread/thread-id/thread-name)
  -q, --quiet           suppress all other logging options, only shows errors
  -o, --once            only check each thread once and quit (supresses
                        --reload)
  -r, --reload          reload the queue file every 5 minutes
  -s SPLIT, --split SPLIT
                        choose substring to separate thread URLs in threads
                        file. (default: \n)
  -t, --title           save original filenames

MLEVEL value:        Behaviour:
  0                     Remove 404'd threads from file
  1                     Remove archived threads
  2                     Remove archived threads, while backing up file (recommended)
```

You can parse a file instead of a thread url. In this file you can put as many links as you want, you just have to make sure that there's one url per line. A line is considered to be a url if the first 4 letters of the line start with 'http'.

If you use the --use-names argument, the thread name is used to name the respective thread directory instead of the thread id.

### Thread Watcher ###

This is a work-in-progress script but basic functionality is already given. If you call the script like

`python thread-watcher.py -b vg -q mhg -f queue.txt -n "Monster Hunter"`

then it looks for all threads that include `mhg` inside the `vg` board, stores the thread url into `queue.txt` and adds `/Monster-Hunter` at the end of the url so that you can use the --use-names argument from the actual download script.

### Legacy ###

The current scripts are written in python3, in case you still use python2 you can use an old version of the script inside the legacy directory.

### Changes ###

This copy of the program includes many changes made by [onioneffect](https://github.com/onioneffect) on github, including the `-mqos` options and some minor changes in the program's logic. Some of these features are still in development and may not work very well!

