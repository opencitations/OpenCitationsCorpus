#!/usr/bin/env python
# encoding: utf-8
"""
MetadataReaders.py

Created by Martyn Whitwell on 2013-02-08.
Based on PubMedCentral Parser by Mark MacGillivray

Parses PubMed Central Front Matter (PMC-FM) and arXiv metadata

"""

from oaipmh import common
from lxml import etree

import re


import logging
logging.basicConfig(filename='importer.log',level=logging.DEBUG)

#logger = logging.getLogger('importer')
#hdlr = logging.FileHandler('importer.log')
#formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
#hdlr.setFormatter(formatter)
#logger.addHandler(hdlr) 
#logger.setLevel(logging.DEBUG)


class MetadataReaderAbstract(object):
    """Metadata reader abstract class containing methods for use in derived classes.
    """

    _namespaces={
        'oai': 'http://www.openarchives.org/OAI/2.0/',
        'nlmaa': 'http://dtd.nlm.nih.gov/2.0/xsd/archivearticle',
        'arXiv': 'http://arxiv.org/OAI/arXiv/',
        'xlink': 'http://www.w3.org/1999/xlink',
        'mml' : 'http://www.w3.org/1998/Math/MathML',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

    #METADATA_FORMAT_OAI_DC = {"prefix": 'oai_dc', "reader": oai_dc_reader}
    #METADATA_FORMAT_ARXIV = {"prefix": 'arXiv', "reader": MetadataReaders.MetadataReaderArXiv()}
    #METADATA_FORMAT_PMC_FM = {"prefix": 'pmc_fm', "reader": MetadataReaders.MetadataReaderPMC()}
    #METADATA_FORMAT_PMC = {"prefix": 'pmc', "reader": MetadataReaders.MetadataReaderPMC()}

    def __init__(self):
        pass


    #Find methods ----------------
    def _find_element(self, current_element, xpath):
        if current_element is not None:
            return current_element.find(xpath, self._namespaces)
        else:
            return None

    def _find_element_xml(self, current_element, xpath):
        sought_element = self._find_element(current_element, xpath)
        if sought_element is not None:
            return etree.tostring(sought_element)
        else:
            return None


    #REPLACE WITH FINDTEXT()??
    def _find_element_text(self, current_element, xpath):
        sought_element = self._find_element(current_element, xpath)
        if sought_element is not None and hasattr(sought_element,'text') and sought_element.text is not None:
            return sought_element.text
        else:
            return None

    def _find_elements(self, current_element, xpath):
        if current_element is not None:
            return current_element.findall(xpath, self._namespaces)
        else:
            return [] #return empty list


    #Set methods ----------------
    def _set_map_with_element_text(self, map, key, current_element, xpath):
        value = self._find_element_text(current_element, xpath)
        if value is not None:
            map[key] = value
            return True
        else:
            return False

    def _set_map_with_element_xml(self, map, key, current_element, xpath):
        value = self._find_element_xml(current_element, xpath)
        if value is not None:
            map[key] = value
            return True
        else:
            return False





class MetadataReaderArXiv(MetadataReaderAbstract):
    """A metadata reader for arXiv.
    """

    def __call__(self, metadata_element):
        map = { 'identifier':[], 'journal':{}, 'author':[] }

        arXiv = self._find_element(metadata_element, "arXiv:arXiv")
        arXiv_id = self._find_element_text(arXiv, "arXiv:id")
        doi = self._find_element_text(arXiv, "arXiv:doi")
        
        if arXiv_id is not None:
            map["identifier"].append({'type':'arXiv', 'id':arXiv_id, 'canonical':'arXiv:' + arXiv_id})

        if doi is not None:
            map["identifier"].append({'type':'doi', 'id':doi, 'canonical':'doi:' + doi})

        #title
        self._set_map_with_element_text(map, "title", arXiv, "arXiv:title")

        #copyright ?
        #license
        self._set_map_with_element_text(map, "license", arXiv, "arXiv:license")
        
        #abstract
        self._set_map_with_element_text(map, "abstract", arXiv, "arXiv:abstract")

        #journal
        self._set_map_with_element_text(map['journal'], "reference", arXiv, "arXiv:journal-ref")
        self._set_map_with_element_text(map['journal'], "comments", arXiv, "arXiv:comments")
        self._set_map_with_element_text(map['journal'], "categories", arXiv, "arXiv:categories")


        #authors
        for author in self._find_elements(arXiv,"arXiv:authors/arXiv:author"):
            entity = {}
            self._set_map_with_element_text(entity, "lastname", author, "arXiv:keyname")
            self._set_map_with_element_text(entity, "forenames", author, "arXiv:forenames") #MW: Changed firstname to forenames. Discuss with Mark.
            self._set_map_with_element_text(entity, "suffix", author, "arXiv:suffix")
            if "lastname" in entity and entity["lastname"] is not None and "forenames" in entity and entity["forenames"] is not None:
                entity["name"] = entity["lastname"] + ", " + entity["forenames"]
            affiliations = self._find_elements(author,"arXiv:affiliation")
            if affiliations:
                entity["affiliation"] = []
                for affiliation in affiliations:
                    entity["affiliation"].append(affiliation.text)
            map["author"].append(entity)

        return common.Metadata(map)



class MetadataReaderPMC(MetadataReaderAbstract):
    """A metadata reader for PubMedCentral Front Matter data.
    """

    def __call__(self, metadata_element, nsprefix="nlmaa:"):
        map = {}

        #logging.info("Parsing " + etree.tostring(metadata_element))

        article = self._find_element(metadata_element,"{0}article".format(nsprefix))

        #In the case of the bulk importer, the root element is Article
        if article is None:
            article = metadata_element

        # front
        front = self._find_element(article,"{0}front".format(nsprefix))
        
        # back
        back = self._find_element(article,"{0}back".format(nsprefix))

        # journal meta
        journal_meta = self._find_element(front,"{0}journal-meta".format(nsprefix))
        
        # article metadata
        article_meta = self._find_element(front,"{0}article-meta".format(nsprefix))
        
        if journal_meta is not None:
            try:
                map["journal"] = {}

                (self._set_map_with_element_text(map["journal"], "name", journal_meta, "{0}journal-title-group/{0}journal-title".format(nsprefix)) or
                    self._set_map_with_element_text(map["journal"], "name", journal_meta, "{0}journal-title".format(nsprefix)))
                
                issns = journal_meta.findall("{0}issn".format(nsprefix), self._namespaces)
                if issns:
                    map["journal"]["identifier"] = []
                    for issn in issns:
                        map["journal"]["identifier"].append({"type": issn.get('pub-type'), "id": issn.text, "canonical":issn.get('pub-type') + ':' + issn.text})
                
                self._set_map_with_element_text(map["journal"], "publisher", journal_meta, "{0}publisher/{0}publisher-name".format(nsprefix))
            except:
                logging.error("Could not extract journal metadata")
        else:
            logging.info("No journal metadata found for ")
        
        
        if article_meta is not None:
            try:
                #identifiers
                article_ids = article_meta.findall("{0}article-id".format(nsprefix), self._namespaces)
                if article_ids:
                    map["identifier"] = []
                    for article_id in article_ids:
                        map["identifier"].append({"type": article_id.get('pub-id-type'), "id": article_id.text, "canonical": article_id.get('pub-id-type') + ':' + article_id.text })

                        if article_id.get('pub-id-type') == 'pmid' and article_id.text == '17242517':
                            print "FOUND THE record with missing citations"
                            logging.critical("FOUND THE record with missing citations")
                            logging.critical(etree.tostring(metadata_element))
                            
            except:
                logging.error("Could not extract identifiers from article metadata")
            
            try:
                #title
                self._set_map_with_element_text(map, "title", article_meta, "{0}title-group/{0}article-title".format(nsprefix))
            except:
                logging.error("Could not extract title from article metadata")
            
            try:
                #pagination
                self._set_map_with_element_text(map, "volume", article_meta, "{0}volume".format(nsprefix))
                self._set_map_with_element_text(map, "issue", article_meta, "{0}issue".format(nsprefix))
                self._set_map_with_element_text(map, "firstpage", article_meta, "{0}fpage".format(nsprefix))
                self._set_map_with_element_text(map, "lastpage", article_meta, "{0}lpage".format(nsprefix))
                if "firstpage" in map:
                    if "lastpage" in map and (map["firstpage"] != map["lastpage"]):
                        map["pages"] = map["firstpage"] + "-" + map["lastpage"]
                    else:
                        map["pages"] = map["firstpage"]
            except:
                logging.error("Could not extract pagination from article metadata")

            try:
                #publication date
                # why only use the pmc-release date? need to check with Mark
                pub_date = article_meta.find("{0}pub-date[@pub-type='pmc-release']".format(nsprefix), self._namespaces)
                if pub_date is not None:
                    self._set_map_with_element_text(map, "year", pub_date, "{0}year".format(nsprefix))
                    self._set_map_with_element_text(map, "month", pub_date, "{0}month".format(nsprefix))
                    self._set_map_with_element_text(map, "day", pub_date, "{0}day".format(nsprefix))
                else:
                    logging.info("No publication data for ")
            except:
                logging.error("Could not extract publication date from article metadata")
            
            try:
                #copyright
                self._set_map_with_element_text(map, "copyright", article_meta, "{0}permissions/{0}copyright-statement".format(nsprefix))
            except:
                logging.error("Could not extract copyright info from article metadata")
            
            try:
                #abstract
                self._set_map_with_element_xml(map, "abstract", article_meta, "{0}abstract".format(nsprefix))
            except:
                logging.error("Could not extract abstract from article metadata")
            
            try:
                #keywords
                keywords = article_meta.findall("{0}kwd_group/{0}kwd".format(nsprefix), self._namespaces)
                if keywords:
                    map["keyword"] = []
                    for keyword in keywords:
                        map["keyword"].append(keyword.text)
                else:
                    logging.info("No keywords for ")
            except:
                logging.error("Could not extract keywords from article metadata")
            
            try:
                #contributors
                contribs = article_meta.findall("{0}contrib-group/{0}contrib".format(nsprefix), self._namespaces)
                if contribs:
                    map["author"] = []
                    map["editor"] = []
                    for contrib in contribs:
                        entity = {}
                        if contrib.get('corresp') == 'yes':
                            entity["corresponding"] = 'yes'
                        self._set_map_with_element_text(entity, "lastname", contrib, "{0}name/{0}surname".format(nsprefix))
                        self._set_map_with_element_text(entity, "forenames", contrib, "{0}name/{0}given-names".format(nsprefix)) #MW: Changed firstname to forenames. Discuss with Mark.
                        if "lastname" in entity and entity["lastname"] is not None and "forenames" in entity and entity["forenames"] is not None:
                            entity["name"] = entity["lastname"] + ", " + entity["forenames"]
                        email = contrib.find("{0}address/{0}email".format(nsprefix), self._namespaces)
                        if email is None:
                            email = contrib.find("{0}email".format(nsprefix), self._namespaces)
                        if email is not None:
                            entity["identifier"] = {"type": "email", "id": email.text}
                        
                        xrefs = contrib.findall("{0}xref".format(nsprefix), self._namespaces)
                        affs = article_meta.findall("{0}aff".format(nsprefix), self._namespaces) #NOT ContribGroup - check with Mark
                        for xref in xrefs:
                            if xref.get('ref-type') == "aff":
                                rid = xref.get("rid")
                                for aff in affs:
                                    if aff.get("id") == rid:
                                        if "affiliation" not in entity:
                                            entity["affiliation"] = []
                                        for text in aff.itertext():
                                            entity["affiliation"].append(text)
                                        
                        if contrib.get("contrib-type") == "author":
                            map["author"].append(entity)
                        if contrib.get("contrib-type") == "editor":
                            map["editor"].append(entity)
                else:
                    logging.info("No contributors found for ")
            except:
                logging.error("Could not extract contributors from article metadata")
        else:
            logging.info("No article metadata found for ")


        if back is not None:
            acknowledgements = back.findall("{0}ack/{0}sec/{0}p".format(nsprefix), self._namespaces)
            if acknowledgements:
                map["acknowledgement"] = []
                for acknowledgement in acknowledgements:
                    map["acknowledgement"].append(acknowledgement.text)
            else:
                logging.info("No acknowledgements found for ")
            
            conflicts = back.findall("{0}fn-group/{0}fn/{0}p".format(nsprefix), self._namespaces)
            if conflicts:
                map["conflict"] = []
                for conflict in conflicts:
                    map["conflict"].append(conflict.text)
            else:
                logging.info("No conflicts found for ")
                    
            refs = back.findall("{0}ref-list/{0}ref".format(nsprefix), self._namespaces)
            if refs:
                map["citation"] = []
                for ref in refs:
                    entity = {}
                    self._set_map_with_element_text(entity, "label", ref, "{0}label".format(nsprefix))
                    
                    #Three different ways to cite articles. Check with Mark.
                    citation = ref.find("{0}mixed-citation".format(nsprefix), self._namespaces)
                    if citation is None:
                        citation = ref.find("{0}element-citation".format(nsprefix), self._namespaces)
                    if citation is None:
                        citation = ref.find("{0}citation".format(nsprefix), self._namespaces)
                    
                    if citation is not None:
                        self._set_map_with_element_text(entity, "title", citation, "{0}article-title".format(nsprefix))
                        pub_ids = citation.findall("{0}pub-id".format(nsprefix), self._namespaces)
                        if pub_ids:
                            entity["identifier"] = []
                            for pub_id in pub_ids:
                                entity["identifier"].append({"type": pub_id.get('pub-id-type'), "id": pub_id.text, 'canonical':pub_id.get('pub-id-type') + ':' +  pub_id.text})
                    # TODO: should this append happen even if the entity is empty? or bring into the above IF
                    map["citation"].append(entity)
                    # add code here to create a record for this citation if it does not already exist
            else:
                logging.info("No refs found for ")
        else:
            logging.info("No back metadata for ")

        return common.Metadata(map)



class CitationExtractorTex(object):
    """A citation extractor for ArXiv Latex
    """

    # matches \em{, \emph{, {\em, {\emph, \textit{, {\textit
    _re_starts_with_emph_tag = re.compile(r'^\s*(\{\\emp?h?\s+|\\emp?h?\{|\{\\textit\s+|\\textit\{)')

    # matches \em, \emph, \textit
    _re_split_emph_tag = re.compile(r'(\\emp?h?|\\textit)')
    _re_split_newblock = re.compile(r'\\newblock')


    def process(self, arxivid, infile):
        file_handle = open(infile, 'r')
        raw_data = file_handle.read()
        file_handle.close()
    
        #remove latex comments, to avoid confusion in processing
        data = re.sub(r"^\s*\%.*$", "", raw_data, 0, re.MULTILINE)

        #remove whitespace and newlines
        data = re.sub(r"\s+", " ", data, 0, re.MULTILINE)

        #find the bibliography section
        match = re.search(r'\\begin{thebibliography(?P<bibliography>.*)\\end{thebibliography', data, re.DOTALL)
        if match:
            data = match.group('bibliography')

            #get a list of bibitems. Start at [1:] to ignore the stuff between \begin{thebibliography} and \bibitem
            counter=1
            for bibitem in re.split(r"\\bibitem", data)[1:]:

                #trim the string
                bibstring_to_process = bibitem.strip()
                #print "Abibstring_to_process:\t", bibstring_to_process

                (arxiv_id, bibstring_to_process) = extract_arxiv_id(bibstring_to_process)
                #print "Bbibstring_to_process:\t", bibstring_to_process

                (label, key, bibstring_to_process) = extract_label_key(bibstring_to_process)
                #print "Cbibstring_to_process:\t", bibstring_to_process

                (url, bibstring_to_process) = extract_url(bibstring_to_process)

                (authors, bibstring_to_process) = extract_authors(bibstring_to_process)
                #print "Dbibstring_to_process:\t", bibstring_to_process


                #print "BeforeTitle:\t", bibstring_to_process
                (title, bibstring_to_process) = extract_title(bibstring_to_process)
                #print "AfterTitle:\t", bibstring_to_process
            
            
                #print "Counter: %i\tarxiv_id: %s\tlabel: %s\tkey: %s\turl: %s\tauthors: %s\ttitle: %s" % (counter, arxiv_id, label, key, url, authors, title)
                print "COUNTER: %i \t AUTHORS: %s \t TITLE: %s" % (counter, authors, title)
                #print "bibstring_to_process:\t", bibstring_to_process
                print bibitem, "\n"
                counter += 1
                #break
            
            
        
    
        #out = open(args.outfile,'w')
        #out.write(json.dumps(d,indent=4))
        #out.close()

    def extract_arxiv_id(self, bibitem):
        #New arxiv citation format
        match = re.search(r'arxiv\:(?P<arxiv>\d{4}\.\d{4}(v\d+)?)', bibitem, re.IGNORECASE)
        if match:
            return (match.group('arxiv'), re.sub(r'arxiv\:\d{4}\.\d{4}(v\d+)?', "", bibitem, 0, re.IGNORECASE).strip())
        else:
            #try old arxiv citation format
            match = re.search(r'arxiv\:(?P<arxiv>[\w\-]+\/\d{7}(v\d+)?)', bibitem, re.IGNORECASE)
            if match:
                return (match.group('arxiv'), re.sub(r'arxiv\:[\w\-]+\/\d{7}(v\d+)?', "", bibitem, 0, re.IGNORECASE).strip())
            else:
                return (None, bibitem)


    def extract_url(self, bibitem):
        #Extract URL if it is within a \url{} tag
        match = re.search(r'\\url\{(?P<url>https?\:\/\/[^\}]+)\}', bibitem, re.IGNORECASE)
        if match:
            return (match.group('url'), re.sub(r'\\url\{https?\:\/\/[^\}]+\}', "", bibitem, 0, re.IGNORECASE).strip())
        else:
            #Otherwise just try and search for http://
            match = re.search(r'(?P<url>https?\:\/\/[\w\+\&\@\#\/\%\?\=\~\_\-\|\!\:\,\.\;]+[\w\+\&\@\#\/\%\=\~\_\|])', bibitem, re.IGNORECASE)
            if match:
                return (match.group('url'), re.sub(r'https?\:\/\/[\w\+\&\@\#\/\%\?\=\~\_\-\|\!\:\,\.\;]+[\w\+\&\@\#\/\%\=\~\_\|]', "", bibitem, 0, re.IGNORECASE).strip())
            else:
                return (None, bibitem)


    def extract_label_key(self, bibitem):
        match = re.match(r'^(\[(?P<label>[^\]]+)\])?\{(?P<key>[^\}]+)\}', bibitem)
        if match:
            return (match.group('label'), match.group('key'), re.sub(r'^(\[[^\]]+\])?\{[^\}]+\}', "", bibitem).strip())
        else:
            return (None, None, bibitem.strip())


    def extract_authors(self, bibitem):
        #try to split citation by \newblock and assume first section is the author list (it usually is?!)
        sections = _re_split_newblock.split(bibitem, 1)
        if (len(sections) > 1):
            # call remove_wrapping_curly_braces() as sometimes the records are wrapped in them. A full parser is not necessary in this case.
            (authors, remainder) = (remove_wrapping_curly_braces(sections[0]), sections[-1])
        else:
            #instead try to split on \em or \emph or \textit, as that usually demarcates the title
            sections = _re_split_emph_tag.split(bibitem, 1)
            if (len(sections) > 1):
                # call remove_wrapping_curly_braces() as sometimes the records are wrapped in them. A full parser is not necessary in this case.
                (authors, remainder) = (remove_wrapping_curly_braces(sections[0]), "\emph" + sections[-1])
            else:
                # try to split on \<space> as some publications have used this
                sections = re.split(r'\\\s+', bibitem, 1)
                if (len(sections) > 1):
                    # call remove_wrapping_curly_braces() as sometimes the records are wrapped in them. A full parser is not necessary in this case.
                    (authors, remainder) = (remove_wrapping_curly_braces(sections[0]), sections[-1])
                else:
                    # give up and assume that the whole bibitem are the authors
                    (authors, remainder) = (bibitem, "")
        authors = remove_end_punctuation(authors.strip())
        if len(authors) == 0:
            authors = None
        return (authors, remainder.strip())


    def extract_title(self, bibitem):
        # Ok, this is not so trivial!
        # First we will see if there is a \newblock, and if so, assume that the title is everything in front of the first \newblock
        # NB. You must call extract_authors() first to parse out the authors first before the title, as they will be infront of an earlier \newblock
        sections = _re_split_newblock.split(bibitem, 1)
        if (len(sections) > 1):
            # sometimes the title can be in an {\em } tag or \em{ } tag or \textit{} tag, inside of the \newblock section. In this case, extract using the full parser
            match = _re_starts_with_emph_tag.match(bibitem)
            if match:
                (title, remainder) = full_parse_curly_braces(bibitem, 1, 1) #assume first bracket at level 1
                #TODO strip out \em in title
            else:
                # call remove_wrapping_curly_braces() as sometimes the records are wrapped in them. A full parser is not necessary in this case.
                (title, remainder) = (remove_wrapping_curly_braces(sections[0]), sections[1])
        else:
            # No \newblock was found. So we need to try and parse on something else
            # Check to see if the bibitem starts with \emph{ or {\emph }. If so, assume the title is contained inside the \emph{} tag
            # In this case, a full parser is required to extract the title, a regex is insufficient.
            match = re.match(r'^\s*(\{\\emp?h?\s+|\\emp?h?\{)', bibitem)
            if match:
                (title, remainder) = full_parse_curly_braces(bibitem, 1, 1) #assume first brack at level 1
            else:
                # No \newblock or \emph{ was found. Instead, try to split on first full stop + space
                sections = re.split(r'\.\s+', bibitem, 1)
                if (len(sections) > 1):
                    (title, remainder) = (sections[0], sections[1])
                else:
                    # Ok, at this point we are not doing very well. Try to split on a full stop.
                    sections = re.split(r'\.', bibitem, 1)
                    if (len(sections) > 1):
                        (title, remainder) = (sections[0], sections[1])
                    else:
                        # One last try - we've attempted, \newblock, \emph, fullstop+space, fullstop. Now try a comma+space.
                        sections = re.split(r'\,\s+', bibitem, 1)
                        if (len(sections) > 1):
                            (title, remainder) = (sections[0], sections[1])
                        else:
                            # Ok time to give up. Either we can assume that the whole string is a title, or that there is no title.
                            # Lets go with the former.
                            (title, remainder) = (bibitem, "")

        # Finally, lets tidy-up the title and return it
        return (remove_end_punctuation(title.strip()), remainder.strip())



    def remove_end_punctuation(self, bibitem):
        return re.sub(r'[\.\,\s]+$', "", bibitem)



    def full_parse_curly_braces(self, bibitem, brace_level=1, brace_number=1):
        # This method iterates over a string, analysing the curly-braces contained therein. 
        # It extracts the data for the specified level (and above) and specified brace number
        #
        # Some examples:
        #
        # INPUT:
        #   bibitem = "level 0 { level 1a {level 2} level 1a} level 0 {level 1b} level 0"
        #   brace_level = 1
        #   brace_number = 1
        # RESULT:
        #   parsed ==> "level 1a {level 2} level 1a"
        #   remainder ==> "level 0 {} level 0 {level 1b} level 0"
        #
        # INPUT:
        #   bibitem = "level 0 { level 1a {level 2} level 1a} level 0 {level 1b} level 0"
        #   brace_level = 1
        #   brace_number = 2
        # RESULT:
        #   parsed ==> "level 1b"
        #   remainder ==> "level 0 { level 1a {level 2} level 1a} level 0 {} level 0"
        #
        # INPUT:
        #   bibitem = "level 0 { level 1a {level 2} level 1a} level 0 {level 1b} level 0"
        #   brace_level = 2
        #   brace_number = 1
        # RESULT:
        #   parsed ==> "level 2"
        #   remainder ==> "level 0 { level 1a {} level 1a} level 0 {level 1b} level 0"
    
        parser_level = 0
        brace_count = 0
        parsed = ""
        remainder = ""

        # iterate over every character in the string
        for char in bibitem.strip():

            # if we are closing the brace, decrement the parser_level
            if char == '}':         
                parser_level -= 1
        
            # if we are at or above the desired level, and in the correct brace_number, then parse the string
            # otherwise, store the string in the remainder
            if parser_level >= brace_level and brace_count == brace_number:
                parsed += char
            else:
                remainder += char

            # if we are opening the brace, increment the parser_level            
            if char == '{':
                parser_level += 1
                #if we are now on the desired level, then increment the brace_count
                if parser_level == brace_level:
                    brace_count += 1

        # if the parsed string starts with '\em ' then this can be removed
        parsed = re.sub(r'^\\emp?h?\s+', "", parsed, 1)
        return (parsed, remainder)
    

    
    def remove_wrapping_curly_braces(self, bibitem):
        match = re.match(r'^\s*\{(?P<value>.+)\}\.?\s*$', bibitem)
        if match:
            return match.group('value').strip()
        else:
            return bibitem

