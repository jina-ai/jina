
# generate the list of commits from last **release noted** version to HEAD

commits = '''
2022-09-29 09:34:32 +0200; 1153396262; Joan Fontanals; feat: add gateway option to jina ping and use ping in readinessProbe (#5200)
2022-09-28 18:04:59 +0200; b5977f4780; Joan Fontanals; chore: update contributing to remove labeling (#5225)
2022-09-28 18:04:13 +0200; 9a6079ef71; AlaeddineAbdessalem; refactor: separate gateway and asyncio runtime readiness checks (#5224)
2022-09-28 14:43:41 +0200; 147317db8d; Michael Günther; docs: change setenv into environ (#5223)
2022-09-28 11:48:06 +0200; 3683fccfd5; AlaeddineAbdessalem; fix: fix compatibility with protobuf python backend (#5222)
2022-09-28 13:10:17 +0530; ad37bdd23f; Joan Fontanals; docs: mention prefetch (#5220)
2022-09-28 07:54:09 +0200; 45c7c6e1cb; Joan Fontanals; chore: update pull request template link (#5214)
2022-09-27 18:11:57 +0200; d0838d37de; Joan Fontanals; feat: add multiple attempts options to client.post API (#5176)
2022-09-27 16:41:46 +0200; b9c8e44e76; Joan Fontanals; docs: fix install instructions docker (#5213)
2022-09-27 13:07:41 +0200; e932d6f9e0; Yanlong Wang; fix(hubio.fetch_meta): move significant params to sequential (#5205)
2022-09-27 10:53:06 +0200; 13edf9080e; samsja; feat: use default grpc parameters for grpc connection pool connection (#5211)
2022-09-27 10:14:02 +0200; 216b4bf080; samsja; feat(monitoring): add monitoring of requests size in bytes at all level (#5111)
2022-09-26 17:45:56 +0200; 7cbf347147; Alex Cureton-Griffiths; docs(what-is-jina): fix grammar, wording, punctuation (#5209)
2022-09-26 17:44:08 +0200; 7c7d2cb04e; Alex Cureton-Griffiths; docs(what-is-modality): fix grammar, punctuation (#5208)
2022-09-23 15:59:20 +0200; 1399e36cea; Joan Fontanals; docs: clarify exec endpoint usage in http (#5202)
2022-09-23 13:43:05 +0200; 737875f537; Deepankar Mahapatro; feat(logs): json logging for jcloud (#5201)
2022-09-23 11:08:37 +0200; 60e9b8de6f; Joan Fontanals; fix: remove leftover prints (#5199)
2022-09-22 12:47:19 +0200; 842a585b37; AlaeddineAbdessalem; docs: document grpc client limitation (#5193)
2022-09-22 14:15:37 +0530; 96c5e7c1e5; Nikolas Pitsillos; docs(jcloud): update faq and lifetime (#5191)
2022-09-21 22:48:43 +0200; 1eab9ce660; Han Xiao; chore: fix doc template
2022-09-21 16:45:23 +0200; fd4c03476d; Joan Fontanals; feat: support list-like syntax to round robin CUDA devices (#5187)
2022-09-21 13:12:21 +0200; c17e6416d6; Joan Fontanals; docs: improve warning about config file in custom docker (#5190)
2022-09-20 12:59:40 +0200; da186a233c; AlaeddineAbdessalem; fix: provide logger and streamer (#5188)
2022-09-20 12:13:03 +0200; 9dff4c880f; Joan Fontanals; feat: add duration info in events (#5157)
2022-09-20 11:14:50 +0200; 7b5c0316ac; AlaeddineAbdessalem; fix: fix get-openapi-schemas script (#5185)
2022-09-20 10:10:01 +0200; 22330fcb31; Joan Fontanals; docs: clarify __return__ behavior in parameters (#5179)
2022-09-20 08:54:44 +0200; 243639dd2b; AlaeddineAbdessalem; refactor: extract gateway app logic into custom gateway class (#5153)
2022-09-20 08:53:21 +0200; caf4a3d653; zhangkai; fix: fix missing secret when logged-in user  with --force-update and … (#5180)
2022-09-15 15:59:28 +0200; 28aeac8e9a; Girish Chandrashekar; docs: add section for exit_on_exceptions argument (#5172)
2022-09-15 15:58:09 +0200; c51f9014a0; zhangkai; feat: hubble async push (#5129)
2022-09-15 13:41:54 +0200; 29ad1750d9; AlaeddineAbdessalem; fix: exit on exception args only applies to executors (#5169)
2022-09-15 13:41:33 +0200; 5518816588; Joan Fontanals; fix: pin docarray version for new column syntax (#5171)
2022-09-15 10:33:02 +0200; 3f39ed46f8; Girish Chandrashekar; feat(runtime): add argument to specify exceptions that will exit the runtime (#5165)
2022-09-15 10:10:15 +0200; 27e1f7799d; Andrei Ungureanu; feat(hubio): display warning messages from hubble request (jina hub push) (#5156)
2022-09-15 08:42:38 +0100; b59d04500e; AlaeddineAbdessalem; ci: add jina auth token (#5167)
2022-09-15 09:13:55 +0200; fa83955cea; AlaeddineAbdessalem; fix: increase minimum protobuf version (#5166)
2022-09-14 14:25:03 +0800; 33891c46c6; Deepankar Mahapatro; docs(jcloud): labels in flow yaml (#5164)
2022-09-08 15:29:22 +0200; 273fda5a86; Han Xiao; refactor: merge dryrun into ping (#5151)
'''

