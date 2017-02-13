import os
import markdown
import configparser
import shutil
import time
import json
import re
import argparse
from wand.image import Image
from bs4 import BeautifulSoup

import my_ftp
config = {}


def set_config_values(config_path):
    # Read in config data
    c = configparser.ConfigParser()
    c.read(config_path)
    config['src'] = c['blog']['src']
    config['live'] = c['blog']['live']
    config['remote'] = c['blog']['remote']
    config['templates'] = c['blog']['templates']
    config['ftpuser'] = c['FTP']['user']
    config['ftphost'] = c['FTP']['host']
    config['ftppw'] = c['FTP']['pw']


def read_json(file_path):
    """ Reads json from file """
    with open(file_path, "r") as f:
        return json.loads(f.read())


def write_json(file_path, my_json):
    """ Write json to a file """
    with open(file_path, "w") as f:
        f.write(json.dumps(my_json))
    return


def get_title(string):
    """ Converts the folder name to a nicely printed title.

    >>> get_title('test')
    'Test'
    >>> get_title('test_test')
    'Test Test'
    """
    return ' '.join([word.title() for word in string.split('_')])


def get_date(string, post_name):
    """ Captures any dates of the format yyyy-mm-dd or yyyy-mm-dd hh:mm
        from the supplied string.

        >>> get_date('    2016-12-31 10:00    ', 'test1')
        1483178400.0
        >>> get_date('   2016-12-31', 'test2')
        1483142400.0
        >>> get_date('', 'test3')
        Warning: test3 doesn't contain a date
        False
        >>> get_date('   2016-12-31 10:00    2010-12-31 10:00', 'test4')
        1483178400.0

    """
    match = re.search(r'\d{4}-\d{2}-\d{2} *(\d{2}:\d{2})?', string)
    if(not match):
        print("Warning: %s doesn't contain a date" % post_name)
        return False
    else:
        date_string = match.group()
        if(len(date_string) == 16):
            date_time = time.strptime(match.group(), '%Y-%m-%d %H:%M')
            return time.mktime(date_time)
        elif(len(date_string) == 10):
            date_time = time.strptime(match.group(), '%Y-%m-%d')
            return time.mktime(date_time)


def get_summary(html, src_post):
    """ Extract a sample of the post contents. And convert image srcs to
        link to smaller versions. Expects some html in a string.
    """
    bs = BeautifulSoup(html, "html.parser")
    for img in bs.findAll('img'):
        fn_split = img['src'].split('.')
        new_fn = fn_split[0] + '_thumb.' + fn_split[1]
        img['src'] = os.path.join('posts', src_post, new_fn)

    paras = bs.findAll('p', limit=3)
    summary = ''.join(str(p) for p in paras)
    return(summary)


def add_search_index(post_data):
    """Generate a searchable index based on post data
    """
    for p in post_data:
        p['search_index'] = p['title'].split(' ')
    return post_data


def get_search_index_json(post_data):
    """Generate an index of keywords that link to posts
    """
    index = {}
    for p in post_data:
        for keyword in p['search_index']:
            if keyword in index:
                index[keyword].append(p['name'])
            else:
                index[keyword] = [p['name'], ]
    return json.dumps(index)


def resize_and_copy(src, target):
    """ Takes any image files and downsizes then
        copies to target.
    """
    # shutil.copyfile(os.path.join(src_path, file),
    #     os.path.join(live_path, file))
    img = Image(filename=src)

    # Resize large images
    if img.height > 550:
        with img.clone() as new_image:
            new_image.transform(resize='x550')
            new_image.save(filename=target)
    else:
        shutil.copyfile(src, target)

    # Generate thumbnail
    target_th = target.split('.')
    target_th = target_th[0] + '_thumb.' + target_th[1]
    with img.clone() as new_image:
        new_image.transform(resize='x100')
        new_image.save(filename=target_th)


def wrap_and_write_post(replacements, template_path, output_path):
    """ Take a template file and replace the contents with actual data
    as defined in replacements. Results are written to output_path file.
    """

    with open(template_path) as infile, open(output_path, 'w') as outfile:
        for line in infile:
            for src, target in replacements.items():
                line = line.replace(src, target)
            outfile.write(line)


