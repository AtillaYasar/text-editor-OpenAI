import tkinter as tk
import tkinter.font
from datetime import datetime
import os, time, json, openai, threading, sys, requests
import embedder  # for getting cosine similarity between 2 strings or lists of strings (or list of strings and strings)

import logging
logging.basicConfig(filename='log_DEBUGlevel.log', encoding='utf-8', level=logging.DEBUG)
logging.info('start logging, level=debug')

use_mock = False
class Mock:
    def encode(self):
        return [0]
    def decode(self):
        return '0'
if use_mock:
    tokenizer = Mock()
    logging.info('using mock tokenizer')
else:
    t0 = time.time()
    from transformers import GPT2Tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    logging.info(f'using real tokenizer, importing took {time.time()-t0} seconds')

'''
tokenize and untokenize functions require this at the top:
    from transformers import GPT2Tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
'''
# string --> list of token ids
def tokenize(string):
    t0 = time.time()

    tokens = tokenizer.encode(string, max_length=8000, truncation=True)

    logging.info(f'tokenizing took {time.time()-t0} seconds')
    logging.info(f'last string was {len(string)} tokens')
    return tokens
# list of token ids --> string
def untokenize(tokens):
    t0 = time.time()

    string = tokenizer.decode(tokens)

    logging.info(f'tokenizing took {time.time()-t0} seconds')
    return string

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

def call_openai(settings):
    # little shortcircuit for testing things.
    testing = use_mock
    if testing:
        prompt = settings['prompt']
        n = settings['n']
        return [f'{i} response {i}' for i in range(int(n))]

    completions = openai.Completion.create(**settings)
    responses = [choice['text'] for choice in completions.choices]
    if store_history:
        call_history.append({'prompt':tokenize(settings['prompt']), 'settings':settings, 'responses':list(map(tokenize,responses))})
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


def color_full(string, directions):
    pass

def generate(prompt):
    full_text = t.get(1.0, 'end')[:-1]
    
    flag = 'emb'
    if f'[{flag}]' in full_text and f'[/{flag}]' in full_text:
        embs = [string[1:-1] for string in between2(full_text, f'[{flag}]', f'[/{flag}')]
    else:
        embs = None
    
    full_text = t.get(1.0, 'end')[:-1]
    api_settings = open_json('api_settings.json')

    # creates a function that if called, will call the openai api and print the outputs in a nice way.
    def call_and_show():
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
        right = symbols['block'] + symbols['thick arrow right']
        joiner = '+'        
        components = []
        combine = lambda:f' {joiner} '.join(components) + f' {right} '

        components.append(col('cy','[ Prompt ]'))
        print(combine())
        print(prompt[-1500:])

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

        def show_embeddings(scores, arggrid):
            for i in range(len(scores)):
                for j in range(len(scores[i])):
                    emb1, emb2 = arggrid[i][j]
                    score = scores[i][j]
                    
                    print(col('gr', 'emb1:'))
                    print(emb1)
                    print(col('gr', 'emb2:'))
                    print(emb2)
                    print(col('ma', 'score:'))
                    print(score)
                    print(col('cy','='*10))

        if embs != None:
            print(col('cy', '============ embeddings coming ============='))
            scores, arggrid = compare_emb(embs, responses)
            show_embeddings(scores, arggrid)
            print(col('ma', '============ grid coming ============='))
            [print(row) for row in scores]
    
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



# (for development,) for accessing tkinter variables while the app is still running
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

# toggling the window being 'on top' or not
def toggle_topmost():
    window = root
    tup = window.attributes()
    ix = tup.index('-topmost')
    if tup[ix+1] == 1:
        window.attributes('-topmost', False)
    else:
        window.attributes('-topmost', True)

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

# find the previous line
def get_previous():
    i = int(t.index('insert').partition('.')[0])-1
    prev_line = t.get(f'{i}.0 linestart', f'{i}.0 lineend')
    return prev_line

def on_release(event):
    hotkeys.event_to_action(event_type='on release', event=event)

def move_insertion(text_widget, right, down):
    w = text_widget
    pos = w.index('insert')
    line, column = map(int,pos.split('.'))
    t.mark_set("insert", "%d.%d" % (line + down, column + right))

