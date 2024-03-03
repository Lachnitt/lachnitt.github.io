from pybtex.database.input import bibtex
parser = bibtex.Parser()
publications = parser.parse_file('publications/proceedings.bib')


html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;"
    }

def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)

import os
for bib_key in bib_data.entries.keys():
    bib_item = bib_data.entries[bib_key]
    
    md_filename = str(bib_key) + ".md"
    html_filename = str(bib_key)
    year = bib_item.fields['year']
    title = bib_item.fields['year']
    abstract = bib_item.fields['abstract']
    title = bib_item.fields['title']

    ## YAML variables
    
    md = "---\ntitle: \""   + title + '"\n'
    
    md += """collection: publications"""
    
    md += """\npermalink: /publication/""" + html_filename
    
    if len(str(abstract)) > 5:
        md += "\nexcerpt: '" + html_escape(abstract) + "'"
    
    md += "\ndate: " + str(year) 
    
    md += "\nvenue: '" + html_escape(item.venue) + "'"
    
    if len(str(item.paper_url)) > 5:
        md += "\npaperurl: '" + item.paper_url + "'"
    
    md += "\ncitation: '" +  "'"
    
    md += "\n---"
    
    ## Markdown description for individual page
    
    if len(str(item.paper_url)) > 5:
        md += "\n\n<a href='" + "'>Download paper here</a>\n" 
        
    if len(str(item.excerpt)) > 5:
        md += "\n" + "\n"
            
    md_filename = os.path.basename(md_filename)
       
    with open("../_publications/mds/" + md_filename, 'w') as f:
        f.write(md)


