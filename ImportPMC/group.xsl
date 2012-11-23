<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:mml="http://www.w3.org/1998/Math/MathML" version="2.0">
  <xsl:output indent="yes"/>
  <xsl:template match="/">
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template match="*">
    <xsl:copy>
      <xsl:copy-of select="@*"/>
      <xsl:for-each-group select="* | text()" group-adjacent="boolean(self::xref[@ref-type='bibr'] or index-of((',', '-', '&#x2013;'), .))">
        <xsl:variable name="g" select="current-group()"/>
        <xsl:choose>
          <xsl:when test="$g[self::xref/@ref-type='bibr']">
            <xsl:call-template name="xref-group">
              <xsl:with-param name="group" select="$g"/>
            </xsl:call-template>
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates select="$g"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:for-each-group>
    </xsl:copy>
  </xsl:template>
  <xsl:template name="xref-group">
    <xsl:param name="group"/>
    <group>
      <xsl:apply-templates select="$group"/>
      <xsl:for-each select="$group">
        <xsl:choose>
          <xsl:when test=". = ','"/>
          <xsl:when test="index-of(('-', '&#x2013;'), .)">
            <xsl:variable name="rid-from" select="preceding-sibling::xref[1]/@rid"/>
            <xsl:variable name="rid-to" select="following-sibling::xref[1]/@rid"/>
            <xsl:variable name="elem-from" select="/article/back/ref-list/ref[@id=$rid-from]"/>
            <xsl:variable name="elem-to" select="/article/back/ref-list/ref[@id=$rid-to]"/>
            <xsl:choose>
              <!-- Sometimes the range bounds are in the wrong order -->
              <xsl:when test="$elem-from and $elem-to and exists(index-of($elem-from/following::*, $elem-to))">
                <xsl:call-template name="xref-range">
                  <xsl:with-param name="starting-from" select="/article/back/ref-list/ref[@id=$rid-from]/following-sibling::ref[1]"/>
                  <xsl:with-param name="upto-but-not-including" select="$rid-to"/>
                </xsl:call-template>
              </xsl:when>
              <xsl:otherwise>
                <warning type="invalid-ref-pointer-range">Invalid in-text reference pointer range</warning>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:when>
          <xsl:otherwise>
            <xsl:for-each select="tokenize(@rid, '\s')">
              <denotes n="{.}"/>
            </xsl:for-each>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:for-each>
      <text>
        <xsl:for-each select="$group">
          <xsl:value-of select="."/>
        </xsl:for-each>
      </text>
      <xpath>
        <xsl:text>//xref[@ref-type='bibr' and @rid='</xsl:text>
        <xsl:value-of select="$group[1]/@rid"/>
        <xsl:text>'][</xsl:text>
        <xsl:value-of select="1+count(preceding::xref[@rid=$group[1]/@rid])"/>
        <xsl:text>]</xsl:text>
        <xsl:if test="count($group) &gt; 1">
          <xsl:text>/preceding::node()[1]/following::node()[position() &lt;= </xsl:text>
          <xsl:value-of select="count($group)"/>
          <xsl:text>]</xsl:text>
        </xsl:if>
      </xpath>
    </group>
  </xsl:template>
  <xsl:template name="xref-range">
    <xsl:param name="starting-from"/>
    <xsl:param name="upto-but-not-including"/>
    <xsl:variable name="following" select="$starting-from/following-sibling::ref[1]"/>
    <denotes n="{$starting-from/@id}"/>
    <xsl:if test="$following/@id != $upto-but-not-including">
      <xsl:call-template name="xref-range">
        <xsl:with-param name="starting-from" select="$following"/>
        <xsl:with-param name="upto-but-not-including" select="$upto-but-not-including"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>
  <xsl:template name="node-path">
    <xsl:param name="first"/>
    <xsl:param name="last"/>
    <xsl:for-each select="$first/ancestor-or-self::*">
      <xsl:text>/</xsl:text>
      <xsl:value-of select="name(.)"/>
      <xsl:text>[</xsl:text>
      <xsl:value-of select="1+count(preceding-sibling::*[name(current()) = name(.)])"/>
      <xsl:choose>
        <xsl:when test="position()=last() and $last">
          <xsl:text>-</xsl:text>
          <xsl:value-of select="1+count($last/preceding-sibling::*[name(current()) = name($last)])"/>
        </xsl:when>
        <xsl:otherwise>
          </xsl:otherwise>
      </xsl:choose>
      <xsl:text>]</xsl:text>
    </xsl:for-each>
  </xsl:template>
</xsl:stylesheet>