features = []
perfs = []
bugs = []
docs = []
allcommits = []

for l in commits.split('\n'):
    if not l.strip():
        continue
    _time, _hash, _author, _msg = [v.strip() for v in l.split(';')]
    _item = dict(time=_time, hash=_hash, author=_author, msg=_msg)
    if _msg.startswith('feat'):
        features.append(_item)
    elif _msg.startswith('perf'):
        perfs.append(_item)
    elif _msg.startswith('fix'):
        bugs.append(_item)
    elif _msg.startswith('docs') or _msg.startswith('chore(docs)'):
        docs.append(_item)
    allcommits.append(_item)

newline = '\n'
new_feature = '''
This new feature will allow users to do XYZ.

To use the new feature, use:

```python

```

which results in:

```text

```

The new feature will provide the following benefits:

- Benefit one
- Benefit two
- Benefit three
'''

print(f'''
# Release Note

[//]: <> (remove the phrase like "0 new features")
This release contains {len(features)} new features, {len(perfs)} performance improvements, {len(bugs)} bug fixes and {len(docs)} documentation improvements.  

[//]: <> (Does it have security update? If yes then add the following lines)
It is recommended to upgrade to this version as it contains security updates.

## 💥 Security Updates

[//]: <> (If no security update please remove this session.)

## 🆕 Features

{"".join(["### "+c['msg'].split(":")[1].strip().capitalize() +newline for c in features])}

[//]: <> (Nicely introduce each feature before/after with some code snippet and results)


## 🚀 Performance

{"".join(["### "+c['msg'].split(":")[1].strip().capitalize() +newline for c in perfs])}

[//]: <> (Nicely introduce each performance improvement before/after with some code snippet and results)

We have made a performance improvement to the system. When running the following code:

The result is 123% faster than before.

-The load time for the system has been significantly reduced.
-The system is now more responsive and faster.
-The overall performance of the system has been improved.


## 🐞 Bug Fixes

{"".join(["### "+c['msg'].split(":")[1].strip().capitalize() +newline for c in bugs])}

[//]: <> (Nicely introduce each bug fix before/after with some code snippet and results)

- The bug was causing [explain what the bug was causing].
- The new version fixes the bug and [explain what the new version does].

## 📗 Documentation Improvements

{"".join(["### "+c['msg'].split(":")[1].strip().capitalize() +newline for c in docs])}

[//]: <> (Nicely introduce each feature before/after with some code snippet and results)


## 🤟 Contributors

We would like to thank all contributors to this release: {newline.join(set([c['author']+"(@github_user) " for c in allcommits]))}
''')
