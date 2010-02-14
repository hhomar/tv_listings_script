#!/usr/bin/python

import os, sys, string, time, urllib, re, glob, blebtv_parser

CONFIG_DIR = os.environ.get("HOME") + "/.tv_listings/"
RECORDINGS_DIR = CONFIG_DIR + "recordings/"
CONFIG_FILE = "listings"
LISTING_PREFIX = ".xml"
DOWNLOADED_DATA = CONFIG_DIR + "data/"
# day the file(s) was downloaded
WEEKDAY_FILE = CONFIG_DIR + "weekday"
MAP_CHANNELS_FILE = "map_channels"

class Config:
    def __init__(self):
        if not os.path.exists(CONFIG_DIR):
            os.mkdir(CONFIG_DIR)
            os.mkdir(RECORDINGS_DIR)
            os.mkdir(DOWNLOADED_DATA)
        try:
            w = open(CONFIG_DIR + CONFIG_FILE)  
        except IOError:
            print "No configuration file found. Please create a a file " \
            " called \"listings\" in " + CONFIG_DIR + " with the name of " \
            " the file being downloaded (minus the extension). " \
            "One line per listing"
            sys.exit(1)
    
        # might need better error handling
        # but this is good enough for now
        self.channels = string.split(w.read())
        w.close()
        self.outputfile = CONFIG_DIR + "tv_listings.html"

class MapChannels:
    def __init__(self):
        try:
            w = open(CONFIG_DIR + MAP_CHANNELS_FILE)
        except IOError:
            print "Without a channel mapping, it's unlikely mplayer will" \
            " be able to record from the correct channel"
            return
        
        self.mappings = {}
        for line in w.readlines():
            line = string.split(line, ' = ')
            self.mappings[line[0]] = line[1].rstrip('\n')
        w.close()

# FIXME: should this be moved into a seperate file
class HTMLOutput:
  def __init__(self, file):
    self.html = open(file, "w")
    self.html.write("<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\">\n")
    self.html.write("<html>\n")
    self.html.write("<head>\n")
    self.html.write("<meta http-equiv=\"Content-Type\" content=\"text/HTML; charset=iso-8859-1\">\n")
    self.html.write("<meta http-equiv=\"Refresh\" content=\"3600\">\n");
    self.write_css()
    self.html.write("<title>TV Listings</title>\n")
    self.html.write("</head>\n")
    self.html.write("<body>\n")
    self.html.write("<table>\n")
    self.html.write("<tr>\n")
    
  def end(self):
    self.html.write("</tr>\n")
    self.html.write("</table>\n")
    self.html.write("</body>\n</html>\n")

    self.html.close()
  
  def new_channel(self, name):
    self.html.write("<td valign=\"top\">\n")
    self.html.write("<table>\n")
    self.html.write("<tr><th>" + name + "</th></tr>\n")
   
  def end_channel(self):
    self.html.write("</table>\n")
    self.html.write("</td>\n")

  def programme(self, prog):
    if prog.type == "Film":
      prog_type = "film"
      spc = re.compile(" ")
      title = spc.sub("%20",prog.title)
      amp = re.compile("&")
      title = amp.sub("amp",prog.title)
      prog.infourl = "http://uk.imdb.com/Tsearch?title=" + title + "&type=substring"
      if prog.year:
        prog.year = "(" + prog.year + ")"
    else:
      prog_type = "prog"
 
    if prog.end == "":
      time = prog.start 
    else:
      time = prog.start + "-" + prog.end
   
    self.html.write("<tr><td class=\"" + prog_type + "\">\n")
    self.html.write("<span class=\"time\">" + time + "</span><br>\n")
    try:
      self.html.write("<a title=\"" + prog.desc + "\" href=\"" + prog.infourl + "\">" + prog.title + "</a>\n")
    except UnicodeError:
      prog.title = prog.title.encode('ascii', 'replace')
      prog.desc = prog.desc.encode('ascii', 'replace')
      self.html.write("<a title=\"" + prog.desc + "\" href=\"" + prog.infourl + "\">" + prog.title + "</a>\n")
    
    self.html.write(prog.year)
    self.html.write("</td></tr>\n")

  def write_css(self):
    self.html.write("<style type=\"text/css\">\n")
    self.html.write("body { background-color: #000000; }\n")
    self.html.write("a:link { color: #00ff00; }\n")
    self.html.write("a:visited { color: #aaaaaa; }\n")
    self.html.write("a:active { color: #0000ff; }\n")
    self.html.write("div.channel { float: left; }\n")
    self.html.write("table { font-size: 12px; }\n")
    self.html.write("th { background-color: #00ff00; }\n")
    self.html.write("td.prog { border: 1px solid #00ff00; }\n")
    self.html.write("td.film { background-color: #dd0000; border: 1px solid #00ff00; }\n")
    self.html.write("span.time { font-weight: bold; color: #ffffff; }\n")
    self.html.write("</style>\n")

