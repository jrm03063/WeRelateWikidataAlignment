import sys
import string
import time
import re

reload(sys)
sys.setdefaultencoding('utf8')
from HTMLParser import HTMLParser

class MyParser(HTMLParser):
    "A simple parser class."

    def parse(self, s):
        "Parse the given string 's'."
        self.feed(s)
        self.close()
        return self.object

    def __init__(self, verbose=0):
        "Initialise an object, passing 'verbose' to the superclass."
        self.object = None
        self.last_attr_tab = None

        HTMLParser.__init__(self)
        self.hyperlinks = []

    def handle_starttag(self, tag, attrs) :
      if (not self.object) :
        self.object = {}

      attrtab = {}
      self.last_attr_tab = attrtab
      for (attr_name, attr_val) in attrs :
        attrtab[attr_name] = attr_val

      if (not self.object.has_key(tag)) :
        self.object[tag] = []

      self.object[tag].append(attrtab)

    def handle_data(self, data) :
      "Process data."

      if (self.last_attr_tab != None) :
        if (not self.last_attr_tab.has_key("data")) :
          self.last_attr_tab["data"] = []

        self.last_attr_tab["data"].append(data)
      # else :
      #   sys.stderr.write("Dropping data: %s\n" % data)

import urllib, sgmllib

def getPage(name, retry=0) :
  url = "http://www.werelate.org/wiki/" + name.replace(" ", "_") + "?action=raw"
  # print "ENTRY TO GETPAGE(%s)" % (name)
  sys.stdout.flush()
  try:
    f = urllib.urlopen(url)
    s = f.read()

  except :
    if (retry < 10) :
      # print "RETRY FOR " + name
      sys.stdout.flush()
      time.sleep(10)
      return getPage(name, retry + 1)
    else :
      sys.stderr.write("I/O error on getPage(%s) open - %d retries\n" % (name, retry))
      return None

  
  if ((s != None) and (s != "")) :
    # print "============ %s ==============" % (name)
    # print s
    # print "=============================="
    myparser = MyParser()
    try:
      pobj = myparser.parse(s.decode('utf-8', 'ignore'))
    except:
      pobj = None
  else:
    if (retry < 10) :
      # print "RETRY FOR " + name
      sys.stdout.flush()
      # time.sleep(5 * (retry + 1))
      time.sleep(10)
      return getPage(name, retry + 1)
    else :
      sys.stderr.write("I/O error on getPage(%s) read - %d retries\n" % (name, retry))
      return None

  # pobj["url"] = [name]
  return pobj

def getPerson(name, retry=0) :
  url = "http://www.werelate.org/wiki/Person:" + name.replace(" ", "_") + "?action=raw"
  # print "ENTRY TO GETPAGE(%s)" % (name)
  sys.stdout.flush()
  try:
    f = urllib.urlopen(url)
    s = f.readlines()

    person_section = []
    collecting_person = False
    for line in s :
      if collecting_person :
        person_section.append(line)
        if (line.find("</person>") >= 0) :
          break
      else :
        if (line.find("<person>") >= 0) :
          collecting_person = True
          person_section.append(line)

  except :
    if (retry < 3) :
      # print "RETRY FOR " + name
      sys.stdout.flush()
      time.sleep(5)
      return getPage(name, retry + 1)
    else :
      sys.stderr.write("I/O error on getPage(%s)\n" % (name))
      return None

  # print "len(person_section) = %d" % (len(person_section))
  if (len(person_section) > 0) :
    # print "============ %s ==============" % (name)
    person_stuff = "".join(person_section)
    # print person_stuff
    # print "=============================="
    myparser = MyParser()
    # try:
    pobj = myparser.parse(person_stuff)
    # print "Parse yields " + str(pobj)
    # except:
    #   pobj = None
  else:
    if (retry < 3) :
      # print "RETRY FOR " + name
      sys.stdout.flush()
      time.sleep(5)
      return getPerson(name, retry + 1)
    else :
      sys.stderr.write("I/O error on getPage(%s)\n" % (name))
      return None

  # pobj["url"] = [name]
  return pobj


def getWpPage(name) :
  urlname = name.replace(" ", "_")
  f = urllib.urlopen("http://en.wikipedia.org/wiki/" + urlname)
  print "urlname: {%s}" % urlname
  s = f.read()
  print "s = %s" % (s)
  return s

  if (s) :
    # print s
    myparser = MyParser()
    try:
      pobj = myparser.parse(s)
    except:
      pobj = None
  else:
    print "S NULL!!!!"
    pobj = None
  # pobj["url"] = [name]
  print "%s" % (str(pobj))
  return pobj


def getWikidataList(start, rows) :
  # url = "http://www.werelate.org/wiki/Special:Search?ns=Family&ecp=c&rows=" + str(rows) + "&cv=true&watch=wu&k=%2BTree%3A%22Jrm03063%2FDefault%22&start=" + str(start)
  url= "http://www.werelate.org/wiki/Special:Search?ns=Person&ecp=c&rows=" + str(rows) + "&watch=wu&k=Wikidata"

  if (start > 0):
    url = url + "&start=" + str(start)

  # url = url + "?action=raw"
  url = url + "&ecp=c"

  f = urllib.urlopen(url)
  s = f.read()

  name = "wikidataList/wikidataList%d:%d" % (start, rows)

  if (s) :
    # Save what we read for later review...
    fp = open(name, "w")
    fp.write(s)
    fp.close()
    prefix_string = '<a href="/wiki/Person:'
    person_strings = re.compile(prefix_string + '.+%29" ')
    results = person_strings.findall(s)
    flist = []
    for item in results :
      stripped_item = item[len(prefix_string):-2]
      xlated_item = stripped_item.replace("%28", "(").replace("%29", ")").replace("%2C", ",")
      flist.append(xlated_item)

  else :
    print "S NULL!!!!"
    flist = None

  return flist