# replaces the current line with something else
def replace_current(widget, replacer_function):
    # get current line
    # delete current line
    # add something else
    w = widget
    f = replacer_function

    current = w.get('insert linestart', 'insert lineend')  # btw current instead of insert would get the cursor line
    w.delete('insert linestart', 'insert lineend')
    w.insert('insert linestart', f(current))

'''
When the hotkey is pressed, replaces the current line where the insertion position is, with something else.

Example:
[replacement]
>>>user('___')
>>>ai('
[/replacement]

Effect of the above text being in the text editor:
    - `hey i wanna play a game` in the current line
    - press the hotkey  (ctrl+r as of writing this)
    -->
    line is replaced with:
`
>>>user('hey i wanna play a game')
>>>ai('
`

so, ___ is the placeholder marker there.
'''
def replacement(event):

    full = t.get('1.0', 'end')
    lang = 'replacement'
    if not f'[{lang}]' in full or not f'[/{lang}]' in full:
        e = f'you used hotkey_replace without any [{lang}] code'
        raise Exception(e)

    replacement_code = full.partition(f'[{lang}]')[2].partition(f'[/{lang}]')[0][1:-1]
    current_marker = '___'
    if current_marker not in replacement_code:
        e = f'the marker is {current_marker}'
        raise Exception(e)

    before, placeholder, after = replacement_code.partition(current_marker)
    string_transformer = lambda placeholder:before + placeholder + after
    
    # replace current line, using a `string-->string` function, to get the new line
    replace_current(w, string_transformer)  # lambda current:f">>>user('{current}')\n>>>ai('"
    if safe_mode == False:
        prompt = get_prompt(event)
        generate(prompt)

def hotkey_test(event):
    pass

# calls moderations endpoint on "prompt" and shows results neatly
def check_moderations(prompt):
    def call_and_show():
        # Set the text you want to check in the 'input' field
        data = {'input': prompt}

        # Set the Content-Type and Authorization headers
        headers = {
          'Content-Type': 'application/json',
          'Authorization': f'Bearer {api_key}'
        }

        # Make the request to the moderation endpoint
        response = requests.post('https://api.openai.com/v1/moderations', headers=headers, json=data).json()

        # Print the response
        categories = response['results'][0]['categories']
        scores = response['results'][0]['category_scores']
        flagged = response['results'][0]['flagged']        

        if flagged:
            print('flagged:', col('re',flagged))
        else:
            print('flagged:', col('gr',flagged))
        for k,v in categories.items():
            v = col('re', v) if v == True else col('gr', v)
            score = float(scores[k])
            print(f'{k}:{v}', round(score, 3))
            
        for k,v in scores.items():
            if scores.keys() == categories.keys():
                break
            print(f'{k}:{v}')
    newThread(call_and_show())

'''
retrieves one of 2 pieces of text:
    - selected text if there is any, if not:
    - text from the beginning of the text widget, until the "insert" point (where you type)
'''
def get_prompt(event):
    try:
        event.widget.selection_get()
    except:
        prompt = event.widget.get(1.0, 'insert')
    else:
        prompt = event.widget.selection_get()
    return prompt

# uses Hotkeys class instance to deal with all commands.
#   except for the color highlighting, that part is in need of a refactor, but is just shoved into a corner for now.
highlight_counter = 1
def on_press(event):
    hotkeys.event_to_action(event_type='on press', event=event)
    handle_colors(event)

# code to highlight text, is messy and ugly.
def handle_colors(event):
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

def cshow(arg=''):
    if 'ram_aid.json' in os.listdir(os.getcwd()):
        return ', '.join(open_json('ram_aid.json').keys())
    else:
        return None

def cfont(n):
    t.config(font=('Comic Sans', n))

def cempty(arg=''):
    t.delete(1.0, 'end')

# the purpose is to use timer.go() and timer.stop() from the UI, by using a tk.Entry widget (called evalthis)
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

def find_script(full_text, lang):
    return [string[1:-1] for string in between2(full_text, start=f'[{lang}]', end=f'[/{lang}]')]

