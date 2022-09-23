import numpy as np
import csv
import sys
import os
import argparse
import re


def get_all_script_files(sb_dir):
    titleyr_to_files = {}
    for d in os.listdir(sb_dir):
        full_path = os.path.join(sb_dir, d)

        if os.path.isdir(full_path):
            profile_path = os.path.join(full_path, 'processed/profile.txt')
            web_html_path = os.path.join(full_path, 'jinni.html')
            
            with open(web_html_path, 'r') as web_html_file:
                year_line = ''
                for i in range(8): # get the 8th line in the file, containing the year
                    year_line = web_html_file.readline()
                year = int(re.search(r'\d\d\d\d', year_line.split(',')[-1]).group(0))

            with open(profile_path, 'r') as profile_file:
                title = profile_file.readline().replace('\n', '')
            
            titleyr_to_files[(title, year)] = (
                os.path.join(full_path, 'processed/script_clean.txt'),
                profile_path,
                web_html_path
            )

    return titleyr_to_files



# condensed movies required info
# file name to (movie title, year)


def read_cm_meta(cm_dir):
    ytid_to_info = {}
    info_to_ytid = {}
    titleyr = set()

    with open(os.path.join(cm_dir, 'metadata/clips.csv'), 'r') as clip_csv:
        csv_reader = csv.DictReader(clip_csv)
        # next(csv_reader.next) # TODO: test without next too

        for row in csv_reader:
            year = int(float(row['year']))
            ytid_to_info[row['videoid']] = (row['title'], year)
            info_to_ytid[(row['title'], year)] = info_to_ytid.get((row['title'], year), []) + [row['videoid']]
            titleyr.add((row['title'], year))

    return ytid_to_info, info_to_ytid, titleyr


def parse_cm_srt(srt_fp):
    srt_file = open(srt_fp, 'r')
    lines = srt_file.readlines()
    clean_lines = []
    for line in lines:
        line = line.replace('\n', '').strip()
        idx_re = re.match(r'\d+', line)
        
        # 00:00:06,109 --> 00:00:09,200
        time_re = re.match(r'\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d', line)
        
        if len(line) == 0:
            continue
        if idx_re != None and len(idx_re.group(0)) == len(line):
            continue
        if time_re != None and len(time_re.group(0)) == len(line):
            continue
        
        if len(clean_lines) == 0 or clean_lines[-1] != line:
            clean_lines.append(line)
    
    return ' '.join(clean_lines)


def read_cm_subtitles(cm_dir):
    video_dir = os.path.join(cm_dir, 'videos')
    ytid_to_subtitle = {}
    
    year_dirs = [
        os.path.join(video_dir, d)
        for d in os.listdir(video_dir)
        if os.path.isdir(os.path.join(video_dir, d))
    ]
    
    for y_dir in year_dirs:
        srt_fps = [
            os.path.join(y_dir, f)
            for f in os.listdir(y_dir)
            if f[-4:] == '.srt'
        ]
        
        for srt_fp in srt_fps:
            subtitle_str = parse_cm_srt(srt_fp)
            ytid = os.path.basename(srt_fp).split('.')[0]
            ytid_to_subtitle[ytid] = ytid_to_subtitle.get(ytid, []) + [subtitle_str]

    return ytid_to_subtitle    



def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('sb_dir', type=str)
    parser.add_argument('cm_dir', type=str)
    args = parser.parse_args(sys.argv[1:])
    
    sb_titleyr_to_files = get_all_script_files(args.sb_dir)
    ytid_to_info, info_to_ytid, cm_titleyr = read_cm_meta(args.cm_dir)

    num_movies = 0
    num_clips = 0
    for title, year in sb_titleyr_to_files:
        if (title, year) in cm_titleyr:
            num_movies += 1
            num_clips += len(info_to_ytid[(title, year)])
            # print(title, year, len(info_to_ytid[(title, year)]))
    
    
    print()
    print('total number of clips:', num_clips)
    print('total number of movies:', num_movies)
    print('avg clips per movie:', num_clips / num_movies)

    ytid_to_subtitle = read_cm_subtitles(args.cm_dir)
    print(ytid_to_subtitle)



if __name__ == '__main__':
    run()