def main():
    # read config file
    cfg = Config()
   
    # delete old listings if necessary
    now = time.localtime()
    cur_time = float(time.mktime(now))
    try: 
        w = open(WEEKDAY_FILE)
        update_time = float(w.read())
        w.close()
        if cur_time >= update_time:
            files = glob.glob(DOWNLOADED_DATA + "*.xml")
            for file in files:
                os.remove(file)
            w = open(WEEKDAY_FILE, "w+")
            w.write(str(time.mktime((now[0],now[1],now[2]+1,06,10,0,0,0,0))))
            w.close()
    except IOError:
        w = open(WEEKDAY_FILE, "w")
        update_time = time.mktime((now[0],now[1],now[2],06,10,0,0,0,0))
        if cur_time >= update_time:
            update_time = time.mktime((now[0],now[1],now[2]+1,06,10,0,0,0,0))
        w.write(str(update_time)) 
        w.close()

    # Rules For Using This Data 
    # 1. A gap of at least 2 seconds must separate each file fetch. 
    # There are other users of the server, remember.
    # 2. The user agent of the script downloading the data should contain, 
    # at a minimum, the application name and author email address. 
    urllib.URLopener.version = "TV Listings Script/0.2 - hhomar@gmail.com"
    dld_channels = []
    for chan in cfg.channels:
        chan_ext = chan + LISTING_PREFIX
        chan_ext_and_dir = DOWNLOADED_DATA + chan_ext
        try:
            chl = open(chan_ext_and_dir)
            chl.close()
            dld_channels.append(chan)
        except IOError:
            try:
                print "downloading " + chan + " listing"
                (filename, info) = urllib.urlretrieve(
                        "http://www.bleb.org/tv/data/listings/0/" + chan_ext,
                        chan_ext_and_dir)
            except IOError, err:
                print "Unable to download file: " + str(err)
                sys.exit(1)
      
            # FIXME: is it safe to assume that any file type that isn't
            # "application/xml" is going to be a bad file
            if (info.gettype() == "application/xml"):
                dld_channels.append(chan)

            time.sleep(2)
    
    channels = []
    chan_data  = blebtv_parser.channel_parser(now)
    # parse channel files
    for chan in dld_channels:
        data_loc = DOWNLOADED_DATA + chan + LISTING_PREFIX
        parsed_channel = chan_data.parse(data_loc)
        if parsed_channel.valid:
            channels.append(parsed_channel)
   
    args = sys.argv[1:]
    if "-s" in args or "--schedule" in args:
#        map_chan = MapChannels()
#        i = j = 1
#        for channel in channels:
#            print str(i) + ": " + channel.name
#            i = i+1
#        print str(i) + ": Quit"
#        sys.stdout.write("Select a channel: ")
#        chan_no = int(sys.stdin.readline().strip())
#        if i == chan_no: 
#            sys.exit(0)
#        for prog in channels[chan_no-1].programmes:
#            print str(j) + ": " + prog.title
#            j = j+1
#        print str(j) + ": Return to previous menu"
#        sys.stdout.write("Programme to record: ")
#        prog_no = int(sys.stdin.readline().strip())
#        if j == prog_no:
#            print "back to main menu"
#        else:
#            chan_name = map_chan.mappings[channels[chan_no-1].name]
#            prog = channels[chan_no-1].programmes[prog_no-1]
#            print "start: " + prog.start
#            print "end: " + prog.end
#            prog_name = prog.title
#            
#            # write_recording(chan_name, prog_name)
#            print "Recording \"" + prog_name + "\" from channel \"" + \
#            chan_name + "\""
        start = "2340"
        end = "2341"
        start_hour = int(start[0] + start[1])
        start_min = int(start[2] + start[3])
        end_hour = int(end[0] + end[1])
        end_min = int(end[2] + end[3])
        stime = time.mktime((0,0,0,start_hour,start_min,0,0,0,0))
        etime = time.mktime((0,0,0,end_hour,end_min,0,0,0,0))
        duration = str(int(etime - stime))
        
        schedule_recording("BBC ONE Wales", "Breakfast", duration, start)
    else:
        # print listings
        out = HTMLOutput(cfg.outputfile)
        for channel in channels:
            out.new_channel(channel.name)
            for prog in channel.programmes:
                out.programme(prog)
            out.end_channel()
        out.end()

    return 0

def schedule_recording(chan_name, prog_name, duration, start):
            #"OVERLAP=300\nDURATION=" + duration + "\n" + \
    script = "#!/bin/bash\n" + \
            "MPLAYER=\"/usr/bin/mplayer\"\n" + \
            "MPLAYER_ARGS=\"-really-quiet -framedrop -vf dvbscale " \
            "-dumpstream\"\n" + \
            "OVERLAP=0\nDURATION=" + duration + "\n" + \
            "$MPLAYER $MPLAYER_ARGS " \
            "-dumpfile " + RECORDINGS_DIR + "\"" + prog_name + "\".ts " \
            "dvb://\"" + chan_name + \
            "\" & \nMPLAYERPROCESS=$!\n" + \
            "let PROGDURATION=$DURATION+$OVERLAP\n" + \
            "S=$PROGDURATION\"s\"\nsleep $S\nkill $MPLAYERPROCESS\n"
        
    script_file = open(RECORDINGS_DIR + prog_name, "w")
    script_file.write(script)
    script_file.close()

    os.system("at " + start + " < " + RECORDINGS_DIR + prog_name)

if __name__ == "__main__":
    sys.exit(main())
