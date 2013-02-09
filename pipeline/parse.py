
from elementtree import ElementTree as ET
import hashlib, md5, re, json
from unicodedata import normalize
from datetime import datetime

import config

class Parse(object):

    def __init__(self):
        pass

    def parse(self, xmlin):
        if config.sourcetype == "pmcoa":
            return self._parse_pmcoa_xml(xmlin)
        elif config.sourcetype == "nlm":
            return self._parse_nlm_xml(xmlin)


    def _parse_pmcoa_xml(self,el):
        doc = self._prepdoc()

        try:
            front = el.find("front")
            
            # journal metadata
            try:
                jm = front.find("journal-meta")
                doc["journal"] = {}
                try:
                    jtg = jm.find('journal-title-group')
                    jt = jtg.find('journal-title')
                    doc["journal"]["name"] = jt.text
                except:
                    pass
                try:
                    issns = jm.findall('issn')
                    doc["journal"]["identifier"] = []
                    for issn in issns:
                        doc["journal"]["identifier"].append({"type":issn.attrib['pub-type'],"id":issn.text})
                except:
                    pass
                try:
                    pub = jm.find('publisher')
                    doc["journal"]["publisher"] = pub.find('publisher-name').text
                except:
                    pass
            except:
                pass
            
            # article metadata
            try:
                am = front.find("article-meta")
                try:
                    ids = am.findall('article-id')
                    doc["identifier"] = []
                    for _id in ids:
                        doc["identifier"].append({"type":_id.attrib['pub-id-type'],"id":_id.text})
                except:
                    pass
                try:
                    tg = am.find('title-group')
                    at = tg.find('article-title')
                    doc["title"] = at.text
                except:
                    pass
                try:
                    doc["volume"] = am.find("volume").text
                except:
                    pass
                try:
                    doc["issue"] = am.find("issue").text
                except:
                    pass
                try:
                    doc["pages"] = am.find("fpage").text + '--' + am.find("lpage").text
                except:
                    pass
                try:
                    doc["firstpage"] = am.find("fpage").text
                except:
                    pass
                try:
                    doc["lastpage"] = am.find("lpage").text
                except:
                    pass
                try:
                    pds = am.findall("pub-date")
                    for pd in pds:
                        if pd.attrib['pub-type'] == "pmc-release":
                            try:
                                doc["year"] = pd.find("year").text
                            except:
                                pass
                            try:
                                doc["day"] = pd.find("day").text
                                doc["month"] = pd.find("month").text
                            except:
                                pass
                except:
                    pass
                try:
                    doc["copyright"] = am.find("permissions").find("copyright-statement").text
                except:
                    pass
                try:
                    doc["abstract"] = ET.tostring(am.find("abstract"))
                except:
                    pass

                # keywords
                try:
                    kwg = am.find('kwd-group')
                    kws = kwg.findall('kwd')
                    doc["keyword"] = []
                    for kw in kws:
                        doc["keyword"].append(kw.text)
                except:
                    pass

                # contributors
                try:
                    doc["author"] = []
                    doc["editor"] = []
                    cg = am.find('contrib-group')
                    contribs = cg.findall('contrib')
                    for contrib in contribs:
                        entity = {}
                        try:
                            if contrib.attrib['corresp'] == "yes":
                                entity["corresponding"] = "yes"
                        except:
                            pass
                        try:
                            nm = contrib.find('name')
                            try:
                                entity["name"] = nm.find('surname').text + " " + nm.find('given-names').text
                            except:
                                pass
                            try:
                                entity["lastname"] = nm.find('surname').text
                                entity["firstname"] = nm.find('given-names').text
                            except:
                                pass
                        except:
                            pass
                        try:
                            addr = contrib.find('address')
                            email = addr.find('email')
                            entity["identifier"] = {"type":"email","id":email.text}
                        except:
                            pass
                        try:
                            xrefs = contrib.findall('xref')
                            affs = cg.findall("aff")
                            for xref in xrefs:
                                if xref.attrib['ref-type'] == "aff":
                                    rid = xref.attrib['rid']
                                    for aff in affs:
                                        if aff.attrib["id"] == rid:
                                            if "affiliation" not in entity: entity["affiliation"] = []
                                            entity["affiliation"].append( ET.tostring(aff.find('label')).replace('<label />','') )
                        except:
                            pass
                        if contrib.attrib['contrib-type'] == "author":
                            doc["author"].append(entity)
                        if contrib.attrib['contrib-type'] == "editor":
                            doc["editor"].append(entity)                            
                except:
                    pass

            except:
                pass

        except:
            pass

        '''try:
            body = el.find("body")
            # the entire html of the article is contained in body, if we want to do anything with it
            # could full-text index the entire thing...
        except:
            pass'''

        try:
            back = el.find("back")
            try:
                doc["acknowledgement"] = back.find('ack').find('p').text
            except:
                pass
            try:
                fng = back.find('fn-group')
                fns = fng.findall('fn')
                for fn in fns:
                    if "conflict" not in doc: doc["conflict"] = []
                    doc["conflict"].append(fn.find('p').text)
            except:
                pass

            #citations
            # there is more data in the citation list about the cited object, but we can pull that via 
            # the pmid if we really care about it - it will just be a ref anyway
            try:
                doc["citation"] = []
                reflist = back.find('ref-list')
                refs = reflist.findall('ref')
                for ref in refs:
                    ent = {}
                    try:
                        ent["label"] = ref.find('label').text
                    except:
                        pass
                    try:
                        refinfo = ref.find('mixed-citation')
                        try:
                            ent["title"] = refinfo.find('article-title').text
                        except:
                            pass
                        try:
                            idents = refinfo.findall('pub-id')
                            ent["identifier"] = []
                            for ident in idents:
                             ent["identifier"].append({"type":ident.attrib['pub-id-type'],"id":ident.text})
                        except:
                            pass
                    except:
                        pass
                    doc["citation"].append(ent)
            except:
                pass

        except:
            pass

        doc = self._completedoc(doc)        
        return doc


    #--------------------------------------------------------------------------------#


    def _parse_nlm_xml(self,el):
        # parse the item into a dict, using some pre-defined details if available
        doc = self._prepdoc()

        # look for the PMID
        try:
            if "identifier" not in doc: doc["identifier"] = []
            doc["identifier"].append({"type":"PMID","id":el.find("PMID").text})
        except:
            pass

        # look for any affiliations - not stricyly bibjson, but quite useful
        try:
            doc["affiliation"] = el.find("Affiliation").text
        except:
            pass

        # look for any keywords
        try:
            keywordlist = el.find("KeywordList")
            doc["keyword"] = []
            for keyword in keywordlist:
                doc["keyword"].append(keyword.text)
        except:
            pass

        # look for grant info - not strictly bibjson but may be useful
        try:
            grantlist = el.find("GrantList")
            doc["grant"] = []
            for grant in grantlist:
                doc["grant"].append({"agency":grant.find("Agency").text})
        except:
            pass

        # get the citations
        if config.include_citations:
            try:
                comments = el.find("CommentsCorrectionsList")
                doc["citation"] = []
                for comment in comments:
                    doc["citation"].append({
                        "identifier":[
                            {
                                "description":comment.find("RefSource").text,
                                "type": "PMID",
                                "id":comment.find("PMID").text
                            }
                        ]
                    })
            except:
                pass

        # identify the article object and set the title and language
        try:
            article = el.find("Article")
            doc["title"] = article.find("ArticleTitle").text
            doc["language"] = article.find("Language").text
        except:
            pass
        
        # look for abstracts if allowed
        if config.include_abstracts:
            # look for a generic record abstract
            try:
                otherabstract = el.find("OtherAbstract")
                doc["abstract"] = otherabstract.find("AbstractText").text
            except:
                pass

            # see if there is a specific article abstract
            try:
                abstract = article.find("Abstract")
                if abstract:
                    for item in abstract:
                        try:
                            doc["abstract"] = abstract.find("AbstractText").text
                        except:
                            pass
                        try:
                            doc["license"] = [{"description":abstract.find("CopyrightInformation").text}]
                        except:
                            pass
            except:
                pass
        
        # look for DOI
        try:
            doi = article.find("ELocationID")
            if doi.attrib["EIdType"] == "doi":
                if "identifier" not in doc: doc["identifier"] = []
                doc["identifier"].append({"type":"DOI","id":doi.text})
        except:
            pass
        
        # look for author list
        try:
            authorlist = article.find("AuthorList")
            doc["author"] = []
            for author in authorlist:
                lastname = author.find("LastName").text
                firstname = author.find("ForeName").text
                initials = author.find("Initials").text
                doc["author"].append({
                    "name": lastname + " " + firstname,
                    "lastname":lastname,
                    "firstname":firstname
                })
        except:
            pass

        # look for journal information
        try:
            journal = article.find("Journal")
            doc["journal"] = {
                "name":journal.find("Title").text,
                "identifier":[
                    {
                        "type": "issn",
                        "id": journal.find("ISSN").text
                    },
                    {
                        "type": "iso",
                        "id": journal.find("ISOAbbreviation").text
                    }
                ]
            }
            try:
                journalissue = journal.find("JournalIssue")
                doc["journal"]["volume"] = journalissue.find("Volume").text
            except:
                pass
            try:
                journalpubdate = journalissue.find("PubDate")
                doc["journal"]["year"] = journalpubdate.find("Year").text
                doc["journal"]["month"] = journalpubdate.find("Month").text
            except:
                pass
        except:
            pass
                    
        # look for dates
        try:
            articledate = article.find("ArticleDate")
            doc["year"] = articledate.find("Year").text
            doc["month"] = articledate.find("Month").text
            doc["day"] = articledate.find("Day").text
        except:
            pass
        
        # give this record an _id and subsequently a URL and bibsoup identifier then return it
        doc = self._completedoc(doc)        
        return doc


    #--------------------------------------------------------------------------------#


    # This is a copy of the bibserver DAO record ID maker, found on line 172 of that file
    # you could also just import it instead of having it specified explicitly here
    def _makeid(self, data):
        id_data = {
            'author': [i.get('name','') for i in data.get('author',[])],
            'title': data.get('title',''),
            'identifier': [i.get('id','') for i in data.get('identifier',[]) if i.get('type','').lower() != "bibsoup"]
        }
        if id_data['author'] is not None: id_data['author'].sort() # these must be done after the comprehensions above or they give null
        if id_data['identifier'] is not None: id_data['identifier'].sort()
        buf = self._slugify(json.dumps(id_data, sort_keys=True).replace('author:','').replace('title:','').replace('identifier:','').replace('null','').decode('unicode-escape'),delim=u'')
        new_id = hashlib.md5(buf).hexdigest()
        return new_id

    # also copied from bibserver code, from the UTIL, for use in the make ID function
    def _slugify(self, text, delim=u'_'):
        _punct_re = re.compile(r'[\t !"$%&\'()*\-/<=>?@\[\\\]^`{|},.]+')
        result = []
        for word in _punct_re.split(text.lower()):
            word = normalize('NFKD', word).encode('ascii', 'ignore')
            if word:
                result.append(word)
        return unicode(delim.join(result))


    # provide a starting bibjson record
    def _prepdoc(self):
        return {
            '_collection': [config.bibjson_creator + '_____' + config.bibjson_collname],
            '_created': datetime.now().strftime("%Y-%m-%d %H%M"),
            '_created_by': config.bibjson_creator
        }


    # complete a bibjson record
    def _completedoc(self,doc):
        doc['_id'] = self._makeid(doc)
        if "identifier" not in doc: doc["identifier"] = []
        doc["url"] = config.bibjson_url + doc["_id"]
        doc["identifier"].append({"type":"bibsoup","id":doc["_id"],"url":doc["url"]})
        return doc


# run this directly if required
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="location of file to parse")
    parser.add_argument("outfile", help="location of file to output to")
    args = parser.parse_args()

    tree = ET.parse(args.infile)
    e = tree.getroot()

    p = Parse()
    d = p.parse(e)

    out = open(args.outfile,'w')
    out.write(json.dumps(d,indent=4))
    out.close()