# for using hotkeys to interact with functions from within a tkinter tk.Text widget.
class Hotkeys:
    def __init__(self):
        self.bindings = {}
        self.instructions = []

        self.allowed_actions = [
            'moderate',
            'generate',
            'count words',
            'toggle topmost',
            'replacement',
            'autoedit'
        ]
        self.debug = False

    
    # event_type:str, event:tkinter event
    #   if the to_call stuff is too annoying and ugly, just ignore it, and call whatever function immediately
    def event_to_action(self, event_type, event):
        ctrl_held = event.state == 12
        alt_held = event.state == 131080
        other = event.keysym

        report = []

        # turning the pressed hotkey into something managable
        if ctrl_held:
            b = f'ctrl+{other}'
        elif alt_held:
            b = f'alt+{other}'
        else:
            b = other
        
        # for debug
        report.append(json.dumps({
            'reality':{
                'pressed hotkey':b,
                'event type':event_type,
                'ctrl_held':ctrl_held,
                'alt_held':alt_held,
                'other':other
            }
        }, indent=2))
        
        # i feel like this if elif elif elif structure has to exist at some point.
        #   at some point, the abstractions hit bedrock. no need to put that off endlessly.
        for ins in self.instructions:
            report.append('start instruction')
            report.append(json.dumps({'instruction':ins}, indent=2))  # for debug

            c1 = ins['event type'] == event_type
            c2 = ins['binding'] == b
            c3 = ins['action'] in self.allowed_actions
            report.append( '\t' + ', '.join([col('gr','True') if c == True else col('re','False') for c in (c1,c2,c3)]) )  # for debug

            if c1 and c2 and c3:
                report.append(f'\tdoing action, a={ins["action"]}')  # for debug

                a = ins['action']
                if a == 'moderate':
                    prompt = get_prompt(event)
                    to_call = lambda:check_moderations(prompt)
                elif a == 'generate':
                    prompt = get_prompt(event)
                    to_call = lambda:generate(prompt)
                elif a == 'count words':
                    prompt = get_prompt(event)
                    to_call = lambda:root.title('wordcount: ' + str(len(prompt.split(' '))))
                elif a == 'toggle topmost':
                    to_call = lambda:toggle_topmost()
                elif a == 'replacement':
                    to_call = lambda:replacement(event)
                elif a == 'autoedit':
                    lang = 'autoedit'
                    all_chunks = find_script(t.get(1.0, 'end'), lang)
                    f1 = lambda:report.append(f'{lang} all_chunks:{all_chunks}')
                    
                    if all_chunks == []:
                        to_call = f1
                    else:
                        code = all_chunks[0]
                        for line in code.split('\n'):
                            left, right = line.split(' = ')
                            if left == 'next':
                                nxt = right
                            elif left == 'prev contains':
                                prev = right
                            else:
                                raise Exception('autoedit code is wrong')
                        if prev in get_previous():
                            # adds nxt at the current typing position
                            f2 = lambda:t.insert('insert', nxt)
                            to_call = (f1, f2)
                        else:
                            to_call = f1
                else:
                    e = f'action {a} does not exist, ins = {ins}' + str(a == 'moderate')
                    raise Exception(e)
                    to_call = lambda:report.append('raised exception')
                
                report.append(f'calling function for {a}')
                if type(to_call) in (list, tuple):
                    for f in to_call:
                        f()
                else:
                    to_call()
                report.append('done calling function')
            else:
                report.append(f'\tnot doing action, a={ins["action"]}')
            report.append('end instruction')

        if self.debug:
            print('=== REPORT START ===')
            for line in '\n'.join(report).split('\n'):
                print(f'\t{line}')
            print('=== REPORT end ===')

    def add_hotkey(self, d):
        # some validation
        if type(d) is not dict:
            e = f'd is not dict, d={d}'
            raise Exception(e)
        for key in [
            'event type',
            'description',
            'binding',
            'action'
        ]:
            if key not in d:
                e = f'key {key} not in d'
                raise Exception(e)
        if d['action'] not in self.allowed_actions:
            e = f'action not allowed, action={d["action"]}, d={d}'
            raise Exception(e)
        
        # doing this in 2 ways.
        # complicated way:
        # add binding if its ctrl+ or alt+ something, or an F key. else, dont add.
        b = d['binding']
        if 'ctrl+' in b or 'alt+' in b:
            if b in self.bindings:
                print(f'overriding {self.bindings[b]} with {d}')
            self.bindings[b] = d
        elif b[0] == 'F' and b[1:] in [str(i) for i in range(0, 13)]:
            if b in self.bindings:
                print(f'overriding {self.bindings[b]} with {d}')
            self.bindings[b] = d
        else:
            print('did not add d=', d)
    
        # simple way:
        self.instructions.append(d)

        # for debugging
        stringify = lambda d:json.dumps(d, indent=2, default=lambda o:str(o))
        print(f'new bindings: {stringify(self.bindings)}')
        print(f'new instructions: {stringify(self.instructions)}')

