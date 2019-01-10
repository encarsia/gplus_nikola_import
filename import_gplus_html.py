# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import os
import shutil
import sys
import yaml
from collections import Counter

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


class CommandImportGplus(Command, ImportMixin):
    """Import a Google+ dump."""

    name = "import_gplus"
    needs_config = True
    doc_usage = "[options] extracted_dump_file_folder"
    doc_purpose = "import a Google+ dump"
    cmd_options = ImportMixin.cmd_options + [
        {
            "name": "show_statuses",
            "long": "statuses",
            "short": "s",
            "default": False,
            "type": bool,
            "help": "Show all post statuses to support you with configuration",
        }
    ]
    def _execute(self, options, args):
        '''
            Import Google+ dump
        '''

        if not args:
            print(self.help())
            return
        
        options["foldername"] = args[0]
        self.export_folder = os.path.join(options["foldername"], "Takeout")
        self.output_folder = options["output_folder"]
        self.import_into_existing_site = False
        self.url_map = {}

        with open(os.path.join("plugins",
                                "import_gplus_html",
                                "config.yaml")) as f:
            self.config = yaml.load(f)

        # path to post files
        post_path = os.path.join(self.export_folder,
                                 self.config["gto"]["stream"],
                                 self.config["gto"]["posts"],
                                )
        
        # collect all files
        files = [f for f in os.listdir(os.path.join(post_path)) if os.path.isfile(os.path.join(post_path, f))]

        src_files = [f for f in files if f.endswith(".html")]
        if len(src_files) == 0:
            LOGGER.warn("""No HTML files found. Possible reasons:
    1) you pointed to the wrong folder
    2) you selected the wrong file format
    3) there may be (spelling) errors in the configuration file""")
            sys.exit(1)
        else:
            LOGGER.info("{} HTML formatted posts ready for import".format(len(src_files)))
        
        if options["show_statuses"]:
            self.analyze_share(post_path, src_files)
            sys.exit(0)
        
        # init new site and copy media files to output folder
        conf_template = self.generate_base_site()
        self.prepare_media(self.export_folder)
        
        self.context = self.populate_context(src_files,
                                             post_path,
                                             self.config,
                                             )
        self.write_configuration(self.get_configuration_output_path(), conf_template.render(**prepare_config(self.context)))
        self.import_posts(src_files,
                          post_path,
                          self.config,
                          )

    @staticmethod
    def populate_context(names, path, config):
        # get info from configuration file
        context = SAMPLE_CONF.copy()
        context["DEFAULT_LANG"] = config["site"]["lang"]
        context["BLOG_DESCRIPTION"] = config["site"]["descr"]
        context["SITE_URL"] = config["site"]["url"]
        context["BLOG_EMAIL"] = config["site"]["email"]
        context["BLOG_TITLE"] = config["site"]["title"]

        # Get any random post, all have the same data
        with open(os.path.join(path, names[0])) as f:
            soup = bs4.BeautifulSoup(f, "html.parser")
        
        context["BLOG_AUTHOR"] = soup.find("a", "author").text
        profile_url = soup.find("a").get("href")
            
        context["POSTS"] = '''(
            ("posts/*.html", "posts", "post.tmpl"),
            ("posts/*.rst", "posts", "post.tmpl"),
        )'''
        
        context["COMPILERS"] = '''{
        "rest": ('.txt', '.rst'),
        "html": ('.html', '.htm')
        }
        '''
        
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

    def analyze_share(self, path, names):
        status_general = []
        status_detail = []
        for name in names:
            with open(os.path.join(path, name)) as f:
                soup = bs4.BeautifulSoup(f, "html.parser")

            visibility = soup.find("div", "visibility")
            vis_link = soup.find("div", "visibility").find("a")
            status_general.append(visibility.contents[0].split(",")[0].rstrip())
            if vis_link: status_detail.append(vis_link)
            
        #status_detail = Counter(status_detail)

        status_com = []
        status_circle = []
        status_coll = []
        status_event = []
        for s in status_detail:
            try:
                title = s.contents[0]
                if "communities" in s.get("href"):
                    status_com.append(title)
                elif "collection" in s.get("href"):
                    status_coll.append(title)
                elif "circle" in s.get("href"):
                    status_circle.append(title)
                elif  "event" in s.get("href"):
                    status_event.append(title)
            except IndexError:
                if "communities" in s.get("href"):
                    status_com.append("Deleted community")
                elif "collection" in s.get("href"):
                    status_coll.append("Deleted collection")
                elif "circle" in s.get("href"):
                    status_circle.append("Deleted circle")
                elif "event" in s.get("href"):
                    status_event.append("Deleted event")
    
        status_general = Counter(status_general)
        status_com = Counter(status_com)
        status_circle = Counter(status_circle)
        status_coll = Counter(status_coll)
        status_event = Counter(status_event)
    
        text_gen = """
************************************************
*                                              *
* Share information of your G+ Takeout archive *
*                                              *
************************************************

=======
General
=======

(edit the "shared" section of your config.yaml)
"""

        text_com = """
===========
Communities
===========

(edit the "import" section of your config.yaml:
    > set "com" to True to include communities
    > exclude communities by listing them in "com_filter")
"""

        text_crcl = """
=======
Circles
=======

(edit the "import" section of your config.yaml:
    > set "private" to True to include all posts
    > exclude posts to specific circles by listing them in "circle_filter")
"""

        text_coll = """
===========
Collections
===========

(collections are considered public so this is FYI only)
"""

        text_ev = """
======
Events
======

(edit the "import" section of your config.yaml:
    > set "events" to True to include all shares to events)
"""
        
        for txt, lst in [(text_gen, status_general.most_common()),
                          (text_com, status_com.most_common()),
                          (text_crcl, status_circle.most_common()),
                          (text_ev, status_event.most_common()),
                          (text_coll, status_coll.most_common()),
                         ]:
            print(txt)
            for i in lst:
                print("{} ({})".format(i[0], i[1]))
    
    def import_posts(self, names, path, config):
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
            # get name of 1st item of visibility list which is link to com/coll
            # links to deleted profiles still exist without link text
            if vis_link:
                try:
                    vis_text = vis_link.contents[0]
                except IndexError:
                    if "communities" in vis_link.get("href"):
                        vis_text = "Deleted community"
                    elif "collection" in vis_link.get("href"):
                        vis_text = "Deleted collection"
                    elif "event" in vis_link.get("href"):
                        vis_text = "Deleted event"
                    else:
                        vis_text = "Deleted profile"
                    # original post 404
                    post_link = ""

            # get title of com/coll/circle/event
            vis = visibility.contents[0].rstrip()

            if (vis.startswith(config["shared"]["public"]) or \
                    vis.startswith(config["shared"]["circles"]) or \
                    vis.startswith(config["shared"]["extcircles"])):
                # common share status for general posts
                cat = vis.split(",")[0] # get rid of comma if there is any
            elif vis in config["shared"]["com"]:
                # check if communities are ignored
                if not config["import"]["com"]:
                    LOGGER.warning("Community post will be ignored: {}".format(post_link))
                    continue
                # else check if community is in filter list
                elif vis_text in config["import"]["com_filter"]:
                    LOGGER.warning("Community post to \"{}\" will be ignored: {}".format(vis_text, post_link))
                    continue
                cat = "{} \"{}\"".format(vis, vis_text)
            elif vis in config["shared"]["coll"]:
                # collections are considered to be public
                cat = "{} \"{}\"".format(vis, vis_text)
            elif vis in config["shared"]["event"]:
                if not config["import"]["event"]:
                    LOGGER.warning("Post to event will be ignored: {}".format(post_link))
                    continue
                cat = "{} \"{}\"".format(vis, vis_text)
            elif vis_link:
                # check if post is shared with circle
                if "circles" in vis_link.get("href"):
                    if not config["import"]["private"]:
                        LOGGER.warning("Private post will be ignored: {}".format(post_link))
                        continue
                    elif vis_text in config["import"]["circle_filter"]:
                        LOGGER.warning("Post to circle \"{}\" will be ignored: {}".format(vis_text, post_link))
                        continue
                    cat = "Shared to circle \"{}\"".format(vis_text)
            else:
                # everything else is considered private/other
                if not config["import"]["private"]:
                    LOGGER.warning("Private post will be ignored: {}".format(post_link))
                    continue
                cat = config["shared"]["other"]
            
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
            
            LOGGER.info("Imported post with status: {}.".format(cat))

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

    def prepare_media(self, folder):
        # In the Takeout archive photos are linked to the main working
        # directory although they do not necessarily exist there (Hello
        # deadlinks!). The image files are spread to several folders.

        # All archive photos will be copied to the "images" folder.
        try:
            os.makedirs(os.path.join(self.output_folder, "images"))
            LOGGER.debug("Image folder created.")
        except:
            pass

        for root, dirs, files in os.walk(folder):
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
                        LOGGER.info("Skipping {}. File already exists.".format(f))
