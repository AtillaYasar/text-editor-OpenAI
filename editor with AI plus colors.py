import tkinter as tk
import tkinter.font
from datetime import datetime
import os, time, json, openai, threading, sys


# app has:
##    - CUSTOM HIGHLIGHTING OF TEXT
##         + select text and hit ctrl or alt + a number to change the background color or text color
##         + bottom line configures colors

##    - F1 to toggle window staying on top
##    - improved word boundaries (relative to base tkinter)
##    - tabsize set to 2 spaces

def text_append(path, appendage):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(appendage)

def text_create(path, content=''):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def text_read(fileName):
    with open(fileName, 'r', encoding='utf-8') as f:
        contents = f.read()
    return contents

def make_json(dic, filename):
    with open(filename, 'w', encoding="utf-8") as f:
        json.dump(dic, f, indent=2)
        f.close()

def open_json(filename):
    with open(filename, 'r', encoding="utf-8") as f:
        contents = json.load(f)
        f.close()
    return contents

history_path = 'call_history.json'
store_history = True
if history_path in os.listdir() and store_history:
    call_history = open_json(history_path)

def call_openai(settings):
    completions = openai.Completion.create(**settings)
    responses = [choice['text'] for choice in completions.choices]
    if store_history:
        call_history.append({'prompt':settings['prompt'], 'settings':settings, 'responses':responses})
        make_json(call_history, history_path)
    return responses

#basically for getting all the text between 2 given strings, in a big mess of a string, and putting them in a list
#plus an option to only get items with the strings in strings_list in it
def between2(mess,start,end,strings_list=None):
    mess = mess.split(start)
    for i in range(len(mess)):
        mess[i] = mess[i].partition(end)[0]
    if strings_list == None:
        return mess[1:]
    else:
        filtered_mess = []
        for i in mess[1:]:
            for string in strings_list:
                if string in i:
                    filtered_mess.append(i)
        return filtered_mess
    mess = mess.split(start)
    for i in range(len(mess)):
        mess[i] = mess[i].partition(end)[0]
    return mess[1:]

# executes a given function on a new thread, so that the app doesn't freeze while it is running
# because API calls take time.
def newThread(function):
    threading.Thread(target=function).start()

def simple_completion(prompt):
    settings = {
        'engine':'code-davinci-002',
        'prompt':prompt,
        'temperature':0.8,
        'max_tokens':50,
        'n':1,
        'stop':None
        }
    completions = openai.Completion.create(**settings)
    responses = [choice['text'] for choice in completions.choices]
    if store_history:
        call_history.append({'prompt':prompt, 'settings':settings, 'responses':responses})
        make_json(call_history, history_path)
    return responses[0]

symbols = {
    'gear':chr(15),
    'music':chr(14),
    'heart':chr(30),
    'wave':chr(126),
    'wall':chr(124),
    'floor':chr(95),
    'arrow right':chr(26),
    'arrow left':'<-',
    'arrow up':chr(24),
    'arrow down':chr(25),
    'block':chr(22),
    'thick arrow right':chr(16),
    'thick arrow left':chr(17),
    'smile empty':chr(1),
    'smile full':chr(2),
    'at':chr(64)
}

def generate(prompt):
    full_text = t.get(1.0, 'end')[:-1]
    api_settings = open_json('api_settings.json')
    # print({'prompt':prompt})
    # creates a function that if called, will call the openai api and print the outputs.
    def call_and_show():

        right = symbols['block'] + symbols['thick arrow right']
        joiner = '+'        
        components = []
        combine = lambda:f' {joiner} '.join(components) + f' {right} '

        components.append(col('cy','[ Prompt ]'))
        print(combine())
        print(prompt)

        api_settings['prompt'] = prompt

        responses = call_openai(api_settings)
        if '[attach]' in full_text and '[/attach]' in full_text:
            attached = True
            attachments = [string[1:-1] for string in between2(full_text, '[attach]', '[/attach')]
        else:
            attached = False
        for n, r in enumerate(responses):
            components.append(col('ma',f'[ Simulation {n+1} ]'))
            print(combine())
            print(r)

            if attached:
                for na, attachment in enumerate(attachments):
                    components.append(col('gr',f'[ Continuation {na+1} ]'))
                    print(combine())
                    print(attachment + simple_completion(prompt + r + attachment))
                    components = components[:-1]
            components = components[:-1]
                    
    newThread(call_and_show)  # runs the function on a seperate thread from tkinter, to prevent freezing.

