<?xml version="1.0"?>
<xsl:stylesheet xmlns:cito="http://purl.org/spar/cito/" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:org="http://www.w3.org/ns/org#" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:skos="http://www.w3.org/2004/02/skos/core#" xmlns:foaf="http://xmlns.com/foaf/0.1/" xmlns:fabio="http://purl.org/spar/fabio/" xmlns:frbr="http://purl.org/vocab/frbr/core#" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xlink="http://www.w3.org/1999/xlink" version="2.0">
  <xsl:output indent="yes"/>
  <xsl:template match="/">
    <graphml xmlns="http://graphml.graphdrawing.org/xmlns">
      <key attr.type="string" id="_xml_container" for="node" attr.name="_xml_container"/>
      <key attr.type="string" id="title" for="node" attr.name="title"/>
      <key attr.type="string" id="nlmxml" for="node" attr.name="nlmxml"/>
      <key attr.type="string" id="ctype" for="node" attr.name="ctype"/>
      <key attr.type="string" id="month" for="node" attr.name="month"/>
      <key attr.type="string" id="volume" for="node" attr.name="volume"/>
      <key attr.type="string" id="source" for="node" attr.name="source"/>
      <key attr.type="string" id="year" for="node" attr.name="year"/>
      <key attr.type="string" id="publisher-name" for="node" attr.name="publisher-name"/>
      <key attr.type="string" id="issue" for="node" attr.name="issue"/>
      <graph edgedefault="directed">
        <xsl:apply-templates select="*"/>
      </graph>
    </graphml>
  </xsl:template>
  <xsl:template name="article-id">
    <xsl:variable name="ids" select="front/article-meta/article-id"/>
    <xsl:choose>
      <xsl:when test="$ids[@pub-id-type='pmid']">
        <xsl:value-of select="concat('pmid:', $ids[@pub-id-type='pmid'])"/>
      </xsl:when>
      <xsl:when test="$ids[@pub-id-type='pmc']">
        <xsl:value-of select="concat('pmc:', $ids[@pub-id-type='pmc'])"/>
      </xsl:when>
      <xsl:when test="$ids[@pub-id-type='doi']">
        <xsl:value-of select="concat('doi:', $ids[@pub-id-type='doi'])"/>
      </xsl:when>
      <xsl:otherwise>something</xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template match="article">
    <xsl:variable name="id">
      <xsl:call-template name="article-id"/>
    </xsl:variable>
    <node id="{$id}">
      <data key="_xml_container">article</data>
      <data key="type">journal</data>
      <data key="title">
        <xsl:value-of select="front/article-meta/title-group/article-title"/>
      </data>
      <data key="nlmxml"/>
      <data key="ctype"/>
      <xsl:variable name="date">
        <xsl:choose>
          <xsl:when test="front/article-meta/pub-date[@pub-type='ppub']">
            <xsl:copy-of select="front/article-meta/pub-date[@pub-type='ppub']"/>
          </xsl:when>
          <xsl:when test="front/article-meta/pub-date[@pub-type='epub']">
            <xsl:copy-of select="front/article-meta/pub-date[@pub-type='epub']"/>
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
      <xsl:for-each select="front/article-meta/(volume|issue|fpage|lpage)">
        <data key="{name()}">
          <xsl:value-of select="."/>
        </data>
      </xsl:for-each>
      <xsl:for-each select="front/article-meta/article-id">
        <xsl:if test="index-of(('pmc', 'pmid', 'doi'), @pub-id-type)">
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
    </node>
    <xsl:for-each select="back/ref-list/ref">
      <xsl:variable name="ref" select="."/>
      <node name="{$id}:{@id}">
        <data key="_xml_container">
          <xsl:value-of select="*[position()=last()]/name()"/>
        </data>
        <data key="type">
          <xsl:choose>
            <xsl:when test="*[position()=last()]/@publication-type">
              <xsl:value-of select="*[position()=last()]/@publication-type"/>
            </xsl:when>
            <xsl:when test="*[position()=last()]/@citation-type">
              <xsl:value-of select="*[position()=last()]/@citation-type"/>
            </xsl:when>
          </xsl:choose>
        </data>
        <xsl:choose>
          <xsl:when test="(citation|element-citation|mixed-citation)[@publication-type='other' or @citation-type='other']">
              <xsl:variable name="citation" select="(citation|element-citation|mixed-citation)[@publication-type='other' or @citation-type='other']"/>
              <data key="full-citation">
                  <xsl:value-of select="$citation"/>
              </data>
            <xsl:if test="matches($citation, '(^|\s)10\.\d+/[\d.a-zA-Z\-]+')">
              <data key="doi">
                <xsl:value-of select="replace($citation, '^(.*\s|)(10\.\d+/[\d.a-zA-Z\-]*[\da-zA-Z]).*$', '$2')"/>
              </data>
            </xsl:if>
            <xsl:if test="matches($citation, '(^|\s)[12]\d{3}([^\d]|$)')">
              <data key="year">
                <xsl:value-of select="replace($citation, '^(.*\s|)([12]\d{3})($|[^\d].*$)', '$2')"/>
              </data>
            </xsl:if>
            <data key="author">
              <xsl:value-of select="replace($citation, '^(((([A-Z]\.)+\s)|[A-Z][^.]+|[^A-Z.]+)+?)\..*$', '$1')"/>
              <!-- Looks like zero-width negative look-behinds aren't supported in XSL -->
              <!--<xsl:value-of select="replace(mixed-citation, '^(.*?)(?&lt;!\.[A-Z])\..*$', '$1')"/>-->
            </data>
            <xsl:if test="matches($citation, '(^|\s)pp?\.? \d+')">
              <data key="fpage">
                <xsl:value-of select="replace($citation, '^(.*\s|)pp?\.? (\d+).*$', '$2')"/>
              </data>
              <data key="lpage">
                <xsl:choose>
                  <xsl:when test="matches($citation, '\spp?\.? \d+[\-&#x2013;]\d+')">
                    <xsl:value-of select="replace($citation, '^(.*\s|)pp?\.? \d+[\-&#x2013;](\d+).*$', '$2')"/>
                  </xsl:when>
                  <xsl:otherwise>
                    <xsl:value-of select="replace($citation, '^(.*\s|)pp?\.? (\d+).*$', '$2')"/>
                  </xsl:otherwise>
                </xsl:choose>
              </data>
            </xsl:if>
          </xsl:when>
          <xsl:when test="(citation|element-citation|mixed-citation)[@publication-type='book' or @citation-type='book']">
            <xsl:variable name="citation" select="(citation|element-citation|mixed-citation)[@publication-type='book' or @citation-type='book']"/>
            <data name="title">
              <xsl:choose>
                <xsl:when test="$citation/article-title">
                  <xsl:value-of select="$citation/article-title"/>
                </xsl:when>
                <xsl:when test="$citation/source">
                  <xsl:value-of select="$citation/source[1]"/>
                </xsl:when>
              </xsl:choose>
            </data>
            <data name="year">
              <xsl:value-of select="$citation/year"/>
            </data>
            <data name="author">
              <xsl:for-each select="$citation/person-group[@person-group-type='author']/name">
                <xsl:value-of select="concat(surname, ' ', given-names)"/>
                <xsl:if test="position() != last()">
                  <xsl:text>, </xsl:text>
                </xsl:if>
              </xsl:for-each>
            </data>
            <data name="publisher-name">
                <xsl:value-of select="$citation/publisher-name"/>
            </data>
            <data name="edition">
                <xsl:value-of select="$citation/edition"/>
            </data>
          </xsl:when>
          <xsl:when test="(citation|element-citation|mixed-citation)[@publication-type='journal' or @citation-type='journal']">
            <xsl:variable name="citation" select="(citation|element-citation|mixed-citation)[@publication-type='journal' or @citation-type='journal']"/>
            <xsl:for-each select="$citation/(year|month|day|volume|issue|source|fpage|lpage)">
              <data key="{name()}">
                <xsl:value-of select="."/>
              </data>
            </xsl:for-each>
            <data key="title">
              <xsl:value-of select="$citation/article-title"/>
            </data>
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
            <data name="author">
              <xsl:for-each select="$citation/person-group[@person-group-type='author']/name">
                <xsl:value-of select="concat(surname, ' ', given-names)"/>
                <xsl:if test="position() != last()">
                  <xsl:text>, </xsl:text>
                </xsl:if>
              </xsl:for-each>
            </data>
          </xsl:when>
        </xsl:choose>
        <xsl:if test=".//ext-link[@ext-link-type='uri']">
          <data key="uri">
            <xsl:value-of select=".//ext-link[@ext-link-type='uri']/@xlink:href"/>
          </data>
          <xsl:if test="starts-with(.//ext-link[@ext-link-type='uri']/@xlink:href, 'http://dx.doi.org/')">
            <data key="doi">
              <xsl:value-of select="substring-after(.//ext-link[@ext-link-type='uri']/@xlink:href, 'http://dx.doi.org/')"/>
            </data>
          </xsl:if>
        </xsl:if>
      </node>
      <edge source="{$id}" target="{$id}:{@id}">
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
      </edge>
    </xsl:for-each>
  </xsl:template>
</xsl:stylesheet>
