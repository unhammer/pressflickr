#!/usr/bin/env python2
from __future__ import with_statement

import re, sys, os, glob, ConfigParser, webbrowser

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

        if pct > self._last_pct + 10:
            print "%.2f %% ..." % (pct,),
            sys.stdout.flush()
            #print '%s %.2f %% done' % (self._name, pct)
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
    post_id = blog.newPost(post, publish=False)
    return post_id

def filepath_to_class(path):
    cm = re.search(r'(crop[bt][0-9]+(px|pct))[^/]*$', path)
    if cm:
        return "crop "+cm.group(1)
    else:
        return ""

def upload_cwd(blog, same_alt):
    # glob will work in current working directory, which is what we
    # want, so no need to prepend a folder path here
    from pyexpat import ExpatError
    images = glob.glob("*.[Jj][Pp][Gg]") + glob.glob("*.[Pp][Nn][Gg]") + glob.glob("*.[Gg][Ii][Ff]")
    print "Found " + ", ".join(images)
    html = ""
    for i,path in enumerate(images):
        print "Uploading %s (%s/%s)..." % (path,i+1,len(images))
        if same_alt:
            alt = same_alt
        else:
            alt = os.path.basename(path.decode('utf-8'))
        pclass = filepath_to_class(path)
        try:
            url = blog.newMediaObject(path, Progress("%s (%s/%s)" % (path,i+1,len(images))).update)
            print ""
            html += "<p class=\"%s\"><img src=\"%s\" alt=\"%s\" class=\"pressfolder\"/></p>\n" % (
                pclass,
                url,
                alt
            )
        except ExpatError as e:
            print "\nExpatError: {0}\n on {1}\n{2}".format(e.message, path, e)
            html += "<p>%s?</p>\n" % (os.path.basename(path.decode('utf-8')),)


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
    if not config.has_option('Main', 'alttext'):
        config.set('Main', 'alttext', "")
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
    configpath = os.path.expanduser("~/.config/pressfolder/config.cfg")
    config = setup_config(configpath)
    
    blog = getBlog(config.get('Main', 'wp_url', 0),
                   config.get('Main', 'wp_user', 0),
                   config.get('Main', 'wp_pass', 0),
                   config.get('Main', 'blogid', 0))
         
    html = upload_cwd(blog,
                      config.get('Main', 'alttext', 0))

    post_id = post(blog,
                   config.get('Main', 'title', 0),
                   html)

    url = "%swp-admin/post.php?post=%s&action=edit" % (blog.url.rstrip('xmlrpc.php'),
                                                       post_id)
    print "Opening edit post page at " + url
    webbrowser.open(url)