def make_json(dic, filename):
    with open(filename, 'w', encoding="utf-8") as f:
        json.dump(dic, f, indent=2)
        f.close()

def open_json(filename):
    with open(filename, 'r', encoding="utf-8") as f:
        contents = json.load(f)
        f.close()
    return contents

# returns date and time in 2 lines (tab in front by default), as a string
def date_time(infront='\t'):
    #from datetime import datetime
    t = datetime.now()
    date = t.date()
    h = t.hour
    m = t.minute
    return f'{infront}{date}\n{infront}{h}{m}'

# writes string to a file, and the timestamp.
# uses date_time() function if available, otherwise just uses time.time()
# requires os. (because who the hell doesnt import os)
def log_thing(thing, directory, filename, create_txt=False):
    path = f'{directory}/{filename}'

    # log the thing.
    to_add = thing
    #to_add = to_add.replace(', '.join([f'{k}-{v}' for k,v in color_numbers.items()]), '')
    with open(path, 'a', encoding='utf-8') as f:
        f.write(to_add)

# improves word boundaries, so you can navigate better with (shift+) arrows
def set_word_boundaries(root):
    # this first statement triggers tcl to autoload the library
    # that defines the variables we want to override.  
    root.tk.call('tcl_wordBreakAfter', '', 0) 

    # this defines what tcl considers to be a "word". For more
    # information see http://www.tcl.tk/man/tcl8.5/TclCmd/library.htm#M19
    root.tk.call('set', 'tcl_wordchars', '[a-zA-Z0-9_.,]')
    root.tk.call('set', 'tcl_nonwordchars', '[^a-zA-Z0-9_.,]')



# when you press enter, checks the start of the line for key, and inserts value on the next line
my_name = 'Atilla'
other_name = 'Joe'
dialogue = {
    f'{my_name}: ':f'{other_name}:',
    f'{other_name}: ':f'{my_name}:'
    }

use_openai = 'api_key.txt' in os.listdir()
if use_openai:
    api_settings = {
        'engine':'code-davinci-002',
        'prompt':'Once upon a time',
        'temperature':0.8,
        'max_tokens':100,
        'n':1,
        'stop':None
        }
    api_settings = open_json('api_settings.json')
    
    api_key = text_read('api_key.txt')
    openai.api_key = api_key

root = tk.Tk()
root.config(background='black')
#root.attributes('-topmost', True)

root.geometry('1000x600-0+0')
default_app_title = 'text editor'

root.title(default_app_title)
set_word_boundaries(root)

# (for development,) for accessing tkinter variables while the app is still running
fancy = False
def printeval():
    text = evalthis.get()
    evaluation = str(eval(text))
    if evaluation != None:
        if fancy:
            print('\n'.join(['input', text, '', 'result', evaluation]))
        else:
            print(evaluation)
# because eval() doesn't let you do assignment
def toggle_fancy():
    global fancy
    if fancy:
        fancy = False
    else:
        fancy = True

evalthis = tk.Entry(root, width=50)
evalthis.pack()
evalthis.bind('<Return>', lambda *a:printeval())

c1 = 'grey'
c2 = 'black'
sbg = 'cyan'
textSettings = {
    'fg':c1, 'bg':c2, 'insertbackground':'white',
    'selectbackground':c1, 'selectforeground':sbg, 'width':150,
    'height':50, 'font':('Comic Sans','13')
    }