def generate_posts(to_publish, src_dir, live_dir):
    """ Map to_publish folders to live_dir, converting the MD to HTML
        and extracting post_data as we go.
    """

    # Clear down posts folders
    # shutil.rmtree(live_dir)
    # os.mkdir(live_dir)

    post_data = []
    for src_name in to_publish:
        src_path = os.path.join(src_dir, src_name)
        live_path = os.path.join(live_dir, src_name)
        md_file_exists = False
        if not os.path.exists(live_path):
            os.mkdir(live_path)
        for file in os.listdir(src_path):
            if file.endswith(".md"):
                # code expects one and only one md file per folder.
                md_file_exists = True
                input_path, output_path = (
                    os.path.join(src_path, file),
                    os.path.join(live_path, 'index.html'))
                markdown.markdownFromFile(input=input_path,
                                          output=output_path,
                                          output_format="html5")
                pd = {"name": src_name}
                pd["html"] = open(output_path, 'r').read()
                pd["title"] = get_title(src_name)
                pd["date"] = get_date(pd["html"], src_name)
                pd["summary"] = get_summary(pd["html"], pd["name"])
                replacements = {
                    '{{body}}': pd["html"],
                    '{{title}}': pd["title"],
                }
                wrap_and_write_post(
                    replacements,
                    'templates/posts/page_template.html',
                    output_path)
                post_data.append(pd)
            elif file.endswith(tuple(['.jpg', '.gif', '.png', 'jpeg'])):
                src = os.path.join(src_path, file)
                target = os.path.join(live_path, file)
                resize_and_copy(src, target)

        if not md_file_exists:
            shutil.rmtree(live_path)  # delete empty folder
    return post_data


def generate_index(post_data, live_dir, root):
    summary_posts, post_list, posts = '', '', 0
    for post in post_data:
        date = time.strftime("%Y-%m-%d", time.localtime(post['date']))
        if(posts < 3):
            link = ("Read more of: <a href='posts/%s/index.html'>%s</a></li>\n"
                    % (post['name'], post['title']))
            summary_posts += ("<article><h3>%s</h3>\
                    <p>%s</p><p>...</p><p>%s</p></article>\n"
                              % (post['title'], post['summary'], link))
        posts += 1
        post_list += ("<li><a href='%s/index.html'>%s \
                <small>%s</small></a></li>\n"
                      % ('posts/' + post['name'], post['title'], date))
    replacements = {'{{first_post}}': summary_posts,
                    '{{link_list}}': post_list,
                    '{{search_index}}': get_search_index_json(post_data),
                    }
    wrap_and_write_post(replacements,
                        'templates/posts/index_template.html',
                        os.path.join(root, 'index.html'))


def write_file(line, fl_path):
    """ Create a file from and write line to it"""
    with open(fl_path, "w") as f:
        f.write("{0}".format(line))


def create_fresh_live_dir(drctry):
    """ Create a new, empty direcory and .cache file"""
    os.mkdir(drctry)
    os.mkdir(os.path.join(drctry, "posts/"))
    write_file('', os.path.join(drctry, ".cache"))
    write_json(os.path.join(drctry, ".jcache"), [])
    shutil.copytree(os.path.join(config['templates'], 'resources/'),
                    os.path.join(drctry, "resources/"))


def get_changed_directories(all_drs, src_dr, live_dr):
    """ Finds out if any of the directories have been updated since
    last published date """
    changed_drs = []
    with open(os.path.join(live_dr, ".cache")) as c:
        last_modified = c.read()
        if last_modified != '':
            last_modified = float(last_modified)
    for dr in all_drs:
        path = os.path.join(src_dr, dr)
        path_modified = get_last_update(path)
        if last_modified == '' or path_modified > last_modified:
            changed_drs.append(dr)
    return changed_drs


