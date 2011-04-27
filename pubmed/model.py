from collections import namedtuple

article_fields = (
    "group id xml_container ctype journal doi pmid pmc isbn full_citation year "
  + "month day title author source license publisher issue volume edition "
  + "fpage lpage keywords abstract filename in_text_reference_pointer_count "
  + "reference_count uri in_oa_subset retracted patent_number").split()

article_field_set = set(article_fields)
Article = namedtuple('Article', article_fields)

#person_fields = "given-names surname".split()
#person_field_set = set(person_fields)
#Person = namedtuple('Person', person_fields)

