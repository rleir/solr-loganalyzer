from collections import Counter
import re
import argparse
import sys

LINE_RE = re.compile("INFO:\s+\[(?P<core>\w+)\]\s+webapp=/\w+\s+path=(?P<path>/\w+)\s+params={(?P<search>.*)}\s+status=\w+\s+QTime=(?P<qtime>\w+)")
"""
lines we want:
INFO: [arstechnicacogtree] webapp=/solr path=/mlt params={mlt.count=16&fl=link,title,author,pub_date,thumb_url_medium,metadata,section&start=0&q=link_aliases:http\://arstechnica.com/apple/news/2009/02/the\-case\-of\-the\-app\-store\-ripoff.ars&wt=json&fq=pub_date:[NOW/DAY-14DAYS+TO+NOW/DAY%2B1DAY]&rows=16} status=0 QTime=2
INFO: [places] webapp=/solr path=/select/ params={pf=*&sort=geodist()+asc&fl=*,_dist_:geodist()&q=*&sfield=location&pt=-1.260326940083812,51.759690475011105&wt=json&spellcheck.collate=true&defType=edismax} hits=9830 status=0 QTime=11
"""

class CoreCounter(object):
    def __init__(self,corename):
        self.corename = corename
        self.endpoints = Counter()
        self.urls = Counter()
        self.linesread = 0
        self.qtimes = Counter()
        
    def __repr__(self):
        return "<Core '%s' with %i endpoints %i search urls>" %(self.corename,len(self.endpoints), len(self.urls))

    def timestats(self):
        sqtimes = sorted(self.qtimes.values())
        numitems = len(sqtimes)
        percent_50 = sqtimes[int(numitems / 2)]
        percent_75 = sqtimes[int(numitems * .75)]
        percent_90 = sqtimes[int(numitems * .90)]
        percent_99 = sqtimes[int(numitems * .99)]
        return (("Median", percent_50),
                ("75%", percent_75),
                ("90%", percent_90),
                ("99%", percent_99))

    def _pprint_topn(self,n,counter,title):
        """Print the top N entries of a counter with its title.
        """
        s = "{0}\n{1}\n".format(title, "="*40)
        top = counter.most_common(n)
        for index, item in enumerate(top):
            label, cnt = item
            s += '%i) "%s" %i\n' % (index+1, label, cnt)
        return s

    def pprint_stats(self):
        """Print statistics for a core
        """
        print self._pprint_topn(10, self.endpoints, "Top Endpoints for {0}".format(self.corename))

        print self._pprint_topn(10, self.urls, "Top Search URLs for {0}".format(self.corename))

        print self._pprint_topn(10, self.qtimes, "Slowest Searches for {0}".format(self.corename))

        # qtimes
        print "Search Time for {0}\n{1}\n".format(self.corename, '='*40)
        stats = self.timestats()
        for st in stats:
            print "%s     %s" % (st[0], st[1])
        return ""
    
class StatCounter(object):
    def __init__(self):
        self.corecounters = {}
        
    def process(self,iterinput):
        for line in iterinput:
            matches = LINE_RE.match(line)
            if not matches:
                continue
            core, path, search, qtime = matches.groups()

            corecounter = self.corecounters.get(core,CoreCounter(core))
            corecounter.endpoints[path] += 1
            corecounter.urls[search] += 1
            corecounter.linesread += 1
            corecounter.qtimes[search] = int(qtime)
            
            self.corecounters[core] = corecounter
            
    def allcounterstats(self):
        for cc in self.corecounters.values():
            print cc.pprint_stats()
            print "*"* 100        
            print


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input',
        type = argparse.FileType('r'),
        default = sys.stdin,
        nargs = '?',
        help = "File to parse; will read from stdin otherwise")
    args = parser.parse_args()

    sc = StatCounter()
    sc.process(args.input)
    sc.allcounterstats()