def getWikidataIds(pageName) :
  wikidata_search = re.compile(r'\{\{[Ww]ikidata\|Q[0-9]+\}\}')
  rawPage = str(getPage(pageName))

  if (rawPage == None) :
    return []

  wikidata_ids = []
  rawString = str(rawPage)
  for matchObj in wikidata_search.finditer(rawString) :
    wikidata_ids.append(rawString[matchObj.start() + len("{{Wikidata|"):matchObj.end() - len("}}")])

    # wp_url = "https://en.wikipedia.org/wiki/" + matchStr[len("{{Wikipedia-notice|"):-2]

    # print "MATCH: " + str(matchObj)
    # if matchStr :
    #   return matchStr[len("{{Wikidata|"):-2]
    # else :
    #   return None
  return wikidata_ids



def getFullWikidataList() :
  total_list = []
  offset = 0
  chunk = 200
  # WORK-WORK-WORK
  flist = getWikidataList(offset, chunk)
  # return flist

  while (len(flist) > 0) :
    fflist = []
    for item in flist :
      total_list.append(item)

    offset = offset + chunk
    flist = getWikidataList(offset, chunk)

  return total_list



def getCohabitationWithoutFormalities(start, rows) :
  # url= "http://www.werelate.org/wiki/Special:Search?ns=Person&ecp=c&rows=" + str(rows) + "&watch=wu&k=Wikidata"
  url = "http://www.werelate.org/wiki/Special:Search?ns=Family&ecp=c&rows=" + str(rows) + "&watch=wu&k=CohabitationWithoutFormalities"

  if (start > 0):
    url = url + "&start=" + str(start)

  # url = url + "?action=raw"
  url = url + "&ecp=c"

  f = urllib.urlopen(url)
  s = f.read()

  name = "wikidataList/wikidataList%d:%d" % (start, rows)

  if (s) :
    # Save what we read for later review...
    fp = open(name, "w")
    fp.write(s)
    fp.close()
    prefix_string = '<a href="/wiki/Family:'
    person_strings = re.compile(prefix_string + '.+%29" ')
    results = person_strings.findall(s)
    flist = []
    for item in results :
      stripped_item = item[len(prefix_string):-2]
      xlated_item = stripped_item.replace("%28", "(").replace("%29", ")").replace("%2C", ",")
      flist.append(xlated_item)

  else :
    print "S NULL!!!!"
    flist = None

  return flist


def getFullCohabitationWithoutFormalitiesList() :
  total_list = []
  offset = 0
  # WORK-WORK-WORK
  chunk = 200
  # chunk = 100
  flist = getCohabitationWithoutFormalities(offset, chunk)
  # return flist

  while (len(flist) > 0) :
    offset = offset + chunk
    total_list = total_list + flist
    flist = getCohabitationWithoutFormalities(offset, chunk)

  return total_list


def getWikipediaNoticeAndNotWikidata(start, rows) :
  # url = "http://www.werelate.org/wiki/Special:Search?ns=Family&ecp=c&rows=" + str(rows) + "&cv=true&watch=wu&k=%2BTree%3A%22Jrm03063%2FDefault%22&start=" + str(start)
  # url2 = http://www.werelate.org/wiki/Special:Search?sort=score&ns=Person&watch=wu&a=&st=&g=&s=&p=&bd=&br=0&bp=&dd=&dr=0&dp=&fg=&fs=&mg=&ms=&sg=&ss=&hg=&hs=&wg=&ws=&md=&mr=0&mp=&pn=&li=&su=&sa=&t=&k=Wikidata&rows=200&ecp=c
  url= "http://www.werelate.org/wiki/Special:Search?ns=Person&ecp=c&rows=" + str(rows) + "&watch=wu&k=%2Bwikipedia-notice+-Wikidata"

  if (start > 0):
    url = url + "&start=" + str(start)

  # url = url + "?action=raw"
  url = url + "&ecp=c"

  f = urllib.urlopen(url)
  s = f.read()

  if (s) :
    # print s
    # href="/wiki/Person:John_FitzAlan_%2873%29"
    person_strings = re.compile(r'"/wiki/Person:.+\"')
    results = person_strings.findall(s)
    flist = []
    # print "Requested %d rows, got %d" % (rows, len(results))
    for item in results :
      stripped_item = item[len("./wiki/Person:"):]
      open_pindex = stripped_item.find("%28")
      # print "open_pindex: " + str(open_pindex)
      close_pindex = stripped_item.find("%29", open_pindex)
      # print "close_pindex: " + str(close_pindex)
      index_str = stripped_item[open_pindex+3:close_pindex]
      name = stripped_item[:open_pindex]
      flist.append(name + "(" + index_str + ")")
      # print str(item)

    # myparser = MyParser()
    # try:
    #   flist = myparser.parse(s)
    # except:
    #   flist = None
  else :
    print "S NULL!!!!"
    flist = None

  return flist


