import os
import sys
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
config, post_data = {}, {}


# Support functions
def read_json(file_path):
    """ Reads json from file """
    with open(file_path, "r") as f:
        return json.loads(f.read())


def write_json(jsn, file_path):
    """ Write json to a file """
    with open(file_path, "w") as f:
        f.write(json.dumps(jsn))
    return


def write_file(line, file_path):
    """ Create a file and write line to it"""
    with open(file_path, "w") as f:
        f.write("{0}".format(line))


# Initiate Config
def set_config_values(config_path):
    """ Read in config data and set global config param
    """
    global config
    c = configparser.ConfigParser()
    c.read(config_path)

    config["blog"] = {
        "src_path": c["blog"]["src_path"],
        "published_path": c["blog"]["published_path"],
        "remote_path": c["blog"]["remote_path"],
        "templates_path": c["blog"]["templates_path"]
    }
    config["ftp"] = {
        "host": c["ftp"]["host"],
        "user": c["ftp"]["user"],
        "pw": c["ftp"]["pw"]
    }


# Publish Site
def get_title(string):
    """ Converts the folder name to a nicely printed title.

    >>> get_title("test")
    "Test"
    >>> get_title("test_test")
    "Test Test"
    """
    return " ".join([word.title() for word in string.split("_")])


def get_date(string, post_name):
    """ Captures any dates of the format yyyy-mm-dd or yyyy-mm-dd hh:mm
        from the supplied string.

        >>> get_date("    2016-12-31 10:00    ", "test1")
        1483178400.0
        >>> get_date("   2016-12-31", "test2")
        1483142400.0
        >>> get_date("", "test3")
        Warning: test3 doesn"t contain a date
        False
        >>> get_date("   2016-12-31 10:00    2010-12-31 10:00", "test4")
        1483178400.0

    """
    match = re.search(r"\d{4}-\d{2}-\d{2} *(\d{2}:\d{2})?", string)
    if(not match):
        # print("Warning: %s does not contain a date" % post_name)
        return False
    else:
        date_string = match.group()
        if(len(date_string) == 16):
            date_time = time.strptime(match.group(), "%Y-%m-%d %H:%M")
            return time.mktime(date_time)
        elif(len(date_string) == 10):
            date_time = time.strptime(match.group(), "%Y-%m-%d")
            return time.mktime(date_time)


def get_summary(html, src_post):
    """ Extract a sample of the post contents. And convert image srcs to
        link to smaller versions. Expects some html in a string.
    """
    bs = BeautifulSoup(html, "html.parser")
    for img in bs.findAll("img"):
        fn_split = img["src"].split(".")
        new_fn = fn_split[0] + "_thumb." + fn_split[1]
        img["src"] = os.path.join("posts", src_post, new_fn)

    paras = bs.findAll("p", limit=3)
    summary = "".join(str(p) for p in paras)
    return(summary)


def create_fresh_live_dir(path):
    """ Create a new, empty direcory and .cache file"""
    global config
    os.mkdir(path)
    os.mkdir(os.path.join(path, "posts/"))
    write_file("", os.path.join(path, ".last_updated"))
    write_json([], os.path.join(path, ".pd_cache"))
    shutil.copytree(os.path.join(config["blog"]["templates_path"],
                                 "resources/"),
                    os.path.join(path, "resources/"))


def get_deleted_posts(all_directories):
    """ Returns a list of deleted posts"""
    global post_data
    deleted_posts = []
    for p in post_data:
        if p["name"] not in all_directories:
            deleted_posts.append(p["name"])
    return deleted_posts


def get_new_posts(all_drs, src_dr, live_dr):
    """ Returns a list of new or updated posts"""
    changed_drs = []
    with open(os.path.join(live_dr, ".last_updated")) as c:
        last_modified = c.read()
        if last_modified != "":
            last_modified = float(last_modified)
    for dr in all_drs:
        path = os.path.join(src_dr, dr)
        path_modified = get_last_update(path)
        if last_modified == "" or path_modified > last_modified:
            changed_drs.append(dr)
    return changed_drs


