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


def tag_to_html(NSID, tag):
    hits = flickr.photos_search(user_id=NSID, tags=[tag])
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
    post_id = wp.newPost(post, False)
    return post_id


def setup_config(configpath):
    ### Set up global config file
    config = ConfigParser.ConfigParser()
    configdir = os.path.dirname(configpath)
    if not os.path.exists(configdir): os.makedirs(configdir)
    if not os.path.exists(configpath):
        # Set up initial config file
        config.add_section('Main')
        config.set('Main', 'flickrusers', 'COMMA_DELIMITED_LIST_OF_USER_NSIDS_HERE')
        config.set('Main', 'flickrtag', 'ONE_TAG_PER_NSID_COMMA_DELIMITED_SAME_ORDER')
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


def pos(item, seq):
    for i,x in enumerate(seq):
        if x == item:
            return i
    
def get_tag_by_NSID(NSID,config):
    tags = config.get('Main', 'flickrtags',0).split(',')
    NSIDs = config.get('Main', 'flickrusers',0).split(',')
    return tags[pos(NSID,NSIDs)]

if __name__ == '__main__':
    configpath = os.path.expanduser("~/.pressflickr/config.cfg")
    config = setup_config(configpath)
    if len(sys.argv) == 2:
        NSID = sys.argv[1]
    else:
        print "An NSID from ~/.pressflickr/config.cfg must be supplied as the first argument!"
        sys.exit(1)
    
    api_key = '7e3dfb26a6d98574fc6f1241f9c76d7b'
    api_secret = '6e2a0429802b8759'
    flickr = flickrapi.FlickrAPI(api_key, api_secret, username=NSID)
    (token, frob) = flickr.get_token_part_one(perms='read')
    if not token: raw_input("Press ENTER after you authorized this program")
    flickr.get_token_part_two((token, frob))
    
    post(config.get('Main', 'wp_url', 0),
         config.get('Main', 'wp_user', 0),
         config.get('Main', 'wp_pass', 0),
         config.get('Main', 'blogid', 0),
         config.get('Main', 'title', 0),
         tag_to_html(NSID, get_tag_by_NSID(NSID, config)))