frameSettings = {
    'fg':c1, 'bg':c2, 'width':150,
    'height':50
    }

'''
t = tk.Text(root, fg=c1, bg=c2, insertbackground='white',
            selectforeground=c1, selectbackground=sbg,
            width=150, height=50,
            font=('Comic Sans', '13'))'''
t = tk.Text(root, **textSettings)

w = t
font = tkinter.font.Font(font=w['font'])
tab = font.measure(' '*4)
w.config(tabs=tab)

# for outputs
class Window:
    def __init__(self):
        output_frame = tk.Frame(root, **frameSettings)


# toggling the window being 'on top' or not
def toggle_topmost():
    window = root
    tup = window.attributes()
    ix = tup.index('-topmost')
    if tup[ix+1] == 1:
        window.attributes('-topmost', False)
    else:
        window.attributes('-topmost', True)

# logs contents of editor. and re-creates color dictionary
def func():
    
    contents = t.get(1.0, 'end')[:-1]

    timestamp = date_time()
    edge = '---------------------'
    to_log = '\n' + '\n'.join([edge,timestamp,contents,edge])
    
    directory = r'C:\Users\Gebruiker\Desktop\mental tools'
    filename = 'ram_aid_log.txt'
    
    log_thing(to_log, directory, filename)

    status_message(f'Saved in ram_aid.txt')

t.pack()

def get_color(index, key):
    text = t
    #print(text.tag_names(index)[::-1])
    #print(text.tag_names(index))
    for tag in text.tag_names(index)[::-1]:
        fg = text.tag_cget(tag, key)
        if fg != "":
            return fg
    return text.cget(key)

def get_highlight_hotkeys(line):
    '''
str(line) -> dict(highlight_hotkeys)

- in on_press, highlight_hotkeys is used to see how to color a selected piece of text
- ctrl + a number changes the foreground, alt + a number changes the background
'''
    color_numbers = {tup[0]:tup[1] for tup in [section.split('-') for section in line.split(', ')]}
    highlight_hotkeys = {'alt':{k:{'background':v} for k,v in color_numbers.items()},
                     'control':{k:{'foreground':v} for k,v in color_numbers.items()}}
    return highlight_hotkeys

default_color_line = '1-green, 2-red, 3-cyan, 4-black, 5-grey, 6-orange, 7-brown, 8-purple, 0-violet'

t.insert('end', '\n'.join(['', '', '',
                           'normal color (5-grey)', 'generic highlight (3-cyan)', 'positive (6-orange)', 'negative (8-purple)',
                           default_color_line]))

def on_release(event):
    if event.keysym == 'Return':
        i = int(t.index('insert').partition('.')[0])-1
        cur_line = t.get(f'{i}.0 linestart', f'{i}.0 lineend')

        for person in dialogue:
            if cur_line.startswith(person):
                t.insert('insert', dialogue[person])
                break

