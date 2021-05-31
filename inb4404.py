#!/usr/bin/python3

import urllib.request, urllib.error, urllib.parse, argparse, logging
import os, re, time
import http.client 
import fileinput
from multiprocessing import Process

log = logging.getLogger('inb4404')
workpath = os.path.dirname(os.path.realpath(__file__))
args = None

# TODO: Make a function that returns only the parsed thread links
# See lines 193-209
# TODO: Make a copy of the file before writing to it! Very important!
def handle_mlevel(thread_index : int, code):
    urls_file = open(args.thread[0], "r")
    all_urls = urls_file.read().split(args.split)
    urls_file.close()

    if code == 0:
        all_urls.pop(thread_index)
    elif code == 3:
        all_urls[thread_index] = '#' + all_urls[thread_index]

    if not args.split:
        joiner = '\n'
    else:
        joiner = args.split

    w_urls_file = open(args.thread[0], "w")
    w_urls_file.write(joiner.join(all_urls))
    w_urls_file.close()

# TODO: Make it possible to combine multiple of these!
# Also make the codes more extensible!
def mlevel_msg():
    cool = [
        "Remove 404'd threads from file",
        "Remove archived threads",
        "Remove duplicate threads",
        "Comment out 404'd threads",
        "Comment out archived threads",
        "Comment out duplicate threads"
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
    parser.add_argument('-m', '--mlevel', action='store', help='define how to manage threads file') # TODO
    parser.add_argument('-n', '--use-names', action='store_true', help='use thread names instead of the thread ids (...4chan.org/board/thread/thread-id/thread-name)')
    parser.add_argument('-q', '--quiet', action='store_true', help='suppress all other logging options, only shows errors')
    parser.add_argument('-o', '--once', action='store_true', help='only check each thread once and quit (supresses --reload)')
    parser.add_argument('-r', '--reload', action='store_true', help='reload the queue file every 5 minutes')
    parser.add_argument('-s', '--split', action='store', help='choose substring to separate thread URLs in threads file (default: \\n)')
    parser.add_argument('-t', '--title', action='store_true', help='save original filenames')
    args = parser.parse_args()

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
    if thread[:4].lower() == 'http' and not os.path.exists(thread):
        download_thread(thread, args)
    else:
        download_from_file(thread)

def load(url):
    req = urllib.request.Request(url, headers={'User-Agent': '4chan Browser'})
    return urllib.request.urlopen(req).read()

def get_title_list(html_content):
    ret = list()

    from bs4 import BeautifulSoup
    parsed = BeautifulSoup(html_content, 'html.parser')
    divs = parsed.find_all("div", {"class": "fileText"})

    for i in divs:
        current_child = i.findChildren("a", recursive = False)[0]
        try:
            ret.append(current_child["title"])
        except KeyError:
            ret.append(current_child.text)

    return ret

def download_thread(thread_link, args, thread_index = None):
    board = thread_link.split('/')[3]
    thread = thread_link.split('/')[5].split('#')[0]
    if len(thread_link.split('/')) > 6:
        thread_tmp = thread_link.split('/')[6].split('#')[0]

        if args.use_names or os.path.exists(os.path.join(workpath, 'downloads', board, thread_tmp)):                
            thread = thread_tmp

    directory = os.path.join(workpath, 'downloads', board, thread)
    if not os.path.exists(directory):
        os.makedirs(directory)

    while True:
        if not args.less:
            log.info('Checking ' + board + '/' + thread)

        try:
            regex = '(\/\/i(?:s|)\d*\.(?:4cdn|4chan)\.org\/\w+\/(\d+\.(?:jpg|png|gif|webm)))'
            html_result = load(thread_link).decode('utf-8')
            regex_result = list(set(re.findall(regex, html_result)))

            regex_result = sorted(regex_result, key=lambda tup: tup[1])
            regex_result_len = len(regex_result)
            regex_result_cnt = 1

            if args.title:
                all_titles = get_title_list(html_result)

            for enum_index, enum_tuple in enumerate(regex_result):
                link, img = enum_tuple

                if args.title:
                    img = all_titles[enum_index]

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
                    
                    if int(args.mlevel) in (0, 3):
                        handle_mlevel(thread_index, int(args.mlevel))
                else:
                    log.error('Something went very wrong! Response code: ' + str(err.code))

                break
            continue
        except (urllib.error.URLError, http.client.BadStatusLine, http.client.IncompleteRead):
            log.error('Something went wrong')

        time.sleep(20)

def download_from_file(filename):
    running_links = list()
    fptr = open(filename)

    # Running .split(None) defaults to splitting on whitespace
    links_generator = fptr.read().split(args.split)

    for link_str in links_generator:
        if len(re.findall('http', link_str)) > 1:
            log.error('Error parsing links from file. Your --split argument may have been misused.')
            log.error('Removing %s...', repr(link_str))
            links_generator.remove(link_str)

    while True:
        processes = []
        for link_ind, link in enumerate([_f for _f in [line.strip() for line in links_generator if line[:4] == 'http'] if _f]):
            if link not in running_links and not link.startswith("#"):
                running_links.append(link)
                log.info('Added ' + link)

            process = Process(target=download_thread, args=(link, args, link_ind))
            process.start()
            processes.append([process, link])

        if len(processes) == 0:
            log.warning(filename + ' empty')
        
        if args.reload:
            time.sleep(60 * 5) # 5 minutes
            links_to_remove = []

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

