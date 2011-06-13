<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:mml="http://www.w3.org/1998/Math/MathML" version="2.0">
  <xsl:output indent="yes"/>
  <xsl:template match="/">
    <article-data>
      <xsl:comment>
          Citation data from <xsl:value-of select="document-uri(.)"/>.
      </xsl:comment>
      <xsl:apply-templates select="*"/>
    </article-data>
  </xsl:template>
  <xsl:template name="article-id">
    <xsl:variable name="ids" select="front/article-meta/article-id"/>
    <xsl:choose>
      <xsl:when test="$ids[@pub-id-type='pmid']">
        <xsl:value-of select="concat('pmid:', $ids[@pub-id-type='pmid'][1])"/>
      </xsl:when>
      <xsl:when test="$ids[@pub-id-type='pmc']">
        <xsl:value-of select="concat('pmc:', $ids[@pub-id-type='pmc'][1])"/>
      </xsl:when>
      <xsl:when test="$ids[@pub-id-type='doi']">
        <xsl:value-of select="concat('doi:', $ids[@pub-id-type='doi'][1])"/>
      </xsl:when>
      <xsl:otherwise>something</xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template match="article">
    <xsl:variable name="id">
      <xsl:call-template name="article-id"/>
    </xsl:variable>
    <!-- We'll keep our in text reference pointers for later -->
    <xsl:variable name="in-text-reference-pointers">
      <xsl:apply-templates select="body">
        <xsl:with-param name="id" select="$id"/>
      </xsl:apply-templates>
    </xsl:variable>
    <node type="article" id="{$id}">
      <data key="provenance">pmc_oa</data>
      <data key="in_text_reference_pointer_count">
        <xsl:value-of select="count($in-text-reference-pointers//node[@type='in-text-reference-pointer'])"/>
      </data>
      <data key="reference_count">
        <xsl:value-of select="count(back//ref-list/ref/(citation|element-citation|mixed-citation))"/>
      </data>
      <data key="xml_container">article</data>
      <data key="ctype">
        <xsl:choose>
          <xsl:when test="@article-type">
            <xsl:value-of select="@article-type"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>journal-article</xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </data>
      <data key="title">
        <xsl:value-of select="front/article-meta/title-group/article-title"/>
      </data>
      <data key="in_oa_subset">true</data>
      <xsl:variable name="date">
        <xsl:choose>
          <xsl:when test="front/article-meta/pub-date[@pub-type='ppub']">
            <xsl:copy-of select="front/article-meta/pub-date[@pub-type='ppub']/*"/>
          </xsl:when>
          <xsl:when test="front/article-meta/pub-date[@pub-type='epub']">
            <xsl:copy-of select="front/article-meta/pub-date[@pub-type='epub']/*"/>
          </xsl:when>
        </xsl:choose>
      </xsl:variable>
      <xsl:for-each select="$date/(day|month|year)">
        <data key="{name()}">
          <xsl:value-of select="."/>
        </data>
      </xsl:for-each>
      <data key="source">
        <xsl:value-of select="front/article-meta/contrib-group/aff[1]"/>
      </data>
      <data key="keywords">
        <xsl:for-each select="front/article-meta/kwd-group/kwd">
          <xsl:value-of select="."/>
          <xsl:if test="position() != last()">
            <xsl:text>, </xsl:text>
          </xsl:if>
        </xsl:for-each>
      </data>
      <data key="abstract">
        <xsl:value-of select="front/article-meta/abstract"/>
      </data>
      <data key="fabio_type">
          <xsl:choose>
              <xsl:when test="front-article-meta/article-categories/subj-group[@subj-group-type = 'heading']/subject[text() = 'Research Article']">
                  <xsl:text>JournalArticle</xsl:text>
                </xsl:when>
                <xsl:otherwise>Expression</xsl:otherwise>
            </xsl:choose>
        </data>
      <xsl:for-each select="front/article-meta/(volume|issue|fpage|lpage)">
        <data key="{name()}">
          <xsl:value-of select="."/>
        </data>
      </xsl:for-each>
      <xsl:if test="front/article-meta/permissions/license/@xlink:href">
        <data key="license">
          <xsl:value-of select="front/article-meta/permissions/license/@xlink:href"/>
        </data>
      </xsl:if>
      <xsl:for-each select="front/article-meta/article-id">
        <xsl:if test="@pub-id-type and index-of(('pmc', 'pmid', 'doi'), @pub-id-type)">
          <data key="{@pub-id-type}">
            <xsl:value-of select="."/>
          </data>
        </xsl:if>
      </xsl:for-each>
      <data key="author">
        <xsl:for-each select="front/article-meta/contrib-group/contrib[@contrib-type='author']/name">
          <xsl:value-of select="concat(surname, ' ', given-names)"/>
          <xsl:if test="position() != last()">
            <xsl:text>, </xsl:text>
          </xsl:if>
        </xsl:for-each>
      </data>
      <xsl:copy-of select="$in-text-reference-pointers"/>
    </node>
    <node type="journal" id="{$id}:journal">
      <data key="nlm_ta">
        <xsl:value-of select="front/journal-meta/journal-id[@journal-id-type='nlm-ta']/text()"/>
      </data>
      <data key="issn">
        <xsl:value-of select="front/journal-meta/issn[not(@pub-type='epub')]/text()"/>
      </data>
      <data key="eissn">
        <xsl:value-of select="front/journal-meta/issn[@pub-type='epub']/text()"/>
      </data>
      <data key="title">
        <xsl:value-of select="front/journal-meta/journal-title-group/text()"/>
      </data>
    </node>
    <edge type="journal" source="{$id}" target="{$id}:journal"/>
    <xsl:for-each select="front/journal-meta/publisher">
      <node type="organisation" id="{$id}:publisher">
        <data key="name">
          <xsl:value-of select="publisher-name"/>
        </data>
        <data key="address">
          <xsl:value-of select="publisher-loc"/>
        </data>
      </node>
      <edge type="publisher" source="{$id}:journal" target="{$id}:publisher"/>
    </xsl:for-each>
    <xsl:for-each select="front/article-meta/contrib-group/contrib">
      <xsl:variable name="person-index" select="position()"/>
      <node type="person" id="{$id}:person:{$person-index}">
        <data key="surname">
          <xsl:value-of select="name/surname"/>
        </data>
        <data key="given-names">
          <xsl:value-of select="name/given-names"/>
        </data>
      </node>
      <edge type="contributor" source="{$id}" target="{$id}:person:{$person-index}">
        <data key="contrib-type">
          <xsl:value-of select="@contrib-type"/>
        </data>
        <data key="position">
          <xsl:value-of select="$person-index"/>
        </data>
      </edge>
      <xsl:for-each select="xref[@ref-type='aff']/@rid">
        <xsl:for-each select="tokenize(., '\s+')">
          <edge type="affiliation" source="{$id}:person:{$person-index}" target="{$id}:affiliation:{.}"/>
        </xsl:for-each>
      </xsl:for-each>
    </xsl:for-each>
    <xsl:for-each select="front/article-meta//aff">
      <node type="organisation" id="{$id}:affiliation:{@id}">
        <data key="address">
          <xsl:choose>
            <xsl:when test="addr-line">
              <xsl:value-of select="addr-line"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="text()"/>
            </xsl:otherwise>
          </xsl:choose>
        </data>
        <data key="position">
          <xsl:value-of select="position()"/>
        </data>
      </node>
    </xsl:for-each>
    <xsl:for-each select="back//ref-list/ref">
      <xsl:variable name="ref" select="."/>
      <xsl:variable name="citation" select="(citation|element-citation|mixed-citation)[1]"/>
      <xsl:variable name="cited-id">
        <xsl:value-of select="concat($id, ':reference:', @id)"/>
      </xsl:variable>
      <xsl:if test="$citation">
        <node type="article" id="{$cited-id}">
          <data key="provenance">pmc_oa_reference</data>
          <data key="xml_container">
            <xsl:value-of select="*[position()=last()]/name()"/>
          </data>
          <xsl:variable name="ctype">
            <xsl:choose>
              <xsl:when test="$citation/@publication-type">
                <xsl:value-of select="$citation/@publication-type"/>
              </xsl:when>
              <xsl:when test="$citation/@citation-type">
                <xsl:value-of select="$citation/@citation-type"/>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>none</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <data key="ctype"><xsl:value-of select="$ctype"/></data>
          <data key="fabio_type">
              <xsl:choose>
                  <xsl:when test="$ctype='journal'">JournalArticle</xsl:when>
                  <xsl:when test="$ctype='book'">Book</xsl:when>
                  <xsl:when test="$ctype='thesis'">Thesis</xsl:when>
                  <xsl:when test="$ctype='database'">Database</xsl:when>
                  <xsl:when test="$ctype='weblink'">WebPage</xsl:when>
                  <xsl:when test="$ctype='webpage'">WebPage</xsl:when>
                  <xsl:when test="$ctype='web'">WebSite</xsl:when>
                  <xsl:when test="$ctype='patent'">Patent</xsl:when>
                  <xsl:when test="$ctype='confproc'">ConferenceProceedings</xsl:when>
                  <xsl:when test="$ctype='conf-proceeding'">ConferenceProceedings</xsl:when>
                  <xsl:when test="$ctype='conf-proc'">ConferenceProceedings</xsl:when>
                  <xsl:when test="$ctype='computer-program'">ComputerProgram</xsl:when>
                  <xsl:when test="$ctype='commun'">PersonalCommunication</xsl:when>
                  <xsl:when test="$ctype='report'">Report</xsl:when>
                  <xsl:when test="$ctype='other'">Expression</xsl:when>
                  <xsl:when test="$ctype='other-ref'">Expression</xsl:when>
                  <xsl:when test="$ctype='undeclared'">Expression</xsl:when>
                  <xsl:otherwise>
                      <xsl:message>Unknown ctype: <xsl:value-of select="$ctype"/></xsl:message>
                      <xsl:text>Expression</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </data>
          <data key="full_citation">
            <xsl:call-template name="verbatim"/>
          </data>
          <xsl:choose>
            <xsl:when test="$citation[@publication-type='other' or @citation-type='other' or not(@publication-type or @citation-type)]">
              <xsl:if test="matches($citation, '(^|[^\dA-Za-z])10\.\d+/[\d.a-zA-Z\-]+')">
                <data key="doi">
                  <xsl:value-of select="replace($citation, '^(.*[^\dA-Za-z]|)(10\.\d+/[\d.a-zA-Z\-]*[\da-zA-Z]).*$', '$2', 's')"/>
                </data>
              </xsl:if>
              <xsl:choose>
                <xsl:when test=".//year">
                  <data key="year">
                    <xsl:value-of select=".//year[1]"/>
                  </data>
                </xsl:when>
                <xsl:when test="matches($citation, '(^|[^\dA-Za-z.])[12]\d{3}([^\d]|$)')">
                  <data key="year">
                    <xsl:value-of select="replace($citation, '^(.*[^\dA-Za-z.]|)([12]\d{3})([^\d].*|)$', '$2', 's')"/>
                  </data>
                </xsl:when>
              </xsl:choose>
              <xsl:if test=".//article-title">
                <data key="title">
                  <xsl:value-of select=".//article-title[1]"/>
                </data>
              </xsl:if>
              <!--
            <data key="author">
              <xsl:value-of select="replace($citation, '^(((([A-Z]\.)+\s)|[A-Z][^.]+|[^A-Z.]+)+?)\..*$', '$1')"/>
            </data>
            -->
              <xsl:if test="matches($citation, '(^|\s)pp?\.? \d+')">
                <data key="fpage">
                  <xsl:value-of select="replace($citation, '^(.*\s|)pp?\.? (\d+).*$', '$2')"/>
                </data>
                <data key="lpage">
                  <xsl:choose>
                    <xsl:when test="matches($citation, '\spp?\.? \d+[\-&#x2013;]\d+')">
                      <xsl:value-of select="replace($citation, '^(.*\s|)pp?\.? \d+[\-&#x2013;](\d+).*$', '$2', 's')"/>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:value-of select="replace($citation, '^(.*\s|)pp?\.? (\d+).*$', '$2', 's')"/>
                    </xsl:otherwise>
                  </xsl:choose>
                </data>
              </xsl:if>
              <xsl:for-each select=".//pub-id[@pub-id-type]">
                <xsl:if test="index-of(('pmid', 'pmc', 'doi'), @pub-id-type)">
                  <data key="{@pub-id-type}">
                    <xsl:value-of select="."/>
                  </data>
                </xsl:if>
              </xsl:for-each>
              <xsl:if test="matches($citation, 'https?://[a-z.]+/[A-Za-z\d\-._%/?=&amp;:#]+([^A-Za-z\d_/]|$)')">
                <data key="uri">
                  <xsl:value-of select="replace($citation, '^.*(https?://[a-z.]+/[A-Za-z\d\-._%/?=&amp;:#]+)([^A-Za-z\d_/].*|$)', '$1', 's')"/>
                </data>
              </xsl:if>
            </xsl:when>
            <!--<xsl:when test="$citation[@publication-type='patent' or @citation-type='patent']">-->
            <xsl:when test="$citation/patent">
              <data key="patent_number">
                <xsl:for-each select="$citation/patent">
                  <xsl:value-of select="."/>
                  <xsl:if test="position() != last()">
                    <xsl:text>, </xsl:text>
                  </xsl:if>
                </xsl:for-each>
              </data>
            </xsl:when>
          </xsl:choose>
          <xsl:if test="$citation/pub-id[@pub-id-type='pmid']">
            <data key="pmid">
              <xsl:value-of select="$citation/pub-id[@pub-id-type='pmid']"/>
            </data>
          </xsl:if>
          <xsl:if test="$citation/pub-id[@pub-id-type='doi']">
            <data key="doi">
              <xsl:value-of select="$citation/pub-id[@pub-id-type='doi']"/>
            </data>
          </xsl:if>
          <xsl:for-each select="$citation/(year|month|day|volume|issue|source|fpage|lpage|edition)">
            <data key="{name()}">
              <xsl:value-of select="."/>
            </data>
          </xsl:for-each>
          <data key="title">
            <xsl:choose>
              <xsl:when test="$citation/article-title">
                <xsl:value-of select="$citation/article-title"/>
              </xsl:when>
              <xsl:when test="$citation/source">
                <xsl:value-of select="$citation/source[1]"/>
              </xsl:when>
            </xsl:choose>
          </data>
          <data key="author">
            <xsl:choose>
              <xsl:when test="$citation/person-group/name">
                <xsl:for-each select="$citation/person-group[not(@person-group-type) or index-of(('author','allauthors'), @person-group-type)]/name">
                  <xsl:value-of select="concat(surname, ' ', given-names)"/>
                  <xsl:if test="position() != last()">
                    <xsl:text>, </xsl:text>
                  </xsl:if>
                </xsl:for-each>
              </xsl:when>
              <xsl:when test="$citation/person-group[@person-group-type='allauthors']">
                <xsl:value-of select="$citation/person-group[@person-group-type='allauthors']"/>
              </xsl:when>
              <xsl:when test="$citation/person-group/collab">
                <xsl:for-each select="$citation/person-group/collab">
                  <xsl:value-of select="concat(surname, ' ', given-names)"/>
                  <xsl:if test="position() != last()">
                    <xsl:text>, </xsl:text>
                  </xsl:if>
                </xsl:for-each>
              </xsl:when>
              <xsl:when test="$citation/name">
                <xsl:for-each select="$citation/name">
                  <xsl:value-of select="concat(surname, ' ', given-names)"/>
                  <xsl:if test="position() != last()">
                    <xsl:text>, </xsl:text>
                  </xsl:if>
                </xsl:for-each>
              </xsl:when>
              <xsl:when test="not($citation/name) and not($citation/person-group)"/>
              <xsl:otherwise>
                <xsl:message>Unable to find author for <xsl:value-of select="$cited-id"/></xsl:message>
              </xsl:otherwise>
            </xsl:choose>
          </data>
          <xsl:if test=".//ext-link[@ext-link-type='uri']">
            <data key="uri">
              <xsl:value-of select=".//ext-link[@ext-link-type='uri']/@xlink:href"/>
            </data>
            <xsl:for-each select=".//ext-link[@ext-link-type='uri' and @xlink:href]">
              <!-- For some reason the 'doi:' part of the URL is valid, but not part of the DOI itself. -->
              <xsl:choose>
                <xsl:when test="starts-with(@xlink:href, 'http://dx.doi.org/doi:')">
                  <data key="doi">
                    <xsl:value-of select="substring-after(@xlink:href, 'http://dx.doi.org/doi:')"/>
                  </data>
                </xsl:when>
                <xsl:when test="starts-with(@xlink:href, 'http://dx.doi.org/')">
                  <data key="doi">
                    <xsl:value-of select="substring-after(@xlink:href, 'http://dx.doi.org/')"/>
                  </data>
                </xsl:when>
              </xsl:choose>
            </xsl:for-each>
          </xsl:if>
          <xsl:if test=".//uri">
            <data key="uri">
              <xsl:value-of select=".//uri[1]/@xlink:href"/>
            </data>
          </xsl:if>
        </node>
        <xsl:if test="$citation/source">
            <node type="journal" id="{$id}:reference:{$ref/@id}:journal">
              <data key="nlm_ta">
                  <xsl:value-of select="$citation/source"/>
                </data>
            </node>
            <edge type="journal" source="{$id}:reference:{$ref/@id}" target="{$id}:reference:{$ref/@id}:journal"/>
        </xsl:if>
        <xsl:for-each select="$citation/person-group[@person-group-type]/name">
          <node type="person" id="{$id}:reference:{$ref/@id}:contributor:{position()}">
            <data key="surname">
              <xsl:value-of select="surname"/>
            </data>
            <data key="given-names">
              <xsl:value-of select="given-names"/>
            </data>
          </node>
          <edge type="contributor" source="{$id}:reference:{$ref/@id}" target="{$id}:reference:{$ref/@id}:contributor:{position()}">
            <data key="contrib-type">
              <xsl:value-of select="../@person-group-type"/>
            </data>
          </edge>
        </xsl:for-each>
        <edge type="cites" source="{$id}" target="{$cited-id}">
          <!--
          <data key="paragraphs">
            <xsl:for-each select="/article/body//p[not(ancestor::p) and .//xref[@rid=$ref/@id or index-of(tokenize(@rid, ' '), $ref/@id)]]">
              <xsl:value-of select="count(preceding::p[ancestor::body])+1"/>
              <xsl:if test="position() != last()">
                <xsl:text> </xsl:text>
              </xsl:if>
            </xsl:for-each>
          </data>
          <data key="count">
            <xsl:value-of select="count(/article/body//xref[@rid=$ref/@id or index-of(tokenize(@rid, '\s'), $ref/@id)])"/>
          </data>
          <xsl:choose>
            <xsl:when test="mixed-citation[@publication-type='journal']">
          </xsl:when>
          </xsl:choose>
          -->
          <xsl:variable name="denotions" select="$in-text-reference-pointers//node[@type='in-text-reference-pointer']/edge[@type='denotes' and @target=$cited-id]"/>
          <data key="count">
            <xsl:value-of select="count($denotions)"/>
          </data>
          <data key="paragraphs">
            <xsl:for-each select="$denotions">
              <xsl:value-of select="count(preceding::p)+1"/>
              <xsl:if test="position() != last()">
                <xsl:text> </xsl:text>
              </xsl:if>
            </xsl:for-each>
          </data>
          <!--
        <data key="denote-ids">
            <xsl:for-each select="$denotions/..">
                <xsl:value-of select="@id"/>
              <xsl:if test="position() != last()">
                <xsl:text> </xsl:text>
              </xsl:if>
            </xsl:for-each>
        </data>
        -->
        </edge>
      </xsl:if>
    </xsl:for-each>
    <xsl:call-template name="retraction">
      <xsl:with-param name="article-id" select="$id"/>
    </xsl:call-template>
  </xsl:template>
  <xsl:template match="body">
    <xsl:param name="id"/>
    <xsl:apply-templates select="sec">
      <xsl:with-param name="id" select="$id"/>
    </xsl:apply-templates>
  </xsl:template>
  <xsl:template match="sec">
    <xsl:param name="id"/>
    <node type="section">
      <data key="title">
        <xsl:value-of select="title[1]/text()"/>
      </data>
      <xsl:if test="@sec-type">
        <data key="sec-type">
          <xsl:value-of select="@sec-type"/>
        </data>
      </xsl:if>
      <xsl:apply-templates select="*[name() != 'title']">
        <xsl:with-param name="id" select="$id"/>
      </xsl:apply-templates>
    </node>
  </xsl:template>
  <xsl:template match="p">
    <xsl:param name="id"/>
    <p n="{count(preceding-sibling::p)+1}" id="{$id}:paragraph:{count(preceding::p[ancestor::body])+1}">
      <xsl:apply-templates select="node()">
        <xsl:with-param name="id" select="$id"/>
      </xsl:apply-templates>
      <data key="index">
        <xsl:value-of select="count(preceding::p[ancestor::body])+1"/>
      </data>
    </p>
  </xsl:template>
  <xsl:template match="xref[@ref-type='bibr']">
    <xsl:param name="id"/>
    <xsl:variable name="prev" select="preceding-sibling::node()[position()&lt;3]"/>
    <xsl:variable name="next" select="following-sibling::node()[position()&lt;3]"/>
    <xsl:variable name="seps" select="('-', '&#x2013;')"/>
    <xsl:if test="not($prev[2] and index-of($seps, $prev[2]) and name($prev[1])='xref' and $prev[1]/@ref-type='bibr')">
      <node type="in-text-reference-pointer" id="{$id}:in-text-reference-pointer:{generate-id()}">
        <data key="paragraph">
          <xsl:value-of select="count(preceding::p[ancestor::body])+1"/>
        </data>
        <xsl:choose>
          <xsl:when test="$next[2] and index-of($seps, $next[1]) and name($next[2])='xref' and $next[2]/@ref-type='bibr'">
            <xsl:variable name="rid-from" select="@rid"/>
            <xsl:variable name="rid-to" select="$next[2]/@rid"/>
            <data key="text">
              <xsl:value-of select=".//text()"/>
              <xsl:value-of select="$next[1]"/>
              <xsl:value-of select="$next[2]//text()"/>
            </data>
            <xsl:variable name="elem-from" select="/article/back/ref-list/ref[@id=$rid-from]"/>
            <xsl:variable name="elem-to" select="/article/back/ref-list/ref[@id=$rid-to]"/>
            <xsl:choose>
              <!-- Sometimes the range bounds are in the wrong order -->
              <xsl:when test="$elem-from and $elem-to and exists(index-of($elem-from/following::*, $elem-to))">
                <xsl:call-template name="reference-range">
                  <xsl:with-param name="article-id" select="$id"/>
                  <xsl:with-param name="ref" select="/article/back/ref-list/ref[@id=$rid-from]"/>
                  <xsl:with-param name="until" select="$rid-to"/>
                </xsl:call-template>
              </xsl:when>
              <xsl:otherwise>
                <warning type="invalid-ref-pointer-range">Invalid in-text reference pointer range</warning>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:when>
          <xsl:otherwise>
            <data key="text">
              <xsl:value-of select=".//text()"/>
            </data>
            <xsl:for-each select="tokenize(@rid, '\s+')">
              <edge type="denotes" target="{$id}:reference:{.}"/>
            </xsl:for-each>
          </xsl:otherwise>
        </xsl:choose>
      </node>
    </xsl:if>
  </xsl:template>
  <xsl:template match="node()">
    <xsl:param name="id"/>
    <xsl:copy>
      <xsl:apply-templates select="node()">
        <xsl:with-param name="id" select="$id"/>
      </xsl:apply-templates>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="fig|title|caption|label|graphic">
    <xsl:param name="id"/>
    <xsl:apply-templates select="node()">
      <xsl:with-param name="id" select="$id"/>
    </xsl:apply-templates>
  </xsl:template>
  <xsl:template name="reference-range">
    <xsl:param name="article-id"/>
    <xsl:param name="ref"/>
    <xsl:param name="until"/>
    <edge type="denotes" target="{$article-id}:reference:{$ref/@id}"/>
    <xsl:variable name="following" select="$ref/following-sibling::ref[1]"/>
    <xsl:if test="not($ref/@id=$until) and $following">
      <xsl:call-template name="reference-range">
        <xsl:with-param name="article-id" select="$article-id"/>
        <xsl:with-param name="ref" select="$following"/>
        <xsl:with-param name="until" select="$until"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>
  <xsl:template name="retraction">
    <xsl:param name="article-id"/>
    <xsl:for-each select="front/article-meta/related-article[@related-article-type='retracted-article']">
      <node type="article" id="{$article-id}:retracted:{position()}">
        <data key="provenance">pmc_oa_retraction</data>
        <data key="retracted">true</data>
        <data key="fabio_type">Expression</data>
        <xsl:choose>
          <xsl:when test="@ext-link-type='pubmed'">
            <data key="pmid">
              <xsl:value-of select="@xlink:href"/>
            </data>
          </xsl:when>
          <xsl:when test="@ext-link-type='uri' and starts-with(@xlink:href, 'info:doi/')">
            <data key="doi">
              <xsl:value-of select="substring-after(@xlink:href, 'info:doi/')"/>
            </data>
          </xsl:when>
          <xsl:when test="@ext-link-type='uri' and starts-with(@xlink:href, 'info:doi/')">
            <data key="doi">
              <xsl:value-of select="substring-after(@xlink:href, 'info:doi/')"/>
            </data>
          </xsl:when>
          <xsl:when test="@xlink:href">
            <data key="uri">
              <xsl:value-of select="@xlink:href"/>
            </data>
          </xsl:when>
          <xsl:otherwise>
            <!--
            <data key="uri">
              <xsl:value-of select="@xlink:href"/>
            </data>
            -->
            <xsl:message terminate="yes">Unexpected @ext-link-type</xsl:message>
            <warning type="unexpected-ext-link-type">Unexpected @ext-link-type</warning>
          </xsl:otherwise>
        </xsl:choose>
      </node>
      <edge type="retracts" source="{$article-id}" target="{$article-id}:retracted:{position()}"/>
    </xsl:for-each>
  </xsl:template>
  <xsl:template name="verbatim_">
    <xsl:choose>
      <xsl:when test="name()='label'"/>
      <xsl:when test="self::text()">
        <xsl:value-of select="replace(., '\s+', ' ')"/>
        <xsl:text> </xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:for-each select="node()">
          <xsl:call-template name="verbatim_"/>
        </xsl:for-each>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template name="verbatim">
    <xsl:variable name="text">
      <xsl:call-template name="verbatim_"/>
    </xsl:variable>
    <xsl:value-of select="normalize-space($text)"/>
  </xsl:template>
</xsl:stylesheet>