highlight_counter = 1
def on_press(event):
    if use_openai:
        # this first part will call the openai api if you press ctrl+g
        # if you select text, itll use that as the prompt. if not, itll use the text up to where the cursor is
        if event.state == 12 and event.keysym == 'g':
            try:
                event.widget.selection_get()
            except:
                prompt = event.widget.get(1.0, 'insert')
            else:
                prompt = event.widget.selection_get()

            generate(prompt)
    '''
Escape -> write to ram_aid_log.txt
control/alt + number -> change highlighted text:
    control for text color
    alt for background color

( potential improvements: other hotkey system than elifelifelifelif, remove need for global highlight_counter (maybe using
    a class), remove code duplication in alt/control branching, remove need for colors['selectbackground']=sgb )
'''
    global highlight_counter
    widget = event.widget

    # code duplication. key 'alt' in one case, key 'control' in another
        # only difference in following bifurcation is:
            # to get 'colors' from highlight_hotkeys you use the key 'alt' in one case, and 'control' in another
    if event.state == 131080: # if 'alt' is held
        lastline = t.get(1.0, 'end').split('\n')[-2]
        highlight_hotkeys = get_highlight_hotkeys(lastline)
        n = event.keysym
        
        colors = highlight_hotkeys['alt'].get(n, False) # check if number is in dictionary, if yes, continue
        if colors:
            # this is so that the color you pick for the background is the one actually shown (because the text is selected)
                # and then when a key other than ctrl or alt is pressed, it fixes the selectbackground.
            colors['selectbackground'] = colors['background']
            
            first,last = widget.index('sel.first'), widget.index('sel.last') # selection indices
            widget.tag_add(highlight_counter, first, last) # add mark
            widget.tag_config(highlight_counter, **colors) # configure mark using colors dictionary, which uses highlight_hotkey
    
            existing_settings = {key:get_color(first,key) # get existing settings
                                 for key in ('foreground','background','selectforeground','selectbackground')}
            highlight_counter += 1 # count up the thingy
            
    elif event.state == 12: # if 'control' is held
        lastline = t.get(1.0, 'end').split('\n')[-2]
        highlight_hotkeys = get_highlight_hotkeys(lastline)
        n = event.keysym
        
        colors = highlight_hotkeys['control'].get(n, False) # check if number is in dictionary, if yes, continue
        if colors:
            first,last = widget.index('sel.first'), widget.index('sel.last') # selection indices
            widget.tag_add(highlight_counter, first, last) # add mark
            widget.tag_config(highlight_counter, **colors) # configure mark using colors dictionary, which uses highlight_hotkey
    
            existing_settings = {key:get_color(first,key) # get existing settings
                                 for key in ('foreground','background','selectforeground','selectbackground')}
            highlight_counter += 1 # count up the thingy
    elif event.keysym == 'Escape':
        func()
    elif event.keysym == 'F1':
        toggle_topmost()

'''
if 'backups' not in os.listdir(os.getcwd()):
    os.mkdir('backups')
def backup(name, entry, j):
    if name in j:
        t = time.time()
        j[name] = entry
        make_json(j, f'{name}-{t}.json')
'''

# returns an ansi escape sequence to color a string.  (ft is "first two", s is "string")
def col(ft, s):
    # black-30, red-31, green-32, yellow-33, blue-34, magenta-35, cyan-36, white-37
    u = '\u001b'
    numbers = dict([(string,30+n) for n, string in enumerate(('bl','re','gr','ye','blu','ma','cy','wh'))])
    n = numbers[ft]
    return f'{u}[{n}m{s}{u}[0m'

# the following are 4 functions that are for convenient use via the "evalthis" tk.Entry widget (which runs eval on the input)
    # cstore, cclear, cload, cshow
def cstore(name):
    if 'ram_aid.json' not in os.listdir(os.getcwd()):
        make_json({}, 'ram_aid.json')
    full_catalogue = open_json('ram_aid.json')
    
    ranges = {}
    for tup in t.dump(1.0, 'end', tag=True):
        number = tup[1]

        if number not in ranges:
            ranges[number] = {}

        ranges[number]['settings'] = {key:t.tag_cget(number, key) for key in ['foreground']}

        if tup[0] == 'tagon':
            ranges[number]['tagon'] = tup[2]
        elif tup[0] == 'tagoff':
            ranges[number]['tagoff'] = tup[2]
            
    ranges = dict(sorted(ranges.items(), key=lambda tup:int(tup[0])))
    j = {'text':t.get(1.0, 'end')[:-1],
         'ranges':ranges}
    full_catalogue[name] = j

    make_json(full_catalogue, 'ram_aid.json')

    default_app_title = name
    status_message(f'succesful')

def cscrub(arg=''):
    for number in list(set([tup[1] for tup in t.dump(1.0, 'end', tag=True)])):
        t.tag_delete(number)

