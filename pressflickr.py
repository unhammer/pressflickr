from __future__ import with_statement
import re, sys, os
import flickrapi
import wordpresslib
import ConfigParser


def link_html(NSID, att):
    # z before the .jpg is medium, l is large...
    z_url = "http://farm" + att['farm'] + ".static.flickr.com/" + att['server'] + "/" + att['id'] + "_" + att['secret'] + "_z.jpg"
    page_url = "http://www.flickr.com/photos/" + NSID + "/" + att['id']
    link_html = '<a href="' + page_url + '"><img src="' + z_url + '" alt="' + att['title'] + '"/></a>'
    return link_html


def set_to_html(NSID, set_id):
    hits = flickr.photosets_getPhotos(photoset_id=set_id)
    postcontent = ''
    for p in hits[0]:
         postcontent += '<p>' + link_html(NSID, p.attrib) + "</p>\n"
    return postcontent


def post(wp_url, wp_user, wp_pass, blogid, title, content):
    wp = wordpresslib.WordPressClient(wp_url, wp_user, wp_pass)
    wp.selectBlog(blogid)
    post = wordpresslib.WordPressPost()
    post.title = title
    post.description = content
    print "Posting to " + wp_url + " with title " + title
    post_id = wp.newPost(post, True)
    return post_id


def setup_config(configpath):
    ### Set up global config file
    config = ConfigParser.ConfigParser()
    configdir = os.path.dirname(configpath)
    if not os.path.exists(configdir): os.makedirs(configdir)
    if not os.path.exists(configpath):
        # Set up initial config file
        config.add_section('Main')
        config.set('Main', 'api_key', 'YOUR_API_KEY_HERE')
        config.set('Main', 'flickrusers', 'COMMA_DELIMITED_LIST_OF_USER_NSIDS_HERE')
        config.set('Main', 'flickrsets', 'ONE_SET_PER_NSID_COMMA_DELIMITED_SAME_ORDER')
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
        blogid = find_wpcom_blog_id(config.get('Main', 'wp_url', 0),
                                    config.get('Main', 'wp_user', 0),
                                    config.get('Main', 'wp_pass', 0))
        config.set('Main', 'blogid', blogid)
        with open(configpath, 'wb') as configfile: config.write(configfile)
    
    return config


def find_wpcom_blog_id(wp_url, wp_user, wp_pass):
    """You have to supply http://wordpress.com to get the list of
    blogid's, but you can only post from http://domain.wordpress.com,
    thus this function.
    """
    # Ensure the url looks exactly like "http://domain.wordpress.com/"
    wpcom_pat = re.compile("(https?://)?([^.]+).wordpress.com")
    wp_url = "http://" + wpcom_pat.match(wp_url).group(2) + ".wordpress.com/"
    
    wp = wordpresslib.WordPressClient('http://wordpress.com/xmlrpc.php',
                                      wp_user, wp_pass)
    blogid = 0
    for b in wp.getUsersBlogs():
        if wp_url == b.url:
            blogid = b.id
            break
    return blogid


def find_flickr_NSID_path(flickrusers):
    ### For turning path_aliases into NSID's, convenience function
    flickr_NSID_path = {}
    for u_id in flickrusers:
        u = flickr.people_getinfo(user_id=u_id)
        path_alias = u[0].attrib['path_alias']
        flickr_NSID_path[ path_alias ] = u_id
        #print u_id + ' is ' + u[0][0].text + ' (' + u[0].attrib['path_alias'] + ')'
    return flickr_NSID_path

def pos(item, seq):
    for i,x in enumerate(seq):
        if x == item:
            return i
    
def get_set_by_NSID(NSID,config):
    set_ids = config.get('Main', 'flickrsets',0).split(',')
    NSIDs = config.get('Main', 'flickrusers',0).split(',')
    return set_ids[pos(NSID,NSIDs)]

if __name__ == '__main__':
    configpath = os.path.expanduser("~/.pressflickr/config.cfg")
    config = setup_config(configpath)
    flickr = flickrapi.FlickrAPI(config.get('Main', 'api_key', 0))
    if len(sys.argv) == 2:
        NSID = sys.argv[1]
    else:
        print "An NSID from ~/.pressflickr/config.cfg must be supplied as the first argument!"
        sys.exit(1)
    set_id = get_set_by_NSID(NSID, config)
    post(config.get('Main', 'wp_url', 0),
         config.get('Main', 'wp_user', 0),
         config.get('Main', 'wp_pass', 0),
         config.get('Main', 'blogid', 0),
         config.get('Main', 'title', 0),
         set_to_html(NSID, set_id))


    ### Used to have path as sys.argv[1], but I'd rather reduce the
    ### amount of requests and call with plain NSID's
    # flickr_NSID_path = find_flickr_NSID_path(config.get('Main', 'flickrusers', 0).split(','))
    # NSID = flickr_NSID_path[path]
    

################################################################
###                        DEPRECATED                        ###
################################################################
def get_links_by_search(user, searchtext):
    "Too much trouble for many pics"
    NSID=usernames[user]
    hits = flickr.photos_search(user_id=NSID,text=searchtext)
    for p in hits[0]:
        print link_html(NSID, p.attrib)

def get_ids_by_tags(user, tags):
    "Tag search unfortunately requires user credentials"
    NSID=usernames[user]
    hits = flickr.photos_search(user_id=NSID,tags=tags)
    for p in hits[0]:
        print link_html(NSID, p.attrib)

def get_link_by_URL(user, URL):
    "Too much work with copy-pasting, would rather rely on flickr set UI since it's already quite good"
    NSID=usernames[user]
    pattern = re.compile('^https?://[^/]*/photos/[^/]*/([0-9]+)')
    photoid = pattern.match(URL).group(1)
    photo=flickr.photos_getInfo(user_id=NSID,photo_id=photoid)
    return link_html(NSID, photo[0].attrib)


def get_links_by_URLs(user, URLs):
    for URL in URLs:
        print "<p>" + get_link_by_URL(user,URL) + "</p>"
