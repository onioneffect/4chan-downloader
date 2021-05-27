#!/usr/bin/python3

import urllib.request, urllib.error, urllib.parse, argparse, logging
import os, re, time
import http.client 
import fileinput
from multiprocessing import Process

log = logging.getLogger('inb4404')
workpath = os.path.dirname(os.path.realpath(__file__))
args = None

def mlevel_msg():
    cool = [
        "Remove 404'd threads from file",
        "Remove archived threads",
        "Remove archived threads, while backing up file (recommended)"
    ]

    ret = """MLEVEL value:        Behaviour:
"""
    for i, j in enumerate(cool):
        ret += "  {0}                     {1}\n".format(i, j)

    return ret

def main():
    global args
    parser = argparse.ArgumentParser(
        description='Python script to download all images/webms of a 4chan thread',
        epilog=mlevel_msg(),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('thread', nargs=1, help='url of the thread (or filename; one url per line)')
    parser.add_argument('-c', '--with-counter', action='store_true', help='show a counter next the the image that has been downloaded')
    parser.add_argument('-d', '--date', action='store_true', help='show date as well')
    parser.add_argument('-l', '--less', action='store_true', help='show less information (supresses checking messages)')
    parser.add_argument('-m', '--mlevel', action='store', help='define how strictly to manage threads file') # TODO
    parser.add_argument('-n', '--use-names', action='store_true', help='use thread names instead of the thread ids (...4chan.org/board/thread/thread-id/thread-name)')
    parser.add_argument('-q', '--quiet', action='store_true', help='suppress all other logging options, only shows errors')
    parser.add_argument('-o', '--once', action='store_true', help='only check each thread once and quit (supresses --reload)')
    parser.add_argument('-r', '--reload', action='store_true', help='reload the queue file every 5 minutes')
    #TODO: The two options below this line are also not implemented.
    parser.add_argument('-s', '--split', action='store', help='choose substring to separate thread URLs in threads file (default: \\n)')
    parser.add_argument('-t', '--title', action='store_true', help='save files with original filename')
    args = parser.parse_args()

    # TODO: Organize these if statements!
    # Some of them would be better as `elif`s!
    if args.quiet:
        logging.basicConfig(level=logging.ERROR)
        args.less = False
        args.date = False

    if args.once:
        args.reload = False

    if args.title:
        try:
            import bs4
        except ImportError:
            log.warning("BeautifulSoup4 not found! Disabling --title option!")
            args.title = False

    chan_fmt = '%I:%M:%S %p'
    if args.date:
        chan_fmt = '%Y-%m-%d ' + chan_fmt
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt=chan_fmt)

    if args.mlevel:
        log.info('The --mlevel function is still in development, so enabling it has no effect!')

    thread = args.thread[0].strip()
    if thread[:4].lower() == 'http':
        download_thread(thread, args)
    else:
        download_from_file(thread)

def load(url):
    req = urllib.request.Request(url, headers={'User-Agent': '4chan Browser'})
    return urllib.request.urlopen(req).read()

def download_thread(thread_link, args):
    board = thread_link.split('/')[3]
    thread = thread_link.split('/')[5].split('#')[0]
    if len(thread_link.split('/')) > 6:
        thread_tmp = thread_link.split('/')[6].split('#')[0]

        if args.use_names or os.path.exists(os.path.join(workpath, 'downloads', board, thread_tmp)):                
            thread = thread_tmp

    directory = os.path.join(workpath, 'downloads', board, thread)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # TODO: Wrap my head around this loop. :woozy:
    while True:
        if not args.less:
            log.info('Checking ' + board + '/' + thread)

        try:
            page_html = load(thread_link).decode('utf-8')

            regex = '(\/\/i(?:s|)\d*\.(?:4cdn|4chan)\.org\/\w+\/(\d+\.(?:jpg|png|gif|webm)))'
            regex_result = list(set(re.findall(regex, page_html)))
            regex_result = sorted(regex_result, key=lambda tup: tup[1])
            regex_result_len = len(regex_result)            
            regex_result_cnt = 1

            # TODO: Maybe turn this into an enumerate?
            # See line 118
            for link, img in regex_result:
                img_path = os.path.join(directory, img)
                if not os.path.exists(img_path):
                    data = load('https:' + link)

                    output_text = board + '/' + thread + '/' + img
                    if args.with_counter:
                        output_text = '[' + str(regex_result_cnt).rjust(len(str(regex_result_len))) +  '/' + str(regex_result_len) + '] ' + output_text

                    if not args.quiet:
                        log.info(output_text)

                    with open(img_path, 'wb') as f:
                        f.write(data)

                    ##################################################################################
                    # saves new images to a separate directory
                    # if you delete them there, they are not downloaded again
                    # if you delete an image in the 'downloads' directory, it will be downloaded again
                    copy_directory = os.path.join(workpath, 'new', board, thread)
                    if not os.path.exists(copy_directory):
                        os.makedirs(copy_directory)
                    copy_path = os.path.join(copy_directory, img)
                    with open(copy_path, 'wb') as f:
                        f.write(data)
                    ##################################################################################
                regex_result_cnt += 1

            if args.once:
                break

        except urllib.error.HTTPError as err:
            time.sleep(10)
            try:
                resp = load(thread_link)
            except urllib.error.HTTPError as err:
                if err.code == 404:
                    log.info(thread_link + ' 404\'d')
                else:
                    log.error('Something went very wrong! Response code: ' + str(err.code))

                break
            continue
        except (urllib.error.URLError, http.client.BadStatusLine, http.client.IncompleteRead):
            log.error('Something went wrong')

        time.sleep(20)

def download_from_file(filename):
    # TODO: Finish all of this...
    running_links = list()
    split_text = list()
    fptr = open(filename)

    if args.split == None:
        for line in fptr:
            split_text += line
    else:
        split_text = fptr.read().split(args.split)

    while True:
        processes = []
        for link in [_f for _f in [line.strip() for line in open(filename) if line[:4] == 'http'] if _f]:
            if link not in running_links:
                running_links.append(link)
                log.info('Added ' + link)

            process = Process(target=download_thread, args=(link, args, ))
            process.start()
            processes.append([process, link])

        if len(processes) == 0:
            log.warning(filename + ' empty')
        
        if args.reload:
            time.sleep(60 * 5) # 5 minutes
            links_to_remove = []
            # Find out what all this does VVVVVVV
            for process, link in processes:
                if not process.is_alive():
                    links_to_remove.append(link)
                else:
                    process.terminate()

            for link in links_to_remove:
                for line in fileinput.input(filename, inplace=True):
                    print(line.replace(link, '-' + link), end='')
                running_links.remove(link)
                log.info('Removed ' + link)
            if not args.less:
                log.info('Reloading ' + args.thread[0]) # thread = filename here; reloading on next loop
        else:
            break

    fptr.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