def getWhatLinksHere(name) :
  # Get something to work with.
  # f = urllib.urlopen("http://www.python.org")
  # f = urllib.urlopen("http://www.werelate.org/wiki/Person:James_Mason_%2813%29?action=raw")
  # f = urllib.urlopen("http://www.werelate.org/wiki/Person:Charlemagne_%281%29?action=raw")
  # name = "Person:Charlemagne (1)"
  specialUrl =  ("http://www.werelate.org/w/index.php?title=Special:Whatlinkshere&target=%s" % name)
  specialUrl =  ("http://www.werelate.org/w/index.php?title=Special:Whatlinkshere/Page %s?action=raw" % name)

  # "?action=raw" 
  # specialUrl += "&limit=10000&from=5000"
  specialUrl += ""

  urlname = specialUrl.replace(" ", "_")
  f = urllib.urlopen(urlname)
  # f = urllib.urlopen("http://www.werelate.org/wiki/Family:Charlemagne_and_Luitgard,_wife_of_Charlemagne_(1)?action=raw")
  # print "urlname: {%s}" % urlname
  s = f.read()
  
  if (s) :
    print str(s)
    myparser = MyParser()
    try:
      pobj = myparser.parse(s)
    except:
      pobj = None
  else:
    print "S NULL!!!!"
    pobj = None
  # pobj["url"] = [name]
  return pobj


def dumpPage(pobj) :
  for key in pobj.keys() :
    print "\n"
    val = pobj[key]
    print "%s:" % key
    for v in val :
      print "  %s" % v


def getFamily(name) :
  return getPage("Family:" + name)


def getWikipediaPage(item) :
  wikipedia_notice = re.compile(r'\{\{[Ww]ikipedia.notice\|[^}]+\}\}')
  personPage = str(getPerson(item))
  # print "(((( " + personPage + "))))"
  matchObj = wikipedia_notice.search(str(getPerson(item)))
  if matchObj :
    matchStr = matchObj.group(0)
    wp_url = "https://en.wikipedia.org/wiki/" + matchStr[len("{{Wikipedia-notice|"):-2]

    print "URL: " + wp_url
    # print "MATCH: " + str(matchObj)
    return

def getWikidataNumber(pobj) :
  wikidata_search = re.compile(r'\{\{[Ww]ikidata\|Q[0-9]+\}\}')
  matchObj = wikidata_search.search(str(pobj))
  if matchObj :
    matchStr = matchObj.group(0)
    # wp_url = "https://en.wikipedia.org/wiki/" + matchStr[len("{{Wikipedia-notice|"):-2]
    
    # print "MATCH: " + str(matchObj)
    if matchStr :
      return matchStr[len("{{Wikidata|"):-2]
    else :
      return None
  else :
    return None


class family_connections :
  # Overloads are presumed to provide implementations and values
  # for the following:
  def __init__(self) :
    self.name = None
    self.marriage = None
    self.fathers = []
    self.mothers = []
    self.children = []

  def __str__(self) :
    return str("Father: %s; Mother: %s; Children: %s - %s" % (str(self.fathers), str(self.mothers), str(self.children), str(self.name)))

  def any_relations(self) :
    return (len(self.fathers) + len(self.mothers) + len(self.children)) > 1

  def married(self) :
    if (self.marriage == None) :
      # sys.stderr.write("Checking if %s married or cohabitation\n" % (self.name))
      if unmarried.has_key(self.name) :
        self.marriage = False
        # sys.stdout.write("Found\n")
      else :
        self.marriage = True
        # sys.stdout.write("Not Found\n")

    return self.marriage


xgenders = []
people_by_name = {}
people_by_qnumber = {}
families_by_name = {}
wikidata_table = {}
duplicates = []
families = {}

class wrPerson :
  def process_page(self) :
    if (not people_by_qnumber.has_key(self.qnumber())) :
      if (not skip_table.has_key(self.qnumber())) :
        # sys.stderr.write("DEBUG: Establishing this person at QNUMBER %s\n" % (self.qnumber()))
        people_by_qnumber[self.qnumber()] = self
      else :
        sys.stderr.write("DEBUG: Skipping add of page %s for %s to people_by_qnumber()\n" % (self.name, self.qnumber()))
        return
    else :
      duplicates.append(people_by_qnumber[self.qnumber()])
      duplicates.append(self)
      return

    if (not people_by_name.has_key(pageName)) :
      people_by_name[pageName] = self

    for family_name in self.child_of_family() :
      if (not families_by_name.has_key(family_name)) :
        families_by_name[family_name] = family_connections()
        families_by_name[family_name].name = family_name
      families_by_name[family_name].children.append(self.qnumber())

    if self.gender() in ["M", "F"] :
      for family_name in self.spouse_of_family() :
        if (not families_by_name.has_key(family_name)) :
          families_by_name[family_name] = family_connections()
          families_by_name[family_name].name = family_name
        if (self.gender() == "M") :
          families_by_name[family_name].fathers.append(self.qnumber())
        else :
          families_by_name[family_name].mothers.append(self.qnumber())
    else :
      xgenders.append(self)


  def __init__(self, pageName) :
    self.name = pageName
    self.page = getPerson(pageName)
    self.m_qnumber = None
    self.m_fathers = []
    self.m_mothers = []
    self.m_siblings = []
    self.m_spouses = []
    self.m_partners = []
    self.m_children = []
    self.process_page()

  def spouse_of_family(self) :
    if self.page.has_key("spouse_of_family") :
      names = []
      for name in self.page["spouse_of_family"] :
        if name.has_key("title") :
          names.append(name["title"])
      return names
    else :
      return []

  def child_of_family(self) :
    if self.page.has_key("child_of_family") :
      names = []
      for name in self.page["child_of_family"] :
        if name.has_key("title") :
          names.append(name["title"])
      return names
    else :
      return []

  def gender(self) :
    if self.page.has_key("gender") :
      return str(self.page["gender"][0]["data"][0])

    return None

  def name(self) :
    return self.name

  def qnumber(self) :
    if (self.m_qnumber == None) :
      self.m_qnumber = getWikidataNumber(self.page)
    return self.m_qnumber