compare_emb = embedder.compare_emb
history_path = 'call_history.json'
store_history = True
if history_path in os.listdir() and store_history:
    call_history = open_json(history_path)


# setting default generation settings, and getting the api key
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

# setting some basic stuff
root = tk.Tk()
root.config(background='black')
root.geometry('1000x600-0+0')
default_app_title = 'text editor'
root.title(default_app_title)
set_word_boundaries(root)

# tk.Entry for running eval()
evalthis = tk.Entry(root, width=50)
evalthis.pack()
evalthis.bind('<Return>', lambda *a:printeval())

# colors and stuff
c1 = 'grey'
c2 = 'black'
sbg = 'cyan'
textSettings = {
    'fg':c1,
    'bg':c2,
    'insertbackground':'white',
    'selectbackground':c1,
    'selectforeground':sbg,
    'width':150,
    'height':50,
    'font':('Comic Sans','14')
}
frameSettings = {
    'fg':c1,
    'bg':c2,
    'width':150,
    'height':50
}

t = tk.Text(root, **textSettings)
t.pack()

# defining how many spaces a tab inserts
w = t
font = tkinter.font.Font(font=w['font'])
tab = font.measure(' '*4)
w.config(tabs=tab)
default_color_line = '1-green, 2-red, 3-cyan, 4-black, 5-grey, 6-orange, 7-brown, 8-purple, 0-violet'

# inserting default text
default_present = False
if 'ram_aid.json' in os.listdir(os.getcwd()):
    collection = open_json('ram_aid.json')
    if 'default' in collection:
        t.delete(1.0, 'end')
        cload('default')
        default_present = True
if default_present == False:
    t.insert('end', '\n'.join([
        '',
        '',
        '',
        'normal color (5-grey)',
        'generic highlight (3-cyan)',
        'positive (6-orange)',
        'negative (8-purple)',
        default_color_line
    ]))

# misc
fancy = False
safe_mode = True
timer = Timer()

# for commands
t.bind('<KeyPress>', on_press)
t.bind('<KeyRelease>', on_release)
hotkeys = Hotkeys()  # where hotkey logic and behavior is managed.

# defining behavior for each hotkey
hotkey_settings = [
    {
        'binding':'ctrl+g',
        'action':'generate',
        'event type':'on press',
        'description':'generate text with openai api, and show outputs'
    },
    {
        'binding':'ctrl+m',
        'action':'moderate',
        'event type':'on press',
        'description':'check "safety" of text with openai api, and show results'
    },
    {
        'binding':'F1',
        'action':'toggle topmost',
        'event type':'on press',
        'description':'toggles topmost'
    },
    {
        'binding':'ctrl+q',
        'action':'count words',
        'event type':'on press',
        'description':'show the word count in the title..'
    },
    {
        'binding':'ctrl+r',
        'action':'replacement',
        'event type':'on press',
        'description':'using [replacement], replace the previous line with something else'
    },
    {
        'binding':'Return',
        'action':'autoedit',
        'event type':'on release',
        'description':'blank'
    }
]
for instruction in hotkey_settings:
    hotkeys.add_hotkey(instruction)


root.mainloop()




