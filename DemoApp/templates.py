

#
#
# Helper and Syles
#
#

analytics = '''
<script type="text/javascript">

  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', 'UA-29989314-4']);
  _gaq.push(['_trackPageview']);

  (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();

</script>'''



mathjax = '''
<script type="text/x-mathjax-config">
MathJax.Hub.Config({
  tex2jax: {inlineMath: [['$','$'], ['\\(','\\)']]},
  "HTML-CSS": {scale: 90},
  ignoreClass: "references",
  processClass: "mathjax",
});
</script>
<script type="text/javascript"
  src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML">
</script>
'''

css = '''
<style type="text/css">
<!--
body {
margin:0;
padding: 0;
}


h1 {
font-size:30px; font-family: 'Lucida Grande', helvetica, arial, verdana, sans-serif;
font-size: x-large;
font-weight: bold;
line-height: 150%;
}

h2 {
font-family: 'Lucida Grande', helvetica, arial, verdana, sans-serif;
font-size: medium;
line-height: 180%;
}

.text {
font-family: 'Lucida Grande', helvetica, arial, verdana, sans-serif;
font-size: 90%;
line-height: 130%;
}

#abstract {
width: 100%;
text-align:justify;
}

h2.abstract {
display: inline;
line-height: 100%;
}

a:link { color:#000070; text-decoration:none; }
a:hover { text-decoration:underline; }
a:visited { color:#551A8B; text-decoration:none; }


#meta {
   width: 80%;
   margin-top:50px;
   align : center;
}

#headder {
padding: 8px;
border-style: none none dotted none;
border-width: 1px;
background-color: #EEEEEE;
}

.references {
font-family: 'Lucida Grande', helvetica, arial, verdana, sans-serif;
font-size: 90%;
line-height: 130%;
text-align:left;
float:left; 
width:100%;
} 

.references ul {
margin: 0;
}
.references ul li {
margin-top: 5;
}

--> 
</style>'''

#
#
#
# Templates
#
#
#


html_head = u'''
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta name="author" content="Heinrich Hartmann">
<meta name="author" content="Rene Pickhardt">
<meta name="keywords" content="Related-Work, Related, Work, Articles, References, Citations, Arxiv">
<meta name="date" content="2012-10-02">
<title>Related-Work.net</title>
''' + css + analytics + u'''</head>'''


head_template = u'''
<div id='headder'>
    <h1 style='display:inline'> <a href='/'>Related-Work.net</a> </h1> 
    <h2 style='display:inline'> {breadcrumbs} </h2>

    <div style='display:inline; float:right; line-height:100%;'>
    <form action="/search" method="get" style='margin:5 0 0 0'>
    <input name='q' type='text' size=20>
    <input type="submit" value="search">
    </form>
    </div>
</div>
'''


front_template = u'''
<body class="tex2jax_ignore">
''' + head_template.format(
    breadcrumbs = ''
    ) + u'''
<div align='center' id='body'>
    <div id='meta'>
         <h1 class='tex2jax_process'>{title}</h1>
         <h2>by:{author}</h2>
         <div id='abstract' class='tex2jax_process'>
             <h2 class='abstract'>Abstract:</h2>{abstract}
         </div>
         <div>
         <div class='references'>
              <h2>Examples:</h2>
              {examples}
         </div>
         <div>

    </div>
</div>
</body>
'''

front_html = front_template.format(
        title = '<a href="#">Related-Work.net</a>',
        author = '<a href="http://heinrich-hartmann.net"> Hartmann, Heinrich</a> and <a href="http://rene-pickhardt.de">Pickhardt, Rene</a>',
        abstract = '''
This is an inofficial demo of our web project <a href='http://blog.related-work.net'>related-work.net</a>. 
The ultimate aim is to create a new website for the scientific community which brings together people reading the same article. 
An essential feature is the availability of reference data, which allows the user to find related work easily. 
So far we have extracted reference data from the <a href='http://arxiv.org'>arxiv</a> and made it browsable. Currently our database contains:
<ul>
<li>ca. 750.000 articles</li>
<li>ca. 16.000.000 reference entries </li>
<li>ca. 2.000.000 links between articles.</li>
</ul>
We follow a strict openness principle by making available the <a href='http://code.google.com/p/reference-retrieval/'> source code </a> and 
the data we collect.  For further information we kindly refer you to our <a href='http://blog.related-work.net'>proposal</a>.''',
        examples = '''
<ul>
<li><a href="http://dev.related-work.net/author/Kontsevich,_Maxim"> Author: Kontsevich, Maxim </a></li>
<li><a href="http://dev.related-work.net/author/Witten,_Edward"> Author: Witten, Edward</a></li>
<li><a href="/arxiv:hep-th_9711200">Maldacena  J.  M., The Large N Limit of Superconformal Field Theories and Supergravity, 1997 (citations: 2992)</a></li> 
<li><a href="/arxiv:hep-th_9802150">Witten  E., Anti De Sitter Space And Holography, 1998 (citations: 2448)</a></li> 
<li><a href="/arxiv:hep-th_9802109">Gubser  S.  S. and Klebanov  I.  R. and Polyakov  A.  M., Gauge Theory Correlators from Non-Critical String Theory, 1998 (citations: 2207)</a></li> 
</ul>
''')



main_template =  u'''
<body class="tex2jax_ignore">
''' + head_template.format(
    breadcrumbs = u'''> arxiv > <a href='#'>{short_id}</a> >>> <a href='{source_url}'> source </a>''' 
    ) + u'''
<div align='center' id='body'>
    <div id='meta'>
         <h1 class='tex2jax_process'>{title}</h1>
         <h2>by: {author}</h2>
         <div id='abstract' class='tex2jax_process'>
             <h2 class='abstract'>Abstract:</h2> {abstract} 
         </div>
         <div>
         <div class='references'>
              <h2>Cited by ({citation_count})</h2>
              {citations}
         </div>
         <div class='references'>
              <h2>References ({reference_count})</h2>
              {references}
         </div>
         <div>
    </div>
</div>
</body>
'''

search_template =  u'''
<body>
''' + head_template.format(
    breadcrumbs = u'''
      >
      search
      >
      {search_string}
'''
    ) + u'''
<div align='center' id='body'>
    <div id='meta'>
         <div>
         <div class='references'>
              <h2>Authors:</h2>
              {authors}
         </div>
         <div class='references'>
              <h2>Articles:</h2>
              {articles}
         </div>
         <div>
    </div>
</div>
</body>
'''

author_template =  u'''
<body>
''' + head_template.format(
    breadcrumbs = u'''
      >
      author
      >
      <a href='{author_url}'> {author_name} </a>
'''
    ) + u'''
<div align='center' id='body'>
    <div id='meta'>
         <h1 class='tex2jax_process'>{author_name}</h1>
         <div class='references'>
              <h2>Articles:</h2>
              {references}
         </div>
    </div>
</div>
</body>
'''