pagesWOLinks = 0
siteLinkTable = {}
def getWikidataEntity(id) :
  # sys.stderr.write("DEBUG: Entry to getWikidataEntity...\n")
  global siteLinkTable

  def dump_dict(indent, item) :
    for key in item.keys() :
      print indent + "Key: %s" % (key)
      dump_item(indent + "  ", item[key])

  def dump_list(indent, items) :
    print indent + "List:"
    for item in items :
      dump_item(indent + "  ", item)

  def dump_str(indent, item) :
    print indent + "Str: " + str(item)

  def dump_unicode(indent, item) :
    print indent + "Unicode: " + str(item.encode('ascii', 'ignore'))

  def dump_item(indent, item) :
    if (type(item) == type({})) :
      dump_dict(indent, item)
    elif (type(item) == type("")) :
      dump_str(indent, item)
    elif (type(item) == type([])) :
      dump_list(indent, item)
    elif (type(item) == type(u'a')) :
      dump_unicode(indent, item)
    else :
      return indent + "Type: %s" + str(type(item))

  # sys.stderr.write("DEBUG: Further in getWikidataEntity...\n")
  import json
  # sys.stderr.write("DEBUG: Imported json\n")
  url = "http://www.wikidata.org/wiki/Special:EntityData/" + id + ".json"
  f = urllib.urlopen(url)
  jobj = json.load(f)
  # if (jobj != None) :
  #   sys.stderr.write("DEBUG: json_load() yields Non-None!\n")
  # else :
  #   sys.stderr.write("DEBUG: json_load() yields None\n")

  # dump_item("", jobj)
  # jstuff = jobj[id]
  result = None
  human = False
  gender = None
  newWdPerson = None
  # sys.stderr.write("DEBUG: Checking if object has entities...\n")
  if jobj.has_key("entities") :
    # sys.stderr.write("DEBUG: Object has entities...\n")
    entities = jobj["entities"]
    if entities.has_key(id) :
      # sys.stderr.write("DEBUG: entities has key %s" % (str(id)))
      entity = entities[id]

      if (entity.has_key("sitelinks")) :
        sitekeys = entity["sitelinks"].keys()
      else :
        sitekeys = []

      # sys.stderr.write("DEBUG: len(sitekeys) = %d\n" % (len(sitekeys)))

      if (len(sitekeys) == 0) :
        # sys.stderr.write("DEBUG: empty sitekeys list?\n")
        pagesWOLinks = pagesWOLinks + 1

      else :
        # sys.stderr.write("DEBUG: looping over list of sitekeys\n")
        for siteKey in sitekeys :
          if not siteLinkTable.has_key(siteKey) :
            siteLinkTable[siteKey] = 0
          siteLinkTable[siteKey] = siteLinkTable[siteKey] + 1

      def collect_claim(entity, property) :
        # sys.stderr.write("DEBUG: collect claim: entity.keys() = %s\n" % (str(entity.keys())))
        # try:
        #   if (entity.has_key("sitelinks")) :
        #     # sys.stderr.write("DEBUG: Has a key for sitelinks!\n")
        #     stuff = entity["sitelinks"]
        #     # sys.stderr.write("DEBUG: SITELINKS {%s}\n" % (str(stuff)))
        #     # sys.stderr.write("DEBUG: KEYS {%s}\n" % (str(stuff.keys())))
        #     # sys.stderr.write("DEBUG: SITELINKS.....\n" % (str(type(stuff))))
        #     # for skey in stuff.keys() :
        #     #   sys.stderr.write("DEBUG:   %s: %s\n" % (skey, str(stuff[skey])))
        #     # sys.stderr.write("\n")
        # except:
        #   sys.stderr.write("DEBUG:   Oops...\n")
        #   sys.exit(0)

        if (entity.has_key("claims")) :
          claims = entity["claims"]
          if (type(claims) != type({})) :
            return None

        results = []
        if claims.has_key(property) :
          instances_of = claims[property]
          for inst in instances_of :
            if (inst.has_key("mainsnak")) :
              mainsnak = inst["mainsnak"]
              if (mainsnak.has_key("datavalue")) :
                dvalue = mainsnak["datavalue"]
                if (dvalue.has_key("value")) :
                  value = dvalue["value"]
                  if (value.has_key("id")) :
                    results.append(value["id"].encode('ascii', 'ignore'))

        return results

      class wdPerson :
        def __init__(self) :
          self.name = None
          self.page = None
          self.m_qnumber = None
          self.m_genders = []
          self.m_fathers = []
          self.m_mothers = []
          self.m_siblings = []
          self.m_spouses = []
          self.m_partners = []
          self.m_children = []

      # sys.stderr.write("About to obtain a wdPerson object!\n")
      newWdPerson = wdPerson()
      # sys.stderr.write("Obtained newWdPerson object %s\n" % (str(newWdPerson)))
      newWdPerson.m_qnumber = id
      newWdPerson.m_genders = collect_claim(entity, "P21")
      newWdPerson.m_fathers = collect_claim(entity, "P22")
      newWdPerson.m_mothers = collect_claim(entity, "P25")
      newWdPerson.m_siblings = collect_claim(entity, "P3373")
      newWdPerson.m_spouses = collect_claim(entity, "P26")
      newWdPerson.m_partners = collect_claim(entity, "P451")
      newWdPerson.m_children = collect_claim(entity, "P40")
      # sys.stderr.write("After obtaining various entities, newWdPerson object %s\n" % (str(newWdPerson)))
    # else :
    #   sys.stderr.write("DEBUG: entities does not have key\n")
    # sys.stderr.write("Finishing with newWdPerson = %s\n" % (str(newWdPerson)))
  # else :
  #   sys.stderr.write("DEBUG: Object does not have entities...\n")
  # sys.stderr.write("Finishing with newWdPerson = %s\n" % (str(newWdPerson)))

  return newWdPerson