def generate_posts(to_publish, src_dir, live_dir):
    """ Map to_publish folders to live_dir, converting the MD to HTML
        and extracting post_data as we go.
    """

    # Clear down posts folders
    # shutil.rmtree(live_dir)
    # os.mkdir(live_dir)
    global post_data
    # post_data = []
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
                input_path = os.path.join(src_path, file)
                output_path = os.path.join(live_path, "index.html")
                markdown.markdownFromFile(input=input_path,
                                          output=output_path,
                                          output_format="html5")
                # Generate post info for post_data
                pd = {"name": src_name}
                pd["html"] = open(output_path, "r").read()
                pd["title"] = get_title(src_name)
                pd["date"] = get_date(pd["html"], src_name)
                pd["summary"] = get_summary(pd["html"], pd["name"])

                replacements = {
                    "{{body}}": pd["html"],
                    "{{title}}": pd["title"],
                }
                # write html
                template_file = os.path.join(config["blog"]["templates_path"],
                                             "posts/page_template.html")
                wrap_and_write_post(replacements, template_file, output_path)
                post_data.append(pd)
            elif file.endswith(tuple([".jpg", ".gif", ".png", "jpeg"])):
                src = os.path.join(src_path, file)
                target = os.path.join(live_path, file)
                resize_and_copy(src, target)
        if not md_file_exists:
            shutil.rmtree(live_path)  # delete empty folder


def add_search_index():
    """Generate a searchable index based on post data
    """
    global post_data
    for p in post_data:
        p["search_index"] = p["title"].split(" ")


def get_search_index_json():
    """Generate an index of keywords that link to posts
    """
    global post_data
    index = {}
    for p in post_data:
        for keyword in p["search_index"]:
            if keyword in index:
                index[keyword].append(p["name"])
            else:
                index[keyword] = [p["name"], ]
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
            new_image.transform(resize="x550")
            new_image.save(filename=target)
    else:
        shutil.copyfile(src, target)

    # Generate thumbnail
    target_th = target.split(".")
    target_th = target_th[0] + "_thumb." + target_th[1]
    with img.clone() as new_image:
        new_image.transform(resize="x100")
        new_image.save(filename=target_th)


def wrap_and_write_post(replacements, templates_path, output_path):
    """ Take a template file and replace the contents with actual data
    as defined in replacements. Results are written to output_path file.
    """
    with open(templates_path) as infile, open(output_path, "w") as outfile:
        for line in infile:
            for src, target in replacements.items():
                line = line.replace(src, target)
            outfile.write(line)


def generate_index(live_dir, root):
    """ Generate the html for the index page """
    global post_data
    summary_posts, post_list = "", ""
    for post in post_data:
        date = time.strftime("%Y-%m-%d", time.localtime(post["date"]))
        # if(posts < 3):
        #     link = ("Read more of: <a href='posts/%s/index.html'>%s</a></li>\n"
        #             % (post["name"], post["title"]))
        #     summary_posts += ("<article><h3>%s</h3>\
        #             <p>%s</p><p>...</p><p>%s</p></article>\n"
        #                       % (post["title"], post["summary"], link))
        # posts += 1
        post_list += ("<li class='group'><a href='%s/index.html'>%s</a> \
                <small>%s</small></li>\n"
                      % ("posts/" + post["name"], post["title"], date))
    replacements = {"{{first_post}}": summary_posts,
                    "{{link_list}}": post_list,
                    "{{search_index}}": get_search_index_json(),
                    }
    wrap_and_write_post(replacements,
                        os.path.join(config["blog"]["templates_path"],
                                     "posts/index_template.html"),
                        os.path.join(root, "index.html"))


def get_last_update(dr):
    dates = []
    for root, directories, filenames in os.walk(dr):
        for filename in filenames:
            f = os.path.join(root, filename)
            dates.append(os.path.getmtime(f))
    return max(dates)


def find_post(name):
    global post_data
    for index in range(len(post_data)):
        if name == post_data[index]["name"]:
            return index
    return -1


def remove_post(post):
    global post_data
    for i in range(len(post_data)):
        if post_data[i]["name"] == post:
            if i == 0:
                post_data = post_data[i + 1:]
                return
            elif i == len(post_data) - 1:
                post_data = post_data[:i]
                return
            else:
                post_data = post_data[:i] + post_data[i + 1:]
                return


