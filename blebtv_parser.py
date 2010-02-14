#!/usr/bin/python

import xml.sax.handler, time, string, re

class Programme:
    def __init__(self):
        self.title = ""
        self.desc = ""
        self.start = ""
        self.end = ""
        self.infourl = ""
        self.year = ""
        self.type = ""
        self.ignore = 0

class Channel:
    def __init__(self):
        self.name = ""
        self.date = ""
        self.valid = 0
        self.programmes = []
      
class ParseChannel(xml.sax.handler.ContentHandler):
    def __init__(self, now):
        self.list_pos = 0
        self.in_desc = 0
        self.in_title = 0
        self.in_start = 0
        self.in_end = 0
        self.in_infourl = 0
        self.in_year = 0
        self.in_type = 0
        self.prog_ignore = 0
        self.now = now
        self.time = time.mktime((self.now[0],self.now[1],self.now[2],
                                self.now[3],self.now[4],0,0,0,0))
  
    def startElement(self, name, attrs):
        if name == "channel":
            self.chan = Channel()
            try:
                self.chan.name = attrs.getValue("id")
                chan_date = attrs.getValue("date")
                tmp = string.split(chan_date, "/")
                self.day = int(tmp[0])
                self.month = int(tmp[1])
                self.year = int(tmp[2])
                self.chan.valid = 1
            except KeyError:
                self.chan.valid = 0
        elif name == "programme":
            self.prog = Programme()
        elif name == "desc":
            self.in_desc = 1
        elif name == "title": 
            self.in_title = 1
        elif name == "start":
            self.in_start = 1
        elif name == "end":
            self.in_end = 1
        elif name == "infourl":
            self.in_infourl = 1
        elif name == "year":
            self.in_year = 1
        elif name == "type":
            self.in_type = 1
  
    def characters(self, data):
        if self.in_title:
            self.prog.title += data
        elif self.in_start:
            self.prog.start = self.format_time(data)
        elif self.in_end:
            self.prog.end = self.format_time(data)
        elif self.in_desc:
            self.prog.desc += data
        elif self.in_infourl:
            self.prog.infourl += data
        elif self.in_year:
            self.prog.year += data
        elif self.in_type:
            self.prog.type += data

    def endElement(self, name):
        #if name == "channel":
        #    self.chan = []
        if name == "programme":
            if self.prog.end != "":
                (hour,min) = map(int,string.split(self.prog.end, ":"))
                
                # between midnight and 6am is a new day
                if hour >= 0 and hour < 6:
                    day = self.day + 1
                else:
                    day = self.day
        
                ptime = time.mktime((self.year,self.month,day,hour,min,0,0,0,0))
                if self.time > ptime:
                    self.prog_ignore = 1
            if not self.prog_ignore:
                self.chan.programmes.append(self.prog)
            self.prog_ignore = 0
        elif name == "desc":
            self.in_desc = 0
        elif name == "title": 
            self.in_title = 0
        elif name == "start":
            self.in_start = 0
        elif name == "end":
            self.in_end = 0
        elif name == "infourl":
            self.in_infourl = 0
        elif name == "year":
            self.in_year = 0
        elif name == "type":
            self.in_type = 0

    def format_time(self, time):
        time_len = len(time);
        # midnight
        if time_len == 1:
            if int(time) == 0:
                time = "0000"
            else: # midnight + minute
                time = "000" + time
        # midnight + minutes
        elif time_len == 2:
            time = "00" + time
        # mornings
        elif time_len == 3:
            time = "0" + time
   
        t4 = re.compile("(\d)(\d)(\d)(\d)")
        time = t4.sub("\g<1>\g<2>:\g<3>\g<4>", time)
   
        return time

class channel_parser:
    def __init__(self, now):
        self.parser = xml.sax.make_parser()
        self.handler = ParseChannel(now)
        self.parser.setContentHandler(self.handler)

    def parse(self, xml_file):
        self.parser.parse(xml_file)
        return self.handler.chan
