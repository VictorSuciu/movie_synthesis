import numpy as np
import argparse
import sys
import json
import os
import re
from scipy.stats import mode as scipy_mode


def remove_imsdb_header(raw_script, writers):

    # look for the line where the writers are listed
    # for example "Written by Jared Bush & Phil Johnston"
    # and return all the lines after that one
    line_num = 0
    for line in raw_script:
        for w in writers:
            if w in line:
                return raw_script[line_num:]

        line_num += 1
    
    return None # could not find writer names in script

def count_indent_spaces(line):
    idx = 0
    while idx < len(line) and line[idx] == ' ':
        idx += 1
    
    return idx


def get_indent_stats(script):
    indent_dict = {}
    
    for line in script:
        if len(line.strip()) > 0:
            num_spaces = count_indent_spaces(line)
            indent_dict[num_spaces] = indent_dict.get(num_spaces, 0) + 1
    
    hist = [[size, num_occur] for size, num_occur in indent_dict.items()]
    hist.sort(key=lambda x: x[1])

    return hist


def get_description_indents(script):
    num_spaces = set()
    for line in script:
        exp = r'^ *[0-9]*[a-zA-Z]*? *'
        if 'EXT. ' in line or 'INT. ' in line:
            print(line)
            result = re.search(exp, line).group(0)
            print(len(result), f'"{result}"')
            num_spaces.add(len(re.search(exp, line).group(0)))
        
    return num_spaces


def analyse_indent_pattern(script):
    num_spaces = []
    for line in script:
        if len(line.strip()) > 0:
            cur_spaces = count_indent_spaces(line)
            num_spaces.append(cur_spaces)
    
    return num_spaces
        

def top_3_mode(num_spaces):
    num_spaces = np.array(num_spaces)
    mode1 = scipy_mode(num_spaces).mode[0]
    mode2 = scipy_mode(num_spaces[num_spaces != mode1]).mode[0]
    mode3 = scipy_mode(num_spaces[(num_spaces != mode1) & (num_spaces != mode2)]).mode[0]

    return np.sort([mode1, mode2, mode3])


def annotate_scriptbase_script(script, indents):
    an_script = []
    annotations = {
        indents[0]: 'description',
        indents[1]: 'dialogue',
        indents[2]: 'character'
    }
    for line in script:
        stripped_line = line.strip()

        if len(stripped_line) > 0:
            line_type = annotations.get(count_indent_spaces(line), 'unknown')
            
            tokens = stripped_line.split()

            # sometimes the charactet and dialogue direction are on the same line
            # For example "PRESIDENT (VO)". This if statement handles this special case
            if line_type == 'character' and stripped_line[-1] == ')':
                char_dir_split = stripped_line.split('(')
                an_script.append(
                    ['character', char_dir_split[0].strip()]
                )
                an_script.append(
                    ['diologue_direction', '(' + char_dir_split[1].strip()]
                )
            else:
                if line_type == 'description' and (tokens[0] =='INT.' or tokens[0] == 'EXT.'):
                    line_type = 'set'
                elif line_type == 'dialogue' and stripped_line[0] =='(' and stripped_line[-1] == ')':
                    line_type = 'diologue_direction'

                an_script.append(
                    [line_type, stripped_line]
                )

    return an_script


def condense_an_script(an_script):
    con_script = []
    con_line = ''
    pre_an = an_script[0][0]

    for i, (an, line) in enumerate(an_script):
        
        if an != pre_an:
            con_script.append([pre_an, con_line])
            con_line = ''

        con_line += line + ' '
        
        if i == len(an_script) - 1:
            con_script.append([an, con_line])
        pre_an = an

    return con_script


def read_scriptbase(j_dir):
    dirs = [os.path.join(j_dir, d) for d in os.listdir(j_dir) if os.path.isdir(os.path.join(j_dir, d))]
    an_scriptbase = []
    for i, d in enumerate(dirs):
        print(f'{i+1} / {len(dirs)}')
        script_fp = os.path.join(d, 'processed/script_clean.txt')
        with open(script_fp, 'r') as script_file:
            script = [
                line.replace('\n', '').replace('\r', '').replace('\t', ' '*4)
                for line in script_file.readlines()
            ]

        indents = top_3_mode(analyse_indent_pattern(script))
        print(indents)
        if len(indents) == 3:
            an_script = annotate_scriptbase_script(script, indents)
            con_an_script = condense_an_script(an_script)
            an_scriptbase.append([os.path.basename(d), con_an_script])
        
    return an_scriptbase


def parse_script(script_dict):
    print()
    script = script_dict['raw_script']
    script = [line.replace('\t', ' '*4) for line in script]
    
    indent_hist = get_indent_stats(script)
    for row in indent_hist:
        print(row)
    print()
    
    des_indents = get_description_indents(script)
    print(des_indents)

    analyse_indent_pattern(script)


def parse_all_scripts(scripts):
    for script_dict in scripts:
        parse_script(script_dict)


def write_script_to_file(scripts, idx, out_dir):
    out_fp = os.path.join(out_dir, f'script_{idx}.txt')
    out_file = open(out_fp, 'w')
    
    for line in scripts[idx]['raw_script']:
        out_file.write(line + '\n')
    
    out_file.close()

    print()
    print(f'Wrote script {idx} ("{scripts[idx]["title"]}" {scripts[idx]["date"]}) to {out_fp}')


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('script_fp', type=str)
    parser.add_argument('-wi', '--write_idx', type=int)
    parser.add_argument('-wd', '--write_dir', type=str)
    parser.add_argument('-p', '--parse', action='store_true')
    parser.add_argument('-pi', '--parse_idx', type=int)
    args = parser.parse_args(sys.argv[1:])

    script_file = open(args.script_fp, 'r')
    scripts = [json.loads(line) for line in script_file.readlines()]
    script_file.close()

    print()
    print(f'Read {len(scripts)} scripts')

    if args.write_idx != None and args.write_dir != None:
        write_script_to_file(scripts, args.write_idx, args.write_dir)
    
    if args.parse:
        if args.parse_idx != None:
            parse_script(scripts[args.parse_idx])
        else:
            parse_all_scripts(scripts)

    print()


def run2():
    parser = argparse.ArgumentParser()
    parser.add_argument('scriptbase_dir', type=str)
    args = parser.parse_args(sys.argv[1:])

    an_scripts = read_scriptbase(args.scriptbase_dir)
    for line in an_scripts[0][1]:
        print(line)
    
    print(an_scripts[0][0])
    print(len(an_scripts))



if __name__ == '__main__':
    run2()
