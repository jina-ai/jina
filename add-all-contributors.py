#! /usr/bin/python3

import sys
import subprocess
import json
import time
import random

# jina_repos = ["jina", "examples", "docs", "jina-hub", "hub-status", "stress-test", "press-kit", "dashboard", "legal", "jina-ai.github.io", "career", "api", "jinabox.js", "cookiecutter-jina"]
# jina_repos.remove('jina')
# jina_repos.append('jina')

jina_repos = ["jina-ai.github.io", "career", "docs", "examples"]

# rewrite the projectName of .all-contributorsrc
def rewrite_projetName(repo):
    inputFile = open(".all-contributorsrc", "r")
    contributorsrc = json.load(inputFile)
    inputFile.close()
    contributorsrc["projectName"] = repo
    if repo not in contributorsrc["types"].keys():
        repo = repo.replace('.', '')
        contributorsrc["types"][repo] = {"symbol": "", "description": "","link": ""}
    print(repo, 'projectName and types be rewrited!')
    outputFile = open(".all-contributorsrc", "w")
    json.dump(contributorsrc, outputFile, indent=2)
    outputFile.close()

# get all unqiue & shuffle jina-ai contributors
def allUniqueContributors(repos_list):
    allContributors = {}
    for repo in repos_list:
        rewrite_projetName(repo)
        all_missings = subprocess.run("all-contributors check", stdout=subprocess.PIPE, shell=True)
        all_missings = all_missings.stdout.decode('utf-8')
        print(all_missings)
        all_missings = all_missings.replace("Missing contributors in .all-contributorsrc:\n    ", "").strip().split(', ')
        for contributor in all_missings:
            repo = repo.replace('.', '')
            if contributor not in allContributors.keys():
                allContributors[contributor] = [repo]
            else:
                allContributors[contributor].append(repo)
    return allContributors

# unqiue & shuffle jina-ai contributors
contributors_dict = allUniqueContributors(jina_repos)
contributors_keys = list(contributors_dict.keys())
print(contributors_dict)
random.shuffle(contributors_keys)

# add jina contributors to .all-contributorsrc
for name in contributors_keys:
    subprocess.check_call(['all-contributors', 'add', name, (',').join(contributors_dict[name])])
    print(name, "added!")

# generate and insert wall of honor of jina README.md
subprocess.check_call(['all-contributors', 'generate'])