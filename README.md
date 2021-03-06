This plugin does a import of a Google+ stream as provided by [Google Takeout](http://google.com/takeout/).

Videos and attached images work, content in general works.

The output is html, and there's little to no configuration done in the resulting site.

## IMPORTANT

As of today (February 2019) this mostly rewritten plugin inspired by the [original import plugin](https://plugins.getnikola.com/v7/import_gplus/). Google confirmed the G+ shutdown on April 2nd 2019 so there will be deadlinks to deleted profiles etc., links to the original posts have already been removed.

If you consider to release this into the wilderness, keep in mind that the import includes not only public but also private and community shares. There are some filter options available (see below).

Enjoy.

## USAGE

 * Download Google Takeout as zip file if you use umlauts or other special characters or just to be sure. There may be encoding issues. Choose the HTML output option.
 * Extract the dump file, merge parts if you have multiple files.
 * Additional Python package requirement: [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/).
 * Copy the extracted plugin archive folder into the ``plugins`` folder of an existing Nikola site.
    * Chances are that there isn't a ``plugins`` folder yet. Create it.
    * The plugin will create a new site in a subfolder so there won't be any contaminations with actual data.
    * If you are unsure or don't want that you can easily initiate an empty site for the purpose: ``$ nikola init dummy_site``.
 * Open ``plugins/gplus_nikola_plugin/config.yaml``.  You may want run the plugin with the option ``-s`` to help you with editing (this will not import anything).

    * Adapt folder names of the ``gto`` section to your language settings (German nomenclature is predefined).
    * Adapt share status strings in the ``shared`` section if neccesary (this will affect the category assignment).
    * Some content filter options are available in the ``import`` section:

      * Posts that are not shared to public/"My circles"/"My extended circles"/communities/collections will be classified as other/private; if you set the ``private`` variable to *False* these posts will not be imported. If set to *True* you can exclude posts to the circles you list in ``circle_filter``.
      * Community shares are not distinguished between public and closed/private communities; if you set the ``com`` variable to *False*, community posts will not be imported. If set to *True* you can still exclude communities listed in ``com_filter``.

    * Set ``watermark`` to *True* to mark images with a horizontal text line (``watermark_text``).

 * Run ``$ nikola import_gplus_html path/to/takeout_folder``.
 * The plugin inits a new Nikola site called ``new_site``. You have to change into that directory to run build commands: ``$ cd new_site``.
 * You can specify a custom output folder name by using the option ``-o``:
   ``$ nikola import_gplus_html -o gplus_archive path/to/takeout_folder``.
 * Building the site can take some time. In case of impatience you may want to test the output with a fraction of the available data.
 * Although the output should work with any theme, it looks quite nice with [hyde](https://themes.getnikola.com/v7/hyde/); hpstr is okay, too.
   Install hyde: ``$ nikola theme -i hyde``.
 * Consider to copy the included ``custom.css`` into the ``themes/THEME_NAME/assets/css`` directory for an even better result.
 * Tweaking ``conf.py``:
   * images:
        * use watermarked images: ``IMAGE_FOLDERS = {"images_wm": "images"}``
        * reduce file size:
            * width: ``MAX_IMAGE_SIZE = 500`` (default 1280)
            * thumbnail: ``IMAGE_THUMBNAIL_SIZE = 200`` (default 400)
   * set theme: ``THEME = "hyde"``
   * disable RSS: ``GENERATE_RSS = False``
   * set link(s) to your main presence or profiles: ``NAVIGATION_LINKS``
   * do not deliver sources:
      * ``SHOW_SOURCELINK = False``
      * ``COPY_SOURCES = False``
   * number of posts per index page: ``INDEX_DISPLAY_POST_COUNT = 20`` (default 10)
   * disable generation of a robots.txt: ``DISABLED_PLUGINS = ["robots"]``
 * Build the site: ``$ nikola build``.
 * Watch the site on localhost:8000: ``$ nikola serve``.

## KNOWN ISSUES TO DEAL WITH WHEN I HAVE THE TIME

 * Non-static image files (gif/mp4...) are not copied to the *image_wm* folder, you may copy these manually.
 * You can delete all thumbnail files in the new created site's image folder because these are not used. This will save you a lot of disc space.
 * Now that the purge has begun, there will be endless amounts of internal deadlinks

