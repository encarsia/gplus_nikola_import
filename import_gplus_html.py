# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import os
import shutil

try:
    import bs4
except ModuleNotFoundError:
    raise

from nikola.plugin_categories import Command
from nikola import utils
from nikola.utils import req_missing, get_logger
from nikola.plugins.basic_import import ImportMixin
from nikola.plugins.command.init import SAMPLE_CONF, prepare_config

LOGGER = get_logger("import_gplus")

# ################### CONFIGURATION ##################
# you may have to adapt strings according to your language

# Google Takeout folder structure

# Takeout/
# ├── +1/
# ├── Google+ stream/
# |   ├── Posts/
# |   ├── Photos/
# |   |   ├── Photos of posts/
# |   |   └── Photos of polls/
# |   ├── Activities/
# |   ├── Collections/
# |   └── Events/
# └── index.html

gto_root = "Takeout"
gto_plus1 = "+1"
gto_stream = "Stream in Google+"
gto_posts = "Beiträge"
gto_photos = "Fotos"
gto_photos_posts = "Fotos von Beiträgen"
gto_photos_polls = "Umfragefotos"
gto_activity = "Aktivitätsprotokoll"
gto_collections = "Sammlungen"
gto_events = "Veranstaltungen"

# Share status

share_public = "Geteilt mit: Öffentlich"
share_circles = "Geteilt mit: Meine Kreise"
share_extcircles = "Geteilt mit: Meine erweiterten Kreise"
share_other = "Andere"

share_com = "Shared to the community "
share_coll = "Shared to the collection "

# exclude posts that are none of the above which are shared with
# certain circles or persons/profiles so probably private posts
# (considered as "Andere"/"Other")
import_private = True

# exclude posts to communities as they may be closed/private
import_com = True

# ##############################################################