def publish():
    global config, post_data
    src_path = config["blog"]["src_path"]
    published_path = config["blog"]["published_path"]
    posts_path = os.path.join(published_path, "posts/")

    # If publishing for the first time, create new directory
    if not os.path.exists(published_path):
        create_fresh_live_dir(published_path)

    # Read in cached post_data
    post_data = read_json(os.path.join(published_path, ".pd_cache"))

    # Determine what needs to be published
    all_directories = [d for d in os.listdir(src_path)
                       if "." not in d]
    deleted_posts = get_deleted_posts(all_directories)
    new_posts = get_new_posts(all_directories, src_path, published_path)
    # print(deleted_posts, new_posts)
    publishing = (len(new_posts) > 0 or len(deleted_posts) > 0)

    # Delete any removed posts
    for post in deleted_posts:
        shutil.rmtree(os.path.join(posts_path, post))
        remove_post(post)  # deletes post from post_data

    # Publish any new posts
    generate_posts(new_posts, src_path, posts_path)  # updates post_data

    # Generate Index
    if publishing or True:
        add_search_index()  # add search data to post_data
        post_data = sorted(post_data, key=lambda x: x["date"], reverse=True)
        generate_index(posts_path, published_path)

        # And update cache data files
        last_updated = get_last_update(posts_path)
        write_file(last_updated,
                   os.path.join(published_path, ".last_updated"))
        write_json(post_data,
                   os.path.join(published_path, ".pd_cache"))

    # copy resources
    res_source_path = os.path.join(config["blog"]["templates_path"],
                                   "resources/")
    res_pub_path = os.path.join(published_path, "resources/")
    # print(published_path, res_source_path, res_pub_path)
    shutil.rmtree(res_pub_path)
    shutil.copytree(res_source_path, res_pub_path)

    return (new_posts, deleted_posts)


# Upload Site
def upload_site(ftp):
    """ Upload full contents of site rooted at src """
    global config
    live_dir = config["blog"]["published_path"]
    remote_dir = config["blog"]["remote_path"]
    my_ftp.upload_dir(ftp, live_dir, remote_dir)


def upload_new_posts(ftp, posts):
    """Upload posts only"""
    published_path = config["blog"]["published_path"]
    remote_path = config["blog"]["remote_path"]
    # upload new posts
    for post in posts:
        src_path = os.path.join(published_path, 'posts', post)
        target_path = os.path.join(remote_path, 'posts', post)
        print(src_path, target_path)
        my_ftp.upload_dir(ftp, src_path, target_path)
    # upload changed index
    root = os.getcwd()
    ftp.cwd(remote_path)
    os.chdir(published_path)
    my_ftp.upload_file(ftp, 'index.html')
    # re-upload resources
    my_ftp.upload_dir(ftp, 'resources', 'resources')
    os.chdir(root)  # change back


def delete_posts(ftp, posts):
    """ Delete any old folder from server """
    posts_path = os.path.join(config["blog"]["remote_path"], 'posts')
    ftp.cwd(posts_path)
    for post in posts:
        if post in ftp.nlst():
            ftp.cwd(post)
            for f in ftp.nlst():
                if f not in ['.', '..']:
                    print(f)
                    print(ftp.delete(f))
            ftp.cwd('..')
            # print(ftp.pwd())
            ftp.rmd(post)


def upload_site_data():
    pass


if __name__ == "__main__":
    """Publish markdown files from source as HTML"""
    parser = argparse.ArgumentParser()
    # default_directory, default_target = "src_test/", "live_test/"
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
        sys.exit()

    set_config_values(args.config)
    new_posts, deleted_posts = publish()

    if args.forceupload:
        # Site published and uploaded to server
        ftp = my_ftp.connect(config["ftp"]["host"], config["ftp"]["user"],
                             config["ftp"]["pw"])
        upload_site(ftp)
        my_ftp.quit(ftp)
    elif args.upload:
        ftp = my_ftp.connect(config["ftp"]["host"], config["ftp"]["user"],
                             config["ftp"]["pw"])
        upload_new_posts(ftp, new_posts)
        # delete_posts(ftp, deleted_posts)
        # upload_site_data(ftp)
        my_ftp.quit(ftp)



        # if published:
        #     new, deleted = published
        #     my_ftp.upload_index()
        #     if len(new) > 0:
        #         upload_posts(new)
        #         print("{0} new/changed posts uploaded to server."
        #               .format(len(new)))
        #     if len(deleted) > 0:
        #         my_ftp.delete_posts(deleted)
        #         print("{0} posts deleted from server.".format(len(deleted)))
        #     # finally upload index