#
#
# MAIN LINE START
#
#

sys.stderr.write("STARTING MAIN LINE!\n")

unmarried = {}
unmarried_list = getFullCohabitationWithoutFormalitiesList()
sys.stderr.write("UNMARRIED LIST LENGTH: %d\n" % (len(unmarried_list)))
for item in unmarried_list :
  ritem = item.replace("_", " ")
  # sys.stderr.write("DEBUG: Cohabitation Item - {%s}\n" % (ritem))
  unmarried[ritem] = ritem

skip_list = getWikidataIds("User:Jrm03063/Wikimedia Alignment Project - IDs to Skip")
sys.stderr.write("SKIP LIST LENGTH: %d\n" % (len(skip_list)))
skip_table = {}
for item in skip_list :
  skip_table[item] = item

# sys.stdout.write("Skip Table = %s" % (str(skip_table)))



total_list = getFullWikidataList()
sys.stderr.write("FULL WIKIDATA LIST LENGTH: %d\n" % (len(total_list)))

# limit = 100

for pageName in total_list :
  new_person = wrPerson(pageName)
  sys.stdout.write("%s: (%s)\n" % (str(new_person.name), str(new_person.qnumber())))
  # limit = limit - 1
  # if (limit <= 0) :
  #   break

print "FULL WIKIDATA LIST REVIEWED"
# WORK-WORK-WORK - Stop here for now

for obj in xgenders :
  print "Unknown Gender: %s" % (obj.name)

for obj in duplicates :
  print "Duplicate: %s" % (obj.name)

sys.stdout.flush()

sys.stderr.write("ABOUT TO CREATE RELATIONSHIP LIST FROM FAMILIES_BY_NAME (len of keys = %d)\n" % (len(families_by_name.keys())))

# Create list of people for whom there is a relationship of some kind...
relation_people = {}
for fname in families_by_name.keys() :
  family = families_by_name[fname]
  if family.any_relations() :
    all_relations = family.fathers + family.mothers + family.children

    for qnumber in all_relations :
      relation_people[qnumber] = True

sys.stderr.write("ABOUT TO REVIEW RELATIONSHIP_PEOPLE (len of keys = %d)\n" % (len(people_by_qnumber.keys())))
consistent = {}