class CommandImportGplus(Command, ImportMixin):
    """Import a Google+ dump."""

    name = "import_gplus"
    needs_config = True
    doc_usage = "[options] extracted_dump_file_folder"
    doc_purpose = "import a Google+ dump"
    cmd_options = ImportMixin.cmd_options

    def _execute(self, options, args):
        '''
            Import Google+ dump
        '''

        if not args:
            print(self.help())
            return

        options["foldername"] = args[0]
        self.export_folder = options["foldername"]
        self.output_folder = options["output_folder"]
        self.import_into_existing_site = False
        self.url_map = {}

        # path to HTML formatted post files
        post_path = os.path.join(self.export_folder,
                                 gto_root,
                                 gto_stream,
                                 gto_posts)
        
        # collect all files
        files = [f for f in os.listdir(os.path.join(post_path)) if os.path.isfile(os.path.join(post_path, f))]

        # filter HTML files
        html_files = [f for f in files if f.endswith(".html")]
        LOGGER.info("{} posts ready for import".format(len(html_files)))
        
        # init new Nikola site "new_site", edit conf.py to your needs
        # change into this folder for the for build process
        self.context = self.populate_context(html_files, post_path)
        conf_template = self.generate_base_site()
        self.write_configuration(self.get_configuration_output_path(), conf_template.render(**prepare_config(self.context)))
        self.import_posts(html_files, post_path)
        
        # In the Takeout archive photos are linked to the main working
        # directory although they do not necessarily exist there (Hello
        # deadlinks!). The image files are spread to several folders.

        # All archive photos will be copied to the "images" folder.
        try:
            os.makedirs(os.path.join(self.output_folder, "images"))
            LOGGER.debug("Image folder created.")
        except:
            pass

        for root, dirs, files in os.walk(os.path.join(self.export_folder, gto_root)):
            for f in files:
                if (f.lower().endswith(".jpg") or \
                        f.lower().endswith(".jpeg") or \
                        f.lower().endswith(".png") or \
                        f.lower().endswith(".m4v") or \
                        f.lower().endswith(".mp4") or \
                        f.lower().endswith(".gif")): # 'Year in photos' 
                    if not os.path.isfile(os.path.join(self.output_folder, "images",f)):
                        if "=" in f:
                            new_f = f.replace("=", "--")
                            shutil.move(os.path.join(root, f), os.path.join(self.output_folder, "images", new_f))
                        else:
                            shutil.copy2(os.path.join(root, f), os.path.join(self.output_folder, "images"))
                        LOGGER.debug("{} copied to Nikola image folder.".format(f))
                    else:
                        LOGGER.info("Skipping {}. File already exists".format(f))
        
    @staticmethod
    def populate_context(names, path):
        # We don't get much data here
        context = SAMPLE_CONF.copy()
        context["DEFAULT_LANG"] = "de"
        context["BLOG_DESCRIPTION"] = ""
        context["SITE_URL"] = "http://localhost:8000/"
        context["BLOG_EMAIL"] = ""
        context["BLOG_TITLE"] = "Static G+ stream archive"

        # Get any random post, all have the same data
        with open(os.path.join(path, names[0])) as f:
            soup = bs4.BeautifulSoup(f, "html.parser")
        
        context["BLOG_AUTHOR"] = soup.find("a", "author").text

        context["POSTS"] = '''(
            ("posts/*.html", "posts", "post.tmpl"),
            ("posts/*.rst", "posts", "post.tmpl"),
        )'''
        
        context["COMPILERS"] = '''{
        "rest": ('.txt', '.rst'),
        "html": ('.html', '.htm')
        }
        '''
        
        profile_url = soup.find("a").get("href")
        context["NAVIGATION_LINKS"] = '''{{
    DEFAULT_LANG: (
        ("{}", "G+ profile"),
        ("/archive.html", "Archives"),
        ("/categories/index.html", "Share status"),
    ),
}}'''.format(profile_url)
        
        # Disable comments
        context["COMMENT_SYSTEM"] = ""
        
        return context

    def import_posts(self, names, path):
        """Import all posts."""
        self.out_folder = "posts"

        for name in names:
            with open(os.path.join(path, name)) as f:
                soup = bs4.BeautifulSoup(f, "html.parser")
                
            tags = []
            
            title_string = str(soup.title.string)
            title = self.prettify_title(title_string)
            
            # post date is the 2nd link on the page
            post_date = soup.find_all("a")[1].text
            
            # receive link from post date
            post_link = soup.find_all("a")[1].get("href")
            
            # collect complete post content
            post_text = soup.find("div", "main-content")
            link_embed = soup.find("a", "link-embed")
            media_link = soup.find_all("a", "media-link")
            album = soup.find("div", "album")
            video = soup.find("div", "video-placeholder")
            visibility = soup.find("div", "visibility")
            vis_link = soup.find("div", "visibility").find("a")
            activity = soup.find("div", "post-activity")
            comments = soup.find("div", "comments")
            
            # turn visibility status into category
            # get name of 2nd item of visibility list which is link to com/coll
            if vis_link:
                try:
                    vis_link = vis_link.contents[0]
                except IndexError:
                    if "communities" in vis_link.get("href"):
                        vis_link = "Deleted community"
                    elif "collection" in vis_link.get("href"):
                        vis_link = "Deleted collection"  
                    else:
                        vis_link = "Deleted profile"
            
            vis = visibility.contents[0]
            if (vis.startswith(share_public) or \
                    vis.startswith(share_circles) or \
                    vis.startswith(share_extcircles)):
                cat = vis.split(",")[0] # get rid of comma if there is any
            elif vis in share_com:
                if import_com is False:
                    LOGGER.warning("Community post will be ignored: {}".format(link))
                    continue
                cat = "{}\"{}\"".format(vis, vis_link)
            elif vis in share_coll:
                cat = "{}\"{}\"".format(vis, vis_link)
            else:
                if import_private is False:
                    LOGGER.warning("Private post will be ignored: {}".format(link))
                    continue
                cat = share_other
            
            if video is not None:
                tags.append("video")
            
            for link in media_link:
                # link to image in image folder if not external link
                if not link["href"].startswith("http"):
                    filename = link["href"]
                    if "=" in filename:
                        filename = filename.replace("=", "--")
                    try:
                        link["href"] = os.path.join("..", "..", "images", filename)
                        tags.append("photo")
                    except TypeError:
                        LOGGER.warning("No href attribute to convert link destination ({})".format(link))
                    try:
                        link.img["src"] = os.path.join("..", "..", "images", filename)
                    except TypeError:
                        LOGGER.warning("No src attribute to convert link destination ({})".format(link))
                # throw away redundant p tag filled with the post text
                try:
                    link.p.decompose()
                except AttributeError:
                    pass
            
            # multiple entries only in albums, so we only need first item
            # BeautifulSoup.find_all() always returns result, so media_link
            # is never None
            try:
                media_link = media_link[0]
            except IndexError:
                media_link = None
            
            if album is not None:
                tags.append("photo_album")
                # we don't need media_link if album is available
                media_link = None
            
            if link_embed is not None:
                tags.append("link")
                # we don't need media_link if we got external link
                media_link = None
            
            content = ""
            for part in [post_text,
                         link_embed,
                         album,
                         media_link,
                         visibility,
                         activity,
                         comments]:
                if part is not None:
                    content = "{}\n{}\n".format(content, part)
           
            slug = utils.slugify("{}_{}".format(post_date.split()[0], title), lang="de")
            
            if not slug:  # should never happen
                LOGGER.error("Error converting post:", title)
                return

            # additional metadata
            # the passed metadata objects are limited by the basic_import's
            # write_metadata fuction
            more = {"link": post_link, # original G+ post
                    "hidetitle": True, # doesn't work for index pages
                    "category": cat,
                    }
                            
            self.write_metadata(os.path.join(self.output_folder,
                                             self.out_folder,
                                             slug + ".meta"),
                                title,
                                slug,
                                post_date,
                                "", # description always empty
                                tags,
                                more)
                                
            self.write_content(
                os.path.join(self.output_folder, self.out_folder, slug + ".html"),
                content)
            
            LOGGER.info("Imported post with status: {}".format(cat))

    def write_metadata(self, filename, title, slug, post_date, description, tags, more):
        super(CommandImportGplus, self).write_metadata(
            filename,
            title,
            slug,
            post_date,
            description,
            tags,
            **more
            )

    def prettify_title(self, t):
        """
            Titles are generated from post text.
            Cut junk and shorten to one line
            for readability and convenience.
        """
        # reduce title string to one line
        t = t.split("<br>")[0]
        # cut trailing dots
        if t.endswith("..."):
            t = t[:-3]
        # link in title? just cut it out, ain't nobody got time for that
        t = t.split("<a ")[0]
        # same for user link, periods, commas, brackets...
        t= t.split("span class=")[0]
        t = t.split(".")[0]
        t = t.split(",")[0]
        t = t.split("?")[0]
        t = t.split("(")[0]
        # cut html elements and fix quotation marks
        for tag in [("<b>", ""),
                     ("</b>", ""),
                     ("&quot;", "\""),
                     ("&#39;", "'"),
                     ("<b", ""),
                     ("</", ""),
                     ("<i>", ""),
                     ("</i>", ""),
                     ("<", ""),]:
            t = t.replace(tag[0], tag[1])
        
        return t
