---
layout: archive
title: "Publications"
permalink: /publications/
author_profile: true
---

{% include base_path %}

{% if author.googlescholar %}
  You can also find my articles on <u><a href="{{ author.googlescholar }}">my Google Scholar profile</a></u>.
{% endif %}

{% comment %}
  This list is generated from _bibliography/papers.bib -- do not edit the
  entries by hand.  See markdown_generator/README.md.

  Each section is "<pubtype>[+<pubtype>...]|<heading>"; a section may gather
  more than one pubtype.
{% endcomment %}

{% assign sections = "journal|Journal Articles,conference|Conference and Workshop Papers,preprint+other|Preprints and Others,thesis|Theses" | split: "," %}
{% assign publications = site.publications | sort: "date" | reverse %}

{% for section in sections %}
{% assign parts = section | split: "|" %}
{% assign keys = parts[0] | split: "+" %}
{% assign heading = parts[1] %}
{% assign group = "" | split: "," %}
{% for key in keys %}
{% assign subset = publications | where: "pubtype", key %}
{% assign group = group | concat: subset %}
{% endfor %}
{% if group.size > 0 %}
{% assign group = group | sort: "date" | reverse %}
<h2 id="{{ keys[0] }}" class="pub-section">{{ heading }}</h2>
<div class="pub-list">
{% for post in group %}{% include archive-single-publication.html %}{% endfor %}
</div>
{% endif %}
{% endfor %}