# for qnumber in relation_people.keys() :
# Now, walk list of all people by qnumber...
for qnumber in people_by_qnumber.keys() :
  # sys.stderr.write("DEBUG: qnumber = %s\n" % (qnumber))
  wrPerson = people_by_qnumber[qnumber]
  # sys.stderr.write("DEBUG: wrPerson.name = %s\n" % (wrPerson.name))
  all_children = []
  all_siblings = []
  all_spouses = []
  all_partners = []
  all_fathers = []
  all_mothers = []

  # sys.stderr.write("DEBUG: Processing families for %s\n" % (qnumber))
  for mfamily in wrPerson.spouse_of_family() :
    family_obj = families_by_name[mfamily]
    all_children = all_children + family_obj.children
    if family_obj.married() :
      # sys.stderr.write("DEBUG: SPOUSE FOUND, %s, for family %s (%s)\n" % (qnumber, str(family_obj.name), str(mfamily)))
      all_spouses = all_spouses + family_obj.fathers + family_obj.mothers
      # sys.stderr.write("DEBUG: all_spouses = %s\n" % (str(all_spouses)))
    else :
      # sys.stderr.write("DEBUG: UNMARRIED PARTNER FOUND, %s, for family %s (%s)\n" % (qnumber, str(family_obj.name), str(mfamily)))
      all_partners = all_partners + family_obj.fathers + family_obj.mothers
      # sys.stderr.write("DEBUG: all_partners = %s\n" % (str(all_partners)))

  # sys.stderr.write("DEBUG: Processing parents for %s\n" % (qnumber))
  for mfamily in wrPerson.child_of_family() :
    family_obj = families_by_name[mfamily]
    all_siblings = all_siblings + family_obj.children
    all_fathers = all_fathers + family_obj.fathers
    all_mothers = all_mothers + family_obj.mothers

  if (len(all_fathers) > 0) :
    for fqnumber in all_fathers :
      # print "  Father: %s" % (fqnumber)
      fqPerson = people_by_qnumber[fqnumber]
      for fqFamily in fqPerson.spouse_of_family() :
        all_siblings = all_siblings + families_by_name[fqFamily].children

  if (len(all_mothers) > 0) :
    for mqnumber in all_mothers :
      # print "  Mother: %s" % (mqnumber)
      mqPerson = people_by_qnumber[mqnumber]
      for mqFamily in mqPerson.spouse_of_family() :
        all_siblings = all_siblings + families_by_name[mqFamily].children

  unique_children = {}
  unique_siblings = {}
  unique_spouses = {}
  unique_partners = {}
  unique_fathers = {}
  unique_mothers = {}

  for child in all_children :
    unique_children[child] = True

  for sibling in all_siblings :
    if (sibling != qnumber) :
      unique_siblings[sibling] = True

  for spouse in all_spouses :
    if (spouse != qnumber) :
      unique_spouses[spouse] = True

  for partner in all_partners :
    if (partner != qnumber) :
      unique_partners[partner] = True

  for mother in all_mothers :
    unique_mothers[mother] = True

  for father in all_fathers :
    unique_fathers[father] = True

  wrPerson.m_fathers = list(unique_fathers.keys())
  wrPerson.m_mothers = list(unique_mothers.keys())
  wrPerson.m_siblings = list(unique_siblings.keys())
  wrPerson.m_spouses = list(unique_spouses.keys())
  wrPerson.m_partners = list(unique_partners.keys())
  wrPerson.m_children = list(unique_children.keys())
  # sys.stderr.write("DEBUG: wrPerson.m_fathers = %s\n" % (wrPerson.m_fathers))
  # sys.stderr.write("DEBUG: wrPerson.m_mothers = %s\n" % (wrPerson.m_mothers))
  # sys.stderr.write("DEBUG: wrPerson.m_siblings = %s\n" % (wrPerson.m_siblings))
  # sys.stderr.write("DEBUG: wrPerson.m_spouses = %s\n" % (wrPerson.m_spouses))
  # sys.stderr.write("DEBUG: wrPerson.m_partners = %s\n" % (wrPerson.m_partners))
  # sys.stderr.write("DEBUG: wrPerson.m_children = %s\n" % (wrPerson.m_children))
  # sys.stdout.write("DEBUG: family %s\n" % (str(mfamily)))
  # sys.stderr.write("DEBUG: FOR %s, SPOUSES,            %s\n" % (qnumber, str(wrPerson.m_spouses)))
  # sys.stderr.write("DEBUG: FOR %s, UNMARRIED PARTNERS, %s\n" % (qnumber, str(wrPerson.m_partners)))

sys.stderr.write("DONE INITIAL WORK THROUGH TRELATIONSHIP_PEOPLE\n")

consistent_count = 0
wr_count = 0
wd_count = 0
wrd_count = 0

# Open various output files
# consistent_both = open("consistent.log", "w")
# missing_both = open("missing_both.log", "w")
# missing_from_wr = open("missing_from_wr.log", "w")
# missing_from_wd = open("missing_from_wd.log", "w")
consistent_both = sys.stdout
missing_both = sys.stdout
missing_from_wr = sys.stdout
missing_from_wd = sys.stdout

wd_inconsistent_ids = {}

consistent_claims = 0
wr_claims = 0
wd_claims = 0

