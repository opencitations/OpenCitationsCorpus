#
# HTML templates
#

#
#
#  Helper and Syles
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
font-family: 'Lucida Grande', helvetica, arial, verdana, sans-serif;
font-size: 90%;
}

a:link { color:#000070; text-decoration:none; }
a:hover { text-decoration:underline; }
a:visited { color:#551A8B; text-decoration:none; }

h1 {
font-size: x-large;
font-weight: bold;
line-height: 150%;
}

h2 {
font-size: medium;
line-height: 180%;
}

#abstract {
width: 100%;
text-align:justify;
font-family: 'Lucida Grande', helvetica, arial, verdana, sans-serif;
line-height:140%;
}

h2.abstract {
display: inline;
line-height: 100%;
}



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

front_html = u'''
<body>
  <div id='headder'>
    <h1 style='display:inline'> <a href='/'>Related-Work.net</a></h1> 
  </div>
  <div align='center' id='body'>
    <div style='width: 60%; margin-top:50px; align:center;'>
      <h1><a href='/'>Related-Work.net</a></h1>
      <span style='line-height: 250%;font-family: 'Lucida Grande', helvetica, arial, verdana, sans-serif;font-size: 90%;'>
	An open scientific discussion and reference platform. <a href='http://blog.related-work.net'>Read more.</a>
      </span>
      <form action="/search" method="get" style='margin:40 0 0 0'>
	<input name='q' type='text' size=50>
	<input type="submit" value="search">
      </form>
      <div style='width:100%; text-align:left; margin-top:50px; line-height:150%'>
	<h2 style=line-height:100%'>Examples:</h2>
	<ul>
	  <li>Search: <a href='/search?q=Operads'>Operads</a></li>
	  <li>Search: <a href='/search?q=Triangulated+Categories'> Triangulated Categories</a></li>
	  <li>Search: <a href='/search?q=Mukai'> Mukai</a></li>
	  <li>Author: <a href='/author/Witten,_Edward'> Witten, Edward </a></li>
	  <li>Author: <a href='/author/Kontsevich,_Maxim'> Kontsevich, Maxim </a></li>
	  <li>Paper: <a href='/arxiv:0707.2348'> Pandharipande and Thomas, <em>Curve counting via stable pairs</em></a></li>
	  <li>Paper: <a href='/arxiv:math_0212237'> Bridgeland, <em>Stability conditions on triangulated categories</em></a></li>
	  <li>Paper: <a href='/arxiv:0907.3987'> Gaiotte, Moore and Neitzke, <em>Wall-crossing, Hitchin Systems, and the WKB Approximation</em></a></li>
	</ul>
      </div>
    </div>
</body>
'''



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
