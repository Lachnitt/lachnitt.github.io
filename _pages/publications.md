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
{% endcomment %}

{% assign sections = "journal|Journal Articles,conference|Conference and Workshop Papers,preprint|Preprints,thesis|Theses,other|Other" | split: "," %}
{% assign publications = site.publications | sort: "date" | reverse %}

{% for section in sections %}
{% assign parts = section | split: "|" %}
{% assign key = parts[0] %}
{% assign heading = parts[1] %}
{% assign group = publications | where: "pubtype", key %}
{% if group.size > 0 %}
<h2 id="{{ key }}" class="pub-section">{{ heading }}</h2>
<div class="pub-list">
{% for post in group %}{% include archive-single-publication.html %}{% endfor %}
</div>
{% endif %}
{% endfor %}