# for qnumber in relation_people.keys() :
sys.stderr.write("ABOUT TO WALK LIST OF PEOPLE BY QNUMBER (len(keys) = %d)\n" % (len(people_by_qnumber.keys())))
# Now, walk list of all people by qnumber...
for qnumber in people_by_qnumber.keys() :
  # sys.stderr.write("QNUMBER %s\n" % (str(qnumber)))
  wrPerson = people_by_qnumber[qnumber]

  try:
    wdPerson = getWikidataEntity(qnumber)
    # sys.stderr.write("DEBUG: wdPerson = %s" % (str(wdPerson)))
    label_line = ("{{WdProject|%s}} [[Person:%s]]" % (qnumber, wrPerson.name))
  except:
    wdPerson = None

  if (wdPerson == None) :
    # sys.stderr.write("wdPerson yields None!\n")
    continue
  # sys.stderr.write("wdPerson non-null...\n")

  # if wdPerson == None :
  #   print "FAILED READ FOR %s WAITING TO RETRY..." % (qnumber)
  #   time.sleep(10)

  #   try:
  #     wdPerson = getWikidataEntity(qnumber)
  #     label_line = ("{{WdProject|%s}} [[Person:%s]]" % (qnumber, wrPerson.name))
  #   except:
  #     wdPerson = None

  #   if wdPerson == None :
  #     print "STILL FAILED READ FOR %s" % (qnumber)
  #     continue


  def compare_ids(wr_ids, wd_ids) :
    ids = {}

    if (wr_ids != None) :
      for id in wr_ids :
        ids[id] = 1

    if (wd_ids != None) :
      for id in wd_ids :
        if (ids.has_key(id)) :
          ids[id] = 0
        else :
          ids[id] = 2

    consistent = []
    wr_only = []
    wd_only = []
    for key in ids.keys() :
      if (ids[key] == 0) :
        consistent.append(key)
      elif (ids[key] == 1) :
        if (not skip_table.has_key(key)) :
          wr_only.append(key)
      else :
        if (not skip_table.has_key(key)) :
          wd_only.append(key)

    return((consistent, wr_only, wd_only))


  def xlate_ids(ids) :
    xlated_items = []
    for id in ids :
      xlated_items.append("{{WdProject|" + id + "}}")

    return " ".join(xlated_items)


  def display_comparison(label, wrlist, wdlist) :
    consistent = 1
    (consistent_list, wrlist, wdlist) = compare_ids(wrlist, wdlist)
    info = []
    # if (len(consistent_list) > 0) :
    #   info.append("both = " + str(consistent_list))

    if (len(wrlist) > 0) :
      info.append("wr = { " + xlate_ids(wrlist) + " }")
      consistent = 0
    
    if (len(wdlist) > 0) :
      for id in wdlist :
        if (not wd_inconsistent_ids.has_key(id)) :
          wd_inconsistent_ids[id] = 1
        else :
          wd_inconsistent_ids[id] = wd_inconsistent_ids[id] + 1

      info.append("wd = { " + xlate_ids(wdlist) + " }")
      consistent = 0

    dstr = (": %s: %s" % (label, ", ".join(info)))
    return (len(wrlist), len(wdlist),  dstr)

  # sys.stderr.write("Location A\n")
  # Display father info consistency
  (fwr, fwd, fstr) = display_comparison("father", wrPerson.m_fathers, wdPerson.m_fathers)
  (consistent_list, frlist, fdlist) = compare_ids(wrPerson.m_fathers, wdPerson.m_fathers)
  consistent_claims = consistent_claims + len(consistent_list)
  wr_claims = wr_claims + fwr
  wd_claims = wd_claims + fwd

  # sys.stderr.write("Location B\n")
  # Display mother info consistency
  (mwr, mwd, mstr) = display_comparison("mother", wrPerson.m_mothers, wdPerson.m_mothers)
  (consistent_list, mrlist, mdlist) = compare_ids(wrPerson.m_mothers, wdPerson.m_mothers)
  consistent_claims = consistent_claims + len(consistent_list)
  wr_claims = wr_claims + mwr
  wd_claims = wd_claims + mwd

  # sys.stderr.write("Location C\n")
  # Display spouse info consistency
  (spr, spd, spstr) = display_comparison("spouse", wrPerson.m_spouses, wdPerson.m_spouses)
  (consistent_list, srlist, sdlist) = compare_ids(wrPerson.m_spouses, wdPerson.m_spouses)
  consistent_claims = consistent_claims + len(consistent_list)
  wr_claims = wr_claims + spr
  wd_claims = wd_claims + spd

  # sys.stderr.write("Location D\n")
  # Display partner info consistency
  (par, pad, pastr) = display_comparison("unmarried partner", wrPerson.m_partners, wdPerson.m_partners)
  (consistent_list, prlist, pdlist) = compare_ids(wrPerson.m_partners, wdPerson.m_partners)
  consistent_claims = consistent_claims + len(consistent_list)
  wr_claims = wr_claims + par
  wd_claims = wd_claims + pad

  # # sys.stderr.write("Location E\n")
  # # Display sibling info consistency
  # (sbr, sbd, sbstr) = display_comparison("sibling", wrPerson.m_siblings, wdPerson.m_siblings)
  # (consistent_list, sirlist, sidlist) = compare_ids(wrPerson.m_siblings, wdPerson.m_siblings)
  # consistent_claims = consistent_claims + len(consistent_list)
  # wr_claims = wr_claims + sbr
  # wd_claims = wd_claims + sbd
  sbr = 0
  sbd = 0

  # sys.stderr.write("Location F\n")
  # Display child info consistency
  (chr, chd, chstr) = display_comparison("child", wrPerson.m_children, wdPerson.m_children)
  (consistent_list, crlist, cdlist) = compare_ids(wrPerson.m_children, wdPerson.m_children)
  consistent_claims = consistent_claims + len(consistent_list)
  wr_claims = wr_claims + chr
  wd_claims = wd_claims + chd

  r_total = fwr + mwr + spr + par + sbr + chr
  d_total = fwd + mwd + spd + pad + sbd + chd
  rr_total = fwr + mwr + spr + par
  dd_total = fwd + mwd + spd + pad

  # sys.stderr.write("Location G\n")
  # consistent_count = fcount + mcount + spcount + pacount + sbcount + chcount
  # consistent_open = open("consistent.log", "w")
  # missing_both = open("missing_both.log", "w")
  # missing_from_wr = open("missing_from_wr.log", "w")
  missing_from_wd = open("wd_claims.txt", "w")
  output_fp = sys.stdout

  # if (dd_total > 0) :
  #   output_fp = sys.stdout

  # sys.stderr.write("Location H\n")

  if ((r_total > 0) and (d_total > 0)):
    wrd_count = wrd_count + 1
    # output_fp = missing_both

  elif ((r_total > 0) and (d_total == 0)) :
    def make_claims(person_id, property_id, claim_targets) :
      for claim_id in claim_targets :
        missing_from_wd.write("\t" + property_id + "\t" + claim_id + "\n")

    wr_count = wr_count + 1

    if ((fwr + fwd) > 0) :
      make_claims(qnumber, "P22", frlist)

    if ((mwr + mwd) > 0) :
      make_claims(qnumber, "P25", mrlist)

    if ((spr + spd) > 0) :
      make_claims(qnumber, "P26", srlist)

    if ((par + pad) > 0) :
      make_claims(qnumber, "P451", prlist)

    if ((sbr + sbd) > 0) :
      make_claims(qnumber, "P3373", sirlist)

    if ((chr + chd) > 0) :
      make_claims(qnumber, "P40", crlist)
    # # print ""
  elif (d_total > 0) :
    # output_fp = missing_from_wr
    wd_count = wd_count + 1
  else :
    output_fp = None
    consistent_count = consistent_count + 1

  # sys.stderr.write("Location I\n")
  if (output_fp == None) :
    continue

  # sys.stderr.write("Location J\n")
  output_fp.write(label_line + "\n")

  if ((fwr + fwd) > 0) :
    output_fp.write(fstr + "\n")

  if ((mwr + mwd) > 0) :
    output_fp.write(mstr + "\n")

  if ((spr + spd) > 0) :
    output_fp.write(spstr + "\n")

  if ((par + pad) > 0) :
    output_fp.write(pastr + "\n")

  if ((sbr + sbd) > 0) :
    output_fp.write(sbstr + "\n")

  if ((chr + chd) > 0) :
    output_fp.write(chstr + "\n")

  output_fp.write("\n")
  # sys.stderr.write("Location K\n")

