#!/usr/bin/env python2
from __future__ import with_statement

import re, sys, os, glob, mimetypes, xmlrpclib, ConfigParser

try:
    import wordpresslib.wordpresslib as wordpresslib
except ImportError, e:
    print
    print "Try this:"
    print "\tcd " + os.path.dirname(__file__)
    print "\tgit clone --branch progress_bar git://github.com/unhammer/wordpresslib.git"
    print "\ttouch wordpresslib/__init__.py"
    print
    raise e


class Progress(object):
    def __init__(self, name):
        self._seen = 0.0
        self._last_pct = 0.0
        self._name = name

    def update(self, total, size):
        self._seen += size
        pct = (self._seen / total) * 100.0

        if pct > self._last_pct:
            print '%s %.2f %% done' % (self._name, pct)
            self._last_pct = pct
        # If size is very small and total is big, pct
        # stays the same, so don't update


def getBlog(wp_url, wp_user, wp_pass, blogid):
    print "Connecting to " + wp_url
    wp = wordpresslib.WordPressClient(xmlrpc_url(wp_url),
                                      wp_user, wp_pass)
    wp.selectBlog(blogid)
    return wp

def post(blog, title, content):
    print "Posting with title " + title
    post = wordpresslib.WordPressPost()
    post.title = title
    post.description = content
    post_id = blog.newPost(post, False)
    return post_id

def upload_cwd(blog):
    # glob will work in current working directory, which is what we
    # want, so no need to prepend a folder path here
    images = glob.glob("*.[Jj][Pp][Gg]") + glob.glob("*.[Pp][Nn][Gg]") + glob.glob("*.[Gg][Ii][Ff]")
    print "Found " + ", ".join(images)
    html = ""
    for i in images:
        print "Uploading " + i + " ..."

        url = blog.newMediaObject(i, Progress(i).update)

        html += "<p><img src=\"%s\" alt=\"%s\" class=\"pressfolder\"/></p>\n" % (
            url, os.path.basename(i)
            )
    return html


def setup_config(configpath):
    ### Set up global config file
    config = ConfigParser.ConfigParser()
    configdir = os.path.dirname(configpath)
    if not os.path.exists(configdir): os.makedirs(configdir)
    if not os.path.exists(configpath):
        # Set up initial config file
        config.add_section('Main')
        config.set('Main', 'wp_user', 'YOUR_WORDPRESS_USERNAME_HERE')
        config.set('Main', 'wp_pass', 'YOUR_WORDPRESS_PASSWORD_HERE')
        config.set('Main', 'wp_url', 'YOUR_WORDPRESS_URL_HERE')
        config.set('Main', 'title', 'YOUR_DEFAULT_POST_TITLE_HERE')
        with open(configpath, 'wb') as configfile: config.write(configfile)
        print "Created default configuration file at " + configpath
        print "Please edit the configuration and try again."
        sys.exit(1)
    
    ### Read config
    config.read(configpath)
    ### Cache blogid:
    if not config.has_option('Main', 'blogid'):
        blogid = find_blog_id(config.get('Main', 'wp_url', 0),
                              config.get('Main', 'wp_user', 0),
                              config.get('Main', 'wp_pass', 0))
        print "Assuming blogid is " + blogid + ", edit " + configpath + " if this is wrong"
        config.set('Main', 'blogid', blogid)
        with open(configpath, 'wb') as configfile: config.write(configfile)
    
    return config


def find_blog_id(wp_url, wp_user, wp_pass):
    blogid = 0
    wpcom_pat = re.compile("(https?://)?([^.]+).wordpress.com")
    wpcom_m = wpcom_pat.match(wp_url)
    if wpcom_m:
        wp_url = "http://" + wpcom_m.group(2) + ".wordpress.com/"
        wp = wordpresslib.WordPressClient('http://wordpress.com/xmlrpc.php',
                                          wp_user, wp_pass)
        for b in wp.getUsersBlogs():
            if wp_url == b.url:
                blogid = b.id
                break
    else:
        wp = wordpresslib.WordPressClient(xmlrpc_url(wp_url),
                                          wp_user, wp_pass)
        for b in wp.getUsersBlogs():
            if xmlrpc_url(wp_url) == xmlrpc_url(b.url):
                blogid = b.id
                break
    return blogid
        
        
    

def find_wpcom_blog_id(wp_url, wp_user, wp_pass):
    """You have to supply http://wordpress.com to get the list of
    blogid's, but you can only post from http://domain.wordpress.com,
    thus this function.
    """
    wp_url = "http://" + wpcom_pat.match(wp_url).group(2) + ".wordpress.com/"
    
    wp = wordpresslib.WordPressClient('http://wordpress.com/xmlrpc.php',
                                      wp_user, wp_pass)
    blogid = 0
    for b in wp.getUsersBlogs():
        if wp_url == b.url:
            blogid = b.id
            break
    return blogid

def xmlrpc_url(wp_url):
    if wp_url.endswith("xmlrpc.php"):
        return wp_url
    else:
        return wp_url.rstrip("/") + "/xmlrpc.php"


if __name__ == '__main__':
    configpath = os.path.expanduser("~/.pressfolder/config.cfg")
    config = setup_config(configpath)
    
    blog = getBlog(config.get('Main', 'wp_url', 0),
                   config.get('Main', 'wp_user', 0),
                   config.get('Main', 'wp_pass', 0),
                   config.get('Main', 'blogid', 0))
         
    html = upload_cwd(blog)

    post(blog,
         config.get('Main', 'title', 0),
         html)

