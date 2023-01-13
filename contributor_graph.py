import git
import datetime, time
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pathlib

repo_path = input('input target repository path >>')
repo = git.Repo(repo_path)
repo_path_obj = pathlib.Path(repo_path)

author_to={}
since_str = input('input since date Y-M-D >>')
since_date = datetime.datetime.strptime(since_str, '%Y-%m-%d')
until_str = input('input until date Y-M-D >>')
until_date = datetime.datetime.strptime(until_str, '%Y-%m-%d')

set_first_date = False
for item in repo.iter_commits():
    commit_date = datetime.datetime.fromtimestamp(item.committed_date)
    if not(commit_date < until_date) :
        continue
    if not(since_date < commit_date) :
        break
    if len(item.parents) > 1 :
        continue # マージコミット除外
    if not set_first_date :
        last_date = commit_date
        set_first_date = True
    old_date = commit_date
    file_list = item.stats.files
    for file_name in file_list:
        insertions = file_list.get(file_name).get('insertions')
        deletions = file_list.get(file_name).get('deletions')
        lines = file_list.get(file_name).get('lines')
        if item.author.name in author_to :
            author_to[item.author.name][0] += insertions
            author_to[item.author.name][1] += deletions
        else:
            author_to[item.author.name] = [insertions, deletions]

sorted_data = sorted(author_to.items(), key=lambda x:(x[1][0]+x[1][1]))
print(sorted_data)

matplotlib.use('Agg')
left = np.arange(len(sorted_data))
labels = [ data[0] for data in sorted_data]
ins_height = [ data[1][0] for data in sorted_data]
del_height = [ data[1][1] for data in sorted_data]
bar_width = 0.3
plt.bar(left, ins_height, color='r', width=bar_width, align='center')
plt.bar(left+bar_width, del_height, color='b', width=bar_width, align='center')
plt.xticks(left+bar_width/2, labels, rotation=30, fontsize='small')
plt.tight_layout()
date_range_str = '(' + old_date.strftime('%Y%m%d') + '-' + last_date.strftime('%Y%m%d') + ')'
png_file_name = repo_path_obj.name + "_" + repo.active_branch.name + "_" + date_range_str + ".png"
plt.savefig(png_file_name)
print('output:' + png_file_name)