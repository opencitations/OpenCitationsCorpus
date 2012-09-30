import re

def extract_bibitems(tex_string):
    tex_string = clear_tex_comments(tex_string)
    tex_string = extract_tex_env(tex_string,'thebibliography')

    for item in tex_string.split('\\bibitem')[2:]:
        # Rem: First entry is space between \begin{theb...} and \bibitem
        # Remove \bibitem{label} - text
        label_end = item.find('}')
        item = item[label_end+1:]
        yield item

def remove_tex_tags(s):
    # Problems still there:
    # a lot of em's tt's it's (ok)
    # \"a \"o not handled properly J o rgensen; K. G o ral, B.-G. Englert, and K. Rz c a . z ewski, (ok now)
    # \label{adwdaw} tags survive Hu (2004) lima2004a Lima (ok now)
    # small Shakura N.L. Sunyaev R.A. 1973, A A 24 , 337 
    # biield    binamefont R. W.  Dunfo(ok now)
    # 2001a 2001MNRAS.326..722B Baes M., Dejonghe H., 20
    # \bibitem[{\citenamefont{Roy}(2008)}]{roy2008}
    # \bibinfo{author}{\bibfnamefont{R.}~\bibnamefont{Roy}},
    # \bibinfo{howpublished}{e-print arXiv:0803.2868} (\bibinfo{year}{2008}). (ok now)

        
    # Remove label and bibinfo tags
    s = re.sub(r'''\\(label|bibinfo)\{.+?\}''',' ',s,re.VERBOSE)

    # Replace \"a by a and \"u by u
    s = re.sub(r'\\"','',s)

    tex_codes = '''
        \\it \\bf \\sc \\em  \\emph 
        \\textbf  \\textit \\textsc
        \\newblock \\textsc
        '''.split()

    remove_strings = '''
        endcsname providecommand newblock samestyle csname
        href  author pages title citenamefont bibnamefont
        BibitemOpen penalty0 bibfield
        '''.split()

    # remove tex code
    for tag in tex_codes:
        s = s.replace(tag,'')

    # remove all non-alphanumeric characters
    s = re.sub(r'[^\w.,():/-]+',' ', s).strip()

    # remove more words
    for subs in remove_strings:
        s = s.replace(subs,'')

    # Remove leading , or whitespace
    s = re.sub(r'^[,\s]+','',s)

    return s


def extract_tex_env(file_string, env_name):
    """ 
    Finds all text enclosed by '\begin{env_name}' and '\end{env_name}' in file_string
    """

    out = ''
    position = 0 
    while True:
        start_sec   = file_string.find('\\begin{' + env_name + '}',position)
        # Break if we have not found anything
        if start_sec == -1: break

        # Find the closing tag
        end_sec     = file_string.find('\\end{' + env_name + '}',  start_sec)

        # Append contents to out
        out += file_string[ start_sec + len(env_name) + 8  :end_sec] 

        # Go on starting from end of last section
        position = end_sec
    return out


def clear_tex_comments(tex_string):
    out = ''
    for line in tex_string.splitlines():
        end = line.find('%')
        if end == -1: # no comment in line
            out += line + '\n'
        else:
            out += line[:end] + '\n'
    return out

