import sys, os, markdown, operator, shutil, time, json, re, argparse
from wand.image import Image
from wand.display import display

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

def get_summary(html):
    """ Extract a sample of the post contents. 
        Expects some html in a string.
    """
    summary = html.split('\n')[2:4]
    summary = ''.join(summary)
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
	            index[keyword] = [p['name'],]
    return json.dumps(index)

def resize_and_copy(src, target):
    """ Takes any image files and downsizes then 
        copies to target.
    """
    # shutil.copyfile(os.path.join(src_path, file), 
                #     os.path.join(live_path, file))
    img = Image(filename=src)
    # print(img.size)
    if img.height > 550:
        with img.clone() as new_image:
            new_image.transform(resize='x550')
            new_image.save(filename=target)
    else:
        shutil.copyfile(src, target)
    
    
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
    shutil.rmtree(live_dir) 
    os.mkdir(live_dir)
    
    post_data = []
    for src_name in to_publish:
        src_path = os.path.join(src_dir, src_name)
        live_path = os.path.join(live_dir, src_name)
        md_file_exists = False
        os.mkdir(live_path)
        for file in os.listdir(src_path):
            if file.endswith(".md"):
                # code expects one and only one md file per folder.
                md_file_exists = True
                input_path, output_path = (
                    os.path.join(src_path,file), 
                    os.path.join(live_path,'index.html'))
                markdown.markdownFromFile(input=input_path, 
                    output=output_path, output_format="html5")
                pd = {"name": src_name}
                pd["html"] = open(output_path, 'r').read()
                pd["title"] = get_title(src_name)
                pd["date"] = get_date(pd["html"], src_name)
                pd["summary"] = get_summary(pd["html"])
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
            shutil.rmtree(live_path) # delete empty folder
    return post_data

def generate_index(post_data, live_dir, root):
    summary_posts, post_list, posts = '', '', 0
    for post in post_data:
        date = time.strftime("%Y-%m-%d", time.localtime(post['date']))
        if(posts < 3):
            link = ("Read more of: <a href='%s/index.html'>%s</a></li>\n"
                %(post['name'], post['title']))
            summary_posts += ("<article><h3>%s</h3>\
                    <p>%s</p><div>%s</div><p>...</p><p>%s</p></article>\n"
                    %(post['title'], date, post['summary'], link))
        posts += 1
        post_list += ("<li><a href='%s/index.html'>%s \
                <small>%s</small></a></li>\n"
                %('posts/'+post['name'], post['title'], date))
    replacements = {'{{first_post}}': summary_posts, 
        '{{link_list}}': post_list,
        '{{search_index}}': get_search_index_json(post_data),
    }
    wrap_and_write_post(replacements, 
        'templates/posts/index_template.html', 
        os.path.join(root,'index.html'))

    
def publish(src_dir):
    root = 'live'
    live_dir = os.path.join(root, 'posts/')
    to_publish = [directory for directory in os.listdir(src_dir) 
        if '.' not in directory]

    post_data = generate_posts(to_publish, src_dir, live_dir)
    post_data = add_search_index(post_data)
    post_data = sorted(post_data, key=lambda x: x['date'], reverse=True)
    
    generate_index(post_data, live_dir, root)
    

if __name__ == "__main__":
    """Publish markdown files from source as HTML
    """
    parser = argparse.ArgumentParser()
    default_directory = 'src_test/'
    parser.add_argument("-t", "--test", 
        help="Run doctests",
        action="store_true")
    parser.add_argument("path", 
        nargs='?', 
        default=os.path.join(os.getcwd(), default_directory),
        help="Path to source files (defaults to "+default_directory+")")
    args = parser.parse_args()
    
    if(args.test): 
        import doctest
        doctest.testmod()
    else: 
        publish(args.path)
    
    