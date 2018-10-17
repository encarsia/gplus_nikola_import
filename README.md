This plugin does a rough import of a Google+ stream as provided by [Google Takeout](http://google.com/takeout/).

Videos work, content in general works, attached images may or may not work depending on source (but mostly work).

The output is html, and there's little to no configuration done in the resulting site.

## IMPORTANT

As of today (October 2018) this mostly rewritten plugin inspired by the [original import plugin](https://plugins.getnikola.com/v7/import_gplus/) works until Google plays around again.

If you consider to release this into the wilderness, keep in mind that the import includes not only public but also private and community shares.

Enjoy.

## Usage

 * Download Google Takeout as zip file if you use umlauts. There may be encoding issues. Choose the HTML output option.
 * Extract the dump file, merge parts if you have multiple files.
 * Additional Python package requirement: [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/).
 * Copy the extracted plugin archive into the ``plugins`` folder of an existing Nikola site.
    * Chances are that there isn't a ``plugins`` folder yet. Create it.
    * The plugin will create a new site in a subfolder so there won't be any contaminations with actual data.
    * If you are unsure or don't want that you can easily initiate an empty site for the purpose: ``$ nikola init dummy_site``.
 * Open ``plugins/import_gplus.py``
    * adapt folder names to your language settings
    * adapt share status strings if neccesary (this will affect the category assigment)
    * posts that are not shared to public/"My circles"/"My extended circles"/communities/collections will be classified as other/private; if you set the ``import_private`` to *False* these posts will not be imported 
 * Run ``$ nikola import_gplus path/to/takeout_folder``
 * The plugin inits a new Nikola site called ``new_site`` (no shit, Sherlock), you have to change into that directory to run build commands: ``$ cd new_site``.
 * Building the site can take long and possibly wake up your fans. You may want to test the output with a fraction of the available data.
 * Although the output should work with any theme, it looks quite nice with [hyde](https://themes.getnikola.com/v7/hyde/); hpstr is okay, too.
   Install hyde: ``$ nikola theme -i hyde``
 * Consider to copy the included ``custom.css`` into the ``themes/THEME_NAME/assets/css`` directory for an even better result.
 * Tweaking ``conf.py``:
  * set theme: ``THEME = "hyde"``
  * disable RSS: ``GENERATE_RSS = False``
 * Build the site: ``$ nikola build``
 * Watch the site on localhost:8000: ``$ nikola serve``