def cdelete(name):
    catalogue = open_json('ram_aid.json')
    
    if name in catalogue:
        del catalogue[name]
        make_json(catalogue, 'ram_aid.json')
        message = 'succesful'
    else:
        message = 'unsuccesful'
        
    status_message(f'{message}')
cremove = cdelete # i just cannot seperate these 2 words.

def status_message(message, milliseconds=500):
    root.title(message)
    root.after(milliseconds, lambda *a:root.title(default_app_title))

def cload(name, replace=True):
    global highlight_counter

    collection = open_json('ram_aid.json')
    if name not in collection:
        message = 'wrong key'
    else:
        j = collection[name]
        ranges = j['ranges']
        text = j['text']
        #print(f'ranges:{ranges}')
        
        if replace:
            t.delete(1.0, 'end')
        t.insert(1.0, text)
        highest = highlight_counter+1000
        for n, (number, d) in enumerate(ranges.items()):
            first, last = d['tagon'], d['tagoff']
            #print(f'first:{first}, last:{last}')
            settings = d['settings']
            #print(f'settings:{settings}')
            t.tag_add(n, first, last)
            t.tag_config(n, **settings)
            highest = max(int(number), highest)
            #print()
        highlight_counter = highest
        
        default_app_title = name
        message = 'succesful'

    status_message(message)

def tempload(name, replace=True):
    global highlight_counter

    collection = open_json('temp.json')
    if name not in collection:
        message = 'wrong key'
    else:
        j = collection[name]
        ranges = j['ranges']
        text = j['text']
        #print(f'ranges:{ranges}')
        
        if replace:
            t.delete(1.0, 'end')
        t.insert(1.0, text)
        highest = highlight_counter+1000
        for n, (number, d) in enumerate(ranges.items()):
            first, last = d['tagon'], d['tagoff']
            #print(f'first:{first}, last:{last}')
            settings = d['settings']
            #print(f'settings:{settings}')
            t.tag_add(n, first, last)
            t.tag_config(n, **settings)
            highest = max(int(number), highest)
            #print()
        highlight_counter = highest
        
        default_app_title = name
        message = 'succesful'

    status_message(message)


if 'ram_aid.json' in os.listdir(os.getcwd()):
    collection = open_json('ram_aid.json')
    if 'default' in collection:
        t.delete(1.0, 'end')
        cload('default')

def cshow(arg=''):
    if 'ram_aid.json' in os.listdir(os.getcwd()):
        return ', '.join(open_json('ram_aid.json').keys())
    else:
        return None

def tempshow(arg=''):
    if 'temp.json' in os.listdir(os.getcwd()):
        return ', '.join(open_json('temp.json').keys())
    else:
        return None


def cfont(n):
    t.config(font=('Comic Sans', n))

def cempty(arg=''):
    t.delete(1.0, 'end')

# the purpose is to use timer.go() and timer.stop() from the UI, by using the tk.Entry widget (called evalthis)
class Timer:
    def __init__(self):
        self.starttime = None
        self.going = False
        self.scale = 's'

    def show_time(self, increment):
        if self.going:
            distance = time.time()-self.starttime
            if self.scale == 's':
                root.title( str(int(round(distance,0)) ))
            elif self.scale == 'm':
                root.title( str(int(round(distance/60),0)) )
            elif self.scale == 'h':
                root.title( str(int(round(distance/3600),0)) )
                
            root.after(increment, lambda:self.show_time(increment))

    # meant for use from the tk.Entry widget that lets you run eval.
    def go(self, increment=1000):
        self.starttime = time.time()
        self.going = True
        self.show_time(increment)
    def start(self, increment=1000):
        self.go(increment)

    def stop(self):
        self.going = False
        root.title(default_app_title)

    def reset(self):
        self.go()


timer = Timer()

t.bind('<KeyPress>', on_press)
t.bind('<KeyRelease>', on_release)

root.mainloop()