def get_last_update(dr):
    dates = []
    for root, directories, filenames in os.walk(dr):
        for filename in filenames:
            f = os.path.join(root, filename)
            dates.append(os.path.getmtime(f))
    return max(dates)


def update_cache(dr):
    posts_dr = os.path.join(dr, 'posts/')
    cache = os.path.join(dr, ".cache")
    write_file(get_last_update(posts_dr), cache)


def find_post(name, post_data):
    for index in range(len(post_data)):
        if name == post_data[index]['name']:
            return index
    return -1


def get_deleted_posts(post_data, all_directories):
    deleted_posts = []
    for p in post_data:
        if p['name'] not in all_directories:
            deleted_posts.append(p['name'])
    return deleted_posts


def remove_post(post_data, post):
    for i in range(len(post_data)):
        if post_data[i]['name'] == post:
            if i == 0:
                return post_data[i + 1:]
            elif i == len(post_data) - 1:
                return post_data[:i]
            else:
                return post_data[:i] + post_data[i + 1:]
    # nothing found
    print("Error: Deleted post not found.")
    return post_data


def publish():
    src_dir = config['src']
    live_root = config['live']  # root of the live directory
    live_posts_dir = os.path.join(live_root, "posts/")  # posts dir
    if not os.path.exists(live_root):
        print("Create new directory.")
        create_fresh_live_dir(live_root)
    post_data = read_json(os.path.join(live_root, ".jcache"))
    all_directories = [d for d in os.listdir(src_dir)
                       if '.' not in d]
    deleted_posts = get_deleted_posts(post_data, all_directories)
    to_publish = get_changed_directories(all_directories, src_dir, live_root)
    if len(to_publish) > 0:
        print("{0} post(s) to be updated".format(len(to_publish)))
        new_posts = generate_posts(to_publish, src_dir, live_posts_dir)
        for post in new_posts:
            post_index = find_post(post['name'], post_data)
            if post_index >= 0:
                print(post_index)
                post_data[post_index] = post
            else:
                post_data.append(post)
    else:
        print("No new posts.")

    if len(deleted_posts) > 0:
        print("{0} post(s) to be deleted".format(len(deleted_posts)))
        for p in deleted_posts:
            shutil.rmtree(os.path.join(live_root, "posts/", p))
            post_data = remove_post(post_data, p)
    else:
        print("No posts deleted.")

    if len(to_publish) > 0 or len(deleted_posts) > 0:
        post_data = add_search_index(post_data)
        post_data = sorted(post_data, key=lambda x: x['date'], reverse=True)
        generate_index(post_data, live_posts_dir, live_root)
        update_cache(live_root)
        write_json(os.path.join(live_root, '.jcache'), post_data)
        return (to_publish, deleted_posts)
    else:
        return None


if __name__ == "__main__":
    """Publish markdown files from source as HTML"""
    parser = argparse.ArgumentParser()
    # default_directory, default_target = 'src_test/', 'live_test/'
    parser.add_argument("-t", "--test",
                        help="Run doctests",
                        action="store_true")
    parser.add_argument("-u", "--upload",
                        help="Upload new/changed posts to remote server",
                        action="store_true")
    parser.add_argument("-fu", "--forceupload",
                        help="Upload all files to remote server",
                        action="store_true")
    parser.add_argument("config",
                        nargs="?",
                        default="config_test.ini",
                        help="Config file path")
    args = parser.parse_args()

    if(args.test):
        import doctest
        doctest.testmod()
    else:
        set_config_values(args.config)
        published = publish()

        if args.forceupload:
            my_ftp.upload_site(config['LIVE_PATH'])
            print("Site uploaded to remote server.")
        elif args.upload and published:
            new, deleted = published
            if len(new) > 0:
                my_ftp.upload_posts(args.target, new)
                print("{0} new/changed posts uploaded to server."
                      .format(len(new)))
            if len(deleted) > 0:
                my_ftp.delete_posts(deleted)
                print("{0} posts deleted from server.".format(len(deleted)))
            # finally upload index
            my_ftp.upload_changed_index(args.target)
        else:
            print("Upload set to {0}".format(args.upload))