print "\n"
print "\n"
print "CONSISTENCY REPORT:"
print "Consistent:  %d" % (consistent_count)
print "WR inconsistent: %d" % (wr_count)
print "WD inconsistent: %d" % (wd_count)
print "Both inconsistent: %d" % (wrd_count)
print "IDs in found in new places on WD: %d" % (len(wd_inconsistent_ids.keys()))
print "Consistent claims: %d" % (consistent_claims)
print "Additional WR claims: %d" % (wr_claims)
print "Additional WD claims: %d" % (wd_claims)
print "Total claims: %d" % (consistent_claims + wr_claims + wd_claims)
print "Sitelink Totals:"
print "  pages w/o site links: %d" % (pagesWOLinks)
for siteKey in siteLinkTable.keys() :
  print "  %s: %d" % (siteKey, siteLinkTable[siteKey])
print "\n"
print "\n"

wd_id_appearances = []
for key in wd_inconsistent_ids.keys() :
  wd_id_appearances.append((wd_inconsistent_ids[key], key))
wd_id_appearances.sort(reverse=True)
print "IDs appearing in WD connections, but not present equivalent WR connections"
for (count, id) in wd_id_appearances :
  if (people_by_qnumber.has_key(id)) :
    print "%s %d <- ALREADY IN WR!" % (id, count)
  else :
    print "%s %d" % (id, count)
print ""
print ""

# Now, walk list of people with relations...
blobs = []
done_qnumbers = {}
pending_qnumbers = {}
pending_list = []
import collections

def collect_person(qnumber, blob) :
  if (done_qnumbers.has_key(qnumber)) :
    return

  print "Collecting " + qnumber
  wrPerson = people_by_qnumber[qnumber]
  pending_qnumbers[qnumber] = True
  done_qnumbers[qnumber] = True
  blob[qnumber] = True

  for rnumber in wrPerson.m_fathers + wrPerson.m_mothers + wrPerson.m_siblings + wrPerson.m_spouses + wrPerson.m_partners + wrPerson.m_children :
    if not done_qnumbers.has_key(rnumber) and not pending_qnumbers.has_key(rnumber) :
      pending_qnumbers[rnumber] = True
      pending_list.append(rnumber)


for qnumber in relation_people.keys() :
  if (done_qnumbers.has_key(qnumber)) :
    continue

  blob = {}
  blobs.append(blob)
  print "Creating New Collection"
  collect_person(qnumber, blob)

  while (len(pending_list) > 0) :
    collect_person(pending_list.pop(), blob)

blob_list = []
for blob in blobs:
  blob_list.append((len(blob.keys()), blob))

blob_list.sort(reverse=True)

blob_total = 0
for index in range(len(blob_list)) :
  (size, blob) = blob_list[index]
  blob_total = blob_total + size
  print "Blob %d contains %d\n" % (index, len(blob.keys()))
  for key in blob.keys() :
    print "  %s %s" % (key, people_by_qnumber[key].name)
  print ""

print "Total Blob Content: %d" % (blob_total)
print "Total relation people: %d" % (len(relation_people.keys()))
print "Total people : %d" % (len(total_list))

# sys.exit(0)

#   # print "ITEM(%s)" % (item)
#   # dumpPage(personPage) 
#   getWikipediaPage(item)
connections = {}
# print "\FAMILIES:"
for fam in families.keys() :
  if ((len(families[fam].spouses) + len(families[fam].partners) + len(families[fam].children)) >= 2) :
    # print "%s: spouses %s  ; children %s" % (fam, str(families[fam].spouses), str(families[fam].children))
    for parent in (families[fam].spouses + families[fam].partners) :
      if not connections.has_key(parent) :
        connections[parent] = {}
      connections[parent][fam] = True

    for child in families[fam].children :
      if not connections.has_key(child) :
        connections[child] = {}
      connections[child][fam] = True

print "\CONNECTIONS:"
for person in connections.keys() :
  print "%s: %s" % (person, str(connections[person].keys()))

# print "\PEOPLE:"
# for per in people.keys() :
#   pobj = people[per]
#   print "%s (%s): parents: %s ; children: %s" % (pobj.person, pobj.qnumber, str(pobj.parents), str(pobj.children))

print "\nDUPLICATES:"
for item in duplicates :
  print str(item)


