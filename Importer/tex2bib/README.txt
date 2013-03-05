  tex2bib
    Input a TeX document containing \bibitems, translate these
    to BibTeX format
 
  Usage:
 		tex2bib [-k][-i infile] [-o outfile]
 		-k:  regenerate keys
 		if infile not given, reads from stdin
 		if outfile not given, prints to stdout

  The entire tex document is scanned for \bibitems, ending when
  the string '\end{thebibliography}' is read.

  Assumes that bibitems are formatted as follows:
   -- {key}author(s), (date) at the beginning
   -- titles of books or names of journals: {\em title}
   -- article titles: 	after date, `` '' quotes optional
   -- volume, pages: 	{\it vol}, nnn-nnn.
   -- publisher/address:    address:publisher
 
   All text in the bibitem which cannot be parsed is included
   in a note = { } field

  Examples of a book, article, inproceedings:

 \bibitem{Bertin83}Bertin, J. (1983),
         {\em Semiology of Graphics} (trans. W. Berg).  Madison, WI:
         University of Wisconsin Press.
 
 \bibitem{Bickel75}Bickel, P. J., Hammel, J. W. and O'Connell, J. W.
         (1975).
         Sex bias in graduate admissions: data from Berkeley.  {\em
         Science}, {\it 187}, 398-403.
 
 \bibitem{Farebrother87}Farebrother, R. W. (1987),
         ``Mechanical representations of the ${L}_1$ and ${L}_2$ estimation
         problems'', In Y. Dodge (ed.)  {\em Statistical data analysis
         based on the L1 norm and related methods}, Amsterdam:
         North-Holland., 455-464.


  These are output as:

 @Book{  Bertin:83,
     author      = {J. Bertin},
     year        = 1983,
     title       = {Semiology of Graphics},
     publisher   = {University of Wisconsin Press},
     address     = {Madison, WI},
     note        = {(trans. W. Berg).}
 }
 @Article{       Bickel:75,
     author      = {Bickel, P. J. and Hammel, J. W. and O'Connell, J. W.},
     year        = 1975,
     title       = {Sex Bias in Graduate Admissions: Data from Berkeley},
     journal     = {Science},
     volume      = 187,
     pages       = {398-403}
 }
 @InCollection{  Farebrother:87,
     author      = {R. W. Farebrother},
     year        = 1987,
     title       = {Mechanical Representations of the ${L}_1$ and ${L}_2$ Estimation Problems},
     booktitle   = {Statistical Data Analysis Based on the L1 Norm and Related Methods},
     editor      = {Y. Dodge},
     publisher   = {North-Holland},
     address     = {Amsterdam},
     pages       = {455-464}

  Text in a bibitem is removed from the bibitem as it is assigned to
  bibtex fields.  Any text remaining is assigned to a note={  } field
  at the end.  Since the parsing is heuristic, some manual fixup work
  can be expected at the end.

