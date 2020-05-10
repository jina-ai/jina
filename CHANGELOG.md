



























# Change Logs

Jina is released on every Friday evening. The PyPi package and Docker Image will be updated, the changes of the release will be tracked by this file.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Release Note (`0.0.4`)](#release-note-004)
- [Release Note (`0.0.5`)](#release-note-005)
- [Release Note (`0.0.6`)](#release-note-006)
- [Release Note (`0.0.7`)](#release-note-007)
- [Release Note (`0.0.8`)](#release-note-008)
- [Release Note (`0.0.9`)](#release-note-009)
- [Release Note (`0.1.0`)](#release-note-010)
- [Release Note (`0.1.1`)](#release-note-011)
- [Release Note (`0.1.2`)](#release-note-012)
- [Release Note (`0.1.3`)](#release-note-013)
- [Release Note (`0.1.4`)](#release-note-014)
- [Release Note (`0.1.5`)](#release-note-015)
- [Release Note (`0.1.6`)](#release-note-016)
- [Release Note (`0.1.7`)](#release-note-017)
- [Release Note (`0.1.8`)](#release-note-018)
- [Release Note (`0.1.9`)](#release-note-019)
- [Release Note (`0.1.10`)](#release-note-0110)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Release Note (`0.0.4`)

> Release time: 2020-03-31 10:03:38



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  🙇


### 🐞 Bug fixes

 - [[```aecc7fcf```](https://github.com/jina-ai/jina/commit/aecc7fcf0ba47109cda126388319dacc1407d6f3)] __-__ release script logic (*Han Xiao*)


## Release Note (`0.0.5`)

> Release time: 2020-04-10 15:59:20



🙇 We'd like to thank all contributors for this new release! In particular,
 Nan Wang,  Han Xiao,  Xiong Ma,  hanxiao,  jina-bot,  Jina Dev Bot,  🙇


### 🆕 New Features

 - [[```063152d4```](https://github.com/jina-ai/jina/commit/063152d4343a8850f60170ee0b0ec277e6775bfe)] __-__ __indexer__: clean up indexers (*Nan Wang*)
 - [[```4b130f29```](https://github.com/jina-ai/jina/commit/4b130f292ff6d65e4749932e1f3c7043dc921d20)] __-__ __indexer__: add LevelDb indexer (*Nan Wang*)
 - [[```b184c0e2```](https://github.com/jina-ai/jina/commit/b184c0e2e82ec3d0ec556032e7d2ee148eec2bbd)] __-__ __crafter__: add docs (*Nan Wang*)
 - [[```8349c33e```](https://github.com/jina-ai/jina/commit/8349c33ea39aea864aa428e25195ce195220e979)] __-__ __crafter__: add Sentencizer (*Nan Wang*)
 - [[```d54e1ed4```](https://github.com/jina-ai/jina/commit/d54e1ed4a417aaebd7c5d509e7b365f77bb080d7)] __-__ __crafter__: fix the line width (*Nan Wang*)
 - [[```1a13e90b```](https://github.com/jina-ai/jina/commit/1a13e90b0a022593b48cb63f9027401bcc498b46)] __-__ __crafter__: adapt the ChunkCrafterDriver (*Nan Wang*)
 - [[```20bd5277```](https://github.com/jina-ai/jina/commit/20bd5277178c1bfbff235c93f91cb19d03ee19ff)] __-__ __crafter__: fix unittests (*Nan Wang*)
 - [[```834760f1```](https://github.com/jina-ai/jina/commit/834760f1cacf78a34b4224c714dbb2afc1a118bb)] __-__ fix sse endpoint for dashboard (*Han Xiao*)
 - [[```e48331b8```](https://github.com/jina-ai/jina/commit/e48331b88eb021c85f5c230bd2676741773e685d)] __-__ add prefetch to gateway (*Han Xiao*)
 - [[```7f0fc881```](https://github.com/jina-ai/jina/commit/7f0fc88123038b612b69727bd49bbdfb9606265c)] __-__ __crafter__: add test arrays (*Nan Wang*)
 - [[```d2db40e6```](https://github.com/jina-ai/jina/commit/d2db40e615a5b3a9cf760bc489f54cb7e5322810)] __-__ __crafter__: add sliding window (*Nan Wang*)
 - [[```fd6a2e65```](https://github.com/jina-ai/jina/commit/fd6a2e65d28dca22a89754e943ce1456c5d882ee)] __-__ __crafter__: add resize crafters (*Nan Wang*)
 - [[```ac30e1bd```](https://github.com/jina-ai/jina/commit/ac30e1bd592a331c1827529447f06bcbcaa8c2ad)] __-__ add flow cli (*Han Xiao*)
 - [[```e929ecc4```](https://github.com/jina-ai/jina/commit/e929ecc4edd9cb414f072c41b4252e5170a2bf3b)] __-__ __crafter__: add cropers (*Nan Wang*)
 - [[```09bc3c10```](https://github.com/jina-ai/jina/commit/09bc3c101db69c471a123e15e5864a8a5d98fcda)] __-__ __crafter__: add ImageReader (*Nan Wang*)
 - [[```db1234c9```](https://github.com/jina-ai/jina/commit/db1234c9dc9c66ff77322deab4d7b64c6f57856e)] __-__ __pod__: add load balancing as one scheduler (*Han Xiao*)
 - [[```964aa7d3```](https://github.com/jina-ai/jina/commit/964aa7d391700cb5c08d81ba22fc52796246e257)] __-__ __proto__: update proto (*Han Xiao*)
 - [[```84ff5b84```](https://github.com/jina-ai/jina/commit/84ff5b842308fa06d445baabc17e456207d01ff5)] __-__ add load balancing to pods (*Han Xiao*)
 - [[```2cf9a9d3```](https://github.com/jina-ai/jina/commit/2cf9a9d355a43dccb8b664cfeef838ae92fd6139)] __-__ add SPTAG indexer, fix #170 (*Han Xiao*)
 - [[```58c3d705```](https://github.com/jina-ai/jina/commit/58c3d705d8af789a3679ac9f1f62330778b11a0f)] __-__ add NMSLIB indexer, fix #169 (*Han Xiao*)
 - [[```a2e26e48```](https://github.com/jina-ai/jina/commit/a2e26e48b295e30c345d70f61c4756740f5c4499)] __-__ __encoder__: remove the PCAEncoder (*Nan Wang*)
 - [[```62b0d840```](https://github.com/jina-ai/jina/commit/62b0d840aff181293bcca341c749c5ac37d46770)] __-__ __encoder__: fix codes in response to the reviews (*Nan Wang*)
 - [[```4448ff58```](https://github.com/jina-ai/jina/commit/4448ff588bec7551cf67a0fe746857d0b7a6fafb)] __-__ __encoder__: fix the unittests (*Nan Wang*)
 - [[```db2a4ea5```](https://github.com/jina-ai/jina/commit/db2a4ea52ca5af6b66fec85a07f6117c70b2b58b)] __-__ __encoder__: fix the extra-requirements (*Nan Wang*)
 - [[```6feb20fb```](https://github.com/jina-ai/jina/commit/6feb20fbeaf3be7c50ccd7bfdfb76d001d16ae0e)] __-__ __encoder__: add the PCAEncoder and refactoring unittests (*Nan Wang*)
 - [[```196e6907```](https://github.com/jina-ai/jina/commit/196e690785577f8090f07ef739a758e22c238d77)] __-__ __encoder__: clean up useless args (*Nan Wang*)
 - [[```bf110817```](https://github.com/jina-ai/jina/commit/bf110817c8a4e744fa959aee19a1ca44a9fc8b1f)] __-__ __encoder__: add the IncrementalPCAEncoder (*Nan Wang*)
 - [[```e0f31e4f```](https://github.com/jina-ai/jina/commit/e0f31e4f1d7e24851433612c8578d5afbb6c8c70)] __-__ add release script (*Han Xiao*)

### 🐞 Bug fixes

 - [[```7fd419a8```](https://github.com/jina-ai/jina/commit/7fd419a89c3a51520dc93e62d7f4fd9d46815e61)] __-__ __cli__: add cli to load directly from yaml (*Han Xiao*)
 - [[```7df4f715```](https://github.com/jina-ai/jina/commit/7df4f7158b2700625e012ecf1d85425b53cae486)] __-__ logserver and log_sse (*Han Xiao*)
 - [[```0da3ed9e```](https://github.com/jina-ai/jina/commit/0da3ed9ee5c17dd99a960d79c7b7b1ed8892b060)] __-__ yaml dump for enum (*Han Xiao*)
 - [[```56ce1d76```](https://github.com/jina-ai/jina/commit/56ce1d76a1aab5f0133fb0c45bb9016e11c8a258)] __-__ __pea__: fix timeout_ready in peas (*Xiong Ma*)
 - [[```46796d35```](https://github.com/jina-ai/jina/commit/46796d35fa6eb4947bb7272aa2943451902d5781)] __-__ change cli underscore to dash (*Han Xiao*)
 - [[```8a9a58ae```](https://github.com/jina-ai/jina/commit/8a9a58ae7a3ddc8d407a981f5f7c4259180d86f0)] __-__ __executor__: fix bert cls output (*Xiong Ma*)
 - [[```38a77a94```](https://github.com/jina-ai/jina/commit/38a77a94d9a2574394e45f8144cd0f1baa240934)] __-__ add some feedback when post_init (*Han Xiao*)
 - [[```f7c6491b```](https://github.com/jina-ai/jina/commit/f7c6491b26ac419bf7285b88f454f2978cfca794)] __-__ __pea__: gracefully exit thread and process (*Han Xiao*)
 - [[```85bc8c31```](https://github.com/jina-ai/jina/commit/85bc8c314cc4defaaa6900cfcf82e1e15ad9f6ae)] __-__ handle dry_run like data request (*Han Xiao*)
 - [[```28197c6b```](https://github.com/jina-ai/jina/commit/28197c6b8a3df79ffbc8f5fea544c8262bd9b80e)] __-__ __crafter__: fix the import issue (*Nan Wang*)
 - [[```f6ca1828```](https://github.com/jina-ai/jina/commit/f6ca182813385defff45a74e1487b452ec28bff3)] __-__ __encoder__: add batching mode (*Nan Wang*)
 - [[```32b032ee```](https://github.com/jina-ai/jina/commit/32b032ee44e67dd306077ead4738eccf5b335c7c)] __-__ image name and internal executor path (*Han Xiao*)
 - [[```479009be```](https://github.com/jina-ai/jina/commit/479009bee914f161250bae10abfe5f2e678d9b8d)] __-__ __encoder__: fix unittests for containers (*Nan Wang*)
 - [[```4e8f784e```](https://github.com/jina-ai/jina/commit/4e8f784e81446e07be2a3f5d65aa423b4f9dff7a)] __-__ __encoder__: refactoring ernie encoders (*Nan Wang*)
 - [[```8b2d87d5```](https://github.com/jina-ai/jina/commit/8b2d87d596f854fb10d72e7984adf2791b6f4979)] __-__ __encoder__: refactoring transformer encoders (*Nan Wang*)
 - [[```05ddd5c9```](https://github.com/jina-ai/jina/commit/05ddd5c9a32aa30301886eca912d28da3fa07dda)] __-__ cd and release logic (*Han Xiao*)
 - [[```cd5f2ae7```](https://github.com/jina-ai/jina/commit/cd5f2ae7f4432013ab32681461129804223650be)] __-__ bind socket error except handle (*Han Xiao*)
 - [[```7fc5eef6```](https://github.com/jina-ai/jina/commit/7fc5eef65c18edbb90457b341eb50c040f981cdd)] __-__ __executor__: delete some useless codes (*Xiong Ma*)
 - [[```78048e57```](https://github.com/jina-ai/jina/commit/78048e578d09b8519abaa5b48fb5d7be85520777)] __-__ __executor__: add pytorch at first (*Xiong Ma*)
 - [[```be1a4ecf```](https://github.com/jina-ai/jina/commit/be1a4ecfe2b1d2323345caf9e7df0893ea081a31)] __-__ __executor__: add tf/pytorch detect in transformertextencoder (*Xiong Ma*)
 - [[```ee290c14```](https://github.com/jina-ai/jina/commit/ee290c1471320f705a3fc4aec4cf57989ab6cf80)] __-__ sse logger threading exception (*Han Xiao*)
 - [[```6ca5b494```](https://github.com/jina-ai/jina/commit/6ca5b494185cb58cf2985a599f5e2d9321a4395e)] __-__ release docker (*Han Xiao*)
 - [[```67df4913```](https://github.com/jina-ai/jina/commit/67df491362a17468a8d57ef504a3c2b43b6a69f4)] __-__ release script logic (*Han Xiao*)

### 🚧 Code Refactoring

 - [[```dd43f001```](https://github.com/jina-ai/jina/commit/dd43f001bf0bc90045c260f272d47676950cc040)] __-__ log server config (*Han Xiao*)
 - [[```154b4b97```](https://github.com/jina-ai/jina/commit/154b4b979a51fb96e2e4415863f4e5835d39852b)] __-__ refactoring unittests (*Nan Wang*)
 - [[```38bac321```](https://github.com/jina-ai/jina/commit/38bac321adf08fe5e2b2eb1a58293ca567db49c1)] __-__ __encoder__: add more transformer encoders (*Nan Wang*)
 - [[```01a830b2```](https://github.com/jina-ai/jina/commit/01a830b261c96380b06ccb1d8d1e1cd7332c5ce8)] __-__ __encoder__: refactoring torch encoders (*Nan Wang*)
 - [[```a73690e9```](https://github.com/jina-ai/jina/commit/a73690e916e9a67610c71c6b42ad11b18be51417)] __-__ __encoder__: refactoring the paddlehub encoder for nlp (*Nan Wang*)
 - [[```7a68b837```](https://github.com/jina-ai/jina/commit/7a68b837007cb0c0463b264ab46655512b8a3b48)] __-__ __encoder__: rename cv to image (*Nan Wang*)
 - [[```9eac5997```](https://github.com/jina-ai/jina/commit/9eac59977d02bd8e448c3187a27a3a75d9d7d5c2)] __-__ __encoder__: add the channel_axis argument (*Nan Wang*)
 - [[```76b7fe7d```](https://github.com/jina-ai/jina/commit/76b7fe7d430c3ab803c0edbd736a0c9daa4af0c6)] __-__ __encoder__: refactoring paddlehub encoders (*Nan Wang*)
 - [[```8a954328```](https://github.com/jina-ai/jina/commit/8a954328b7ddc0c6cad6b7d6bee1217433308667)] __-__ __encoder__: refactoring paddlehub encoders for the cv and video part (*Nan Wang*)
 - [[```aeef4534```](https://github.com/jina-ai/jina/commit/aeef4534c9d414319e65d793860e86f3fdcf06e5)] __-__ __executor__: separate TransformerEncoder class (*Xiong Ma*)
 - [[```7d4e7146```](https://github.com/jina-ai/jina/commit/7d4e7146a72bc11e4af0deced0c5286a14ad9962)] __-__ remove send_to rename recv_from to needs (*Han Xiao*)
 - [[```ab405ea0```](https://github.com/jina-ai/jina/commit/ab405ea0a86ca959b23f20269d286424192cb62a)] __-__ __indexer__: add BaseVectorIndexer, BaseKVIndexer rename old (*Han Xiao*)

### 📗 Documentation

 - [[```c57ca842```](https://github.com/jina-ai/jina/commit/c57ca8420230ae1b5ca1c8ebd764e60b1fac40dc)] __-__ update TOC (*hanxiao*)
 - [[```9d7588b3```](https://github.com/jina-ai/jina/commit/9d7588b3a8ffcc1b42e5ce25b76f3f19037a61ed)] __-__ add release cycle explain (*Han Xiao*)
 - [[```7c1f0f6b```](https://github.com/jina-ai/jina/commit/7c1f0f6b6bcf3ed1525673c7eab6ae8ee605c074)] __-__ __contributing__: fix typo (*Xiong Ma*)
 - [[```97c240d9```](https://github.com/jina-ai/jina/commit/97c240d97eb28ae5fa69e65a17bb93f0cca7b853)] __-__ add toc for to page generator (*Han Xiao*)
 - [[```e2bb0428```](https://github.com/jina-ai/jina/commit/e2bb0428a56789dd3626a7509819147e8750e2c8)] __-__ update CONTRIBUTING guideline and readme (*Han Xiao*)

### 🏁 Unit Test and CICD

 - [[```c3b80680```](https://github.com/jina-ai/jina/commit/c3b80680817217f64e6e9b8f6ab2c04fbc86a0f5)] __-__ fix logic and filters (*Han Xiao*)
 - [[```c24a92fc```](https://github.com/jina-ai/jina/commit/c24a92fc924caa094c20fae197df02135b7a2e72)] __-__ fix flow test deadlock (*Han Xiao*)

### 🍹 Other Improvements

 - [[```705ee269```](https://github.com/jina-ai/jina/commit/705ee2699c20ec394084e1ff785c93e861e21192)] __-__ __version__: bumping version to 0.0.5 (*Jina Dev Bot*)
 - [[```0e8ca53e```](https://github.com/jina-ai/jina/commit/0e8ca53eea99eaa35dc57c75f33536be0bd091cc)] __-__ __version__: bumping version to 0.0.3 (*Jina Dev Bot*)

## Release Note (`0.0.6`)

> Release time: 2020-04-12 10:05:50



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  🙇


### 🍹 Other Improvements

 - [[```533f71e3```](https://github.com/jina-ai/jina/commit/533f71e3de47ca5854f231598cda93002f628fad)] __-__ update readme (*Han Xiao*)
 - [[```fba9d762```](https://github.com/jina-ai/jina/commit/fba9d762e0b86d43c70839f9cd631d079aa49bdb)] __-__ update social links in readme (*Han Xiao*)

## Release Note (`0.0.7`)

> Release time: 2020-04-17 15:58:15



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Nan Wang,  Jina Dev Bot,  🙇


### 🆕 New Features

 - [[```2e72242f```](https://github.com/jina-ai/jina/commit/2e72242f99e12c5d22f7e973176439080ed58733)] __-__ add level-specific driver shortcut (*Han Xiao*)
 - [[```9f9e9564```](https://github.com/jina-ai/jina/commit/9f9e95649cd9d5a2b27116e7413c2c91527cbb14)] __-__ add profile endpoint (*Han Xiao*)
 - [[```4d7518b1```](https://github.com/jina-ai/jina/commit/4d7518b1afce2c932734d380cce73fcb9a1074c1)] __-__ add reducing-yaml-path to pod cli (*Han Xiao*)
 - [[```f7ecf473```](https://github.com/jina-ai/jina/commit/f7ecf4739682b3505ae508e1fbf02e2907e1f70a)] __-__ add backend to npindexer (*Han Xiao*)
 - [[```640ca7c8```](https://github.com/jina-ai/jina/commit/640ca7c83fc926d95b3dbd3c97a15999175886e2)] __-__ add description to cli for sphinx (*Han Xiao*)
 - [[```e6227c07```](https://github.com/jina-ai/jina/commit/e6227c07f2ef5a45d0e6e8b946862c52779e02a4)] __-__ __ranker__: fix the idf (*Nan Wang*)
 - [[```e1c6b904```](https://github.com/jina-ai/jina/commit/e1c6b904a8b6990d3c924a1657b157f47b2d1f83)] __-__ __ranker__: add BM25 ranker (*Nan Wang*)
 - [[```51d34d20```](https://github.com/jina-ai/jina/commit/51d34d20246e50cd50c761c3664776a80b963d08)] __-__ __ranker__: add tfidf ranker (*Nan Wang*)
 - [[```f6f6375a```](https://github.com/jina-ai/jina/commit/f6f6375af298ded52a4875851c04027357649a92)] __-__ __ranker__: add unittest for BiMatchRanker (*Nan Wang*)

### 🐞 Bug fixes

 - [[```8388f4df```](https://github.com/jina-ai/jina/commit/8388f4df2df8f68bc749682a80b4c8f8137f5e37)] __-__ flush on every write safer but slower (*Han Xiao*)
 - [[```f3609cfe```](https://github.com/jina-ai/jina/commit/f3609cfe5b9e480991c627eeed06775bdc690a03)] __-__ __ranker__: fix missing query chunk and float32 (*Nan Wang*)
 - [[```f14b3134```](https://github.com/jina-ai/jina/commit/f14b31347613ac04ec334c577815ea21b2bd19f3)] __-__ fix replica_id behavior (*Han Xiao*)
 - [[```a357e25f```](https://github.com/jina-ai/jina/commit/a357e25f9aaa708ae2fcb3f6401bd8cf8558c906)] __-__ fix broken protoidx for #234 (*Han Xiao*)
 - [[```e4f58e97```](https://github.com/jina-ai/jina/commit/e4f58e972f610048d1ae580dc2cd16153a3df136)] __-__ __indexer__: fix leveldb indexer (*Nan Wang*)
 - [[```c3d1eef4```](https://github.com/jina-ai/jina/commit/c3d1eef414778b1f050660d13866f1f1062ceefe)] __-__ __indexer__: add test for loading exec (*Nan Wang*)
 - [[```599cf14b```](https://github.com/jina-ai/jina/commit/599cf14bbac26b871090213683ec095260eb6383)] __-__ prune driver pruned fields (*Han Xiao*)
 - [[```ed42519e```](https://github.com/jina-ai/jina/commit/ed42519e94a7d44c223e78cba64ec24791e08f36)] __-__ __driver__: fix the top_k for docs (*Nan Wang*)
 - [[```c705f5c9```](https://github.com/jina-ai/jina/commit/c705f5c937b1ed11efe5e89be635a458ab1bf672)] __-__ __driver__: fix the comments (*Nan Wang*)
 - [[```4750555f```](https://github.com/jina-ai/jina/commit/4750555f0ef17ea3874de8f1e5fbd62ff94a35a9)] __-__ float32 matchidx overflow (*Han Xiao*)
 - [[```6cd26fc0```](https://github.com/jina-ai/jina/commit/6cd26fc07ecf67a58813e5fd136dec50a14f2721)] __-__ float32 match_idx overflow (*Han Xiao*)
 - [[```8dc37ddf```](https://github.com/jina-ai/jina/commit/8dc37ddf62903866c5c6eb81cabfbea6db8f4d18)] __-__ sse logger shutdown problem (*Han Xiao*)

### 🚧 Code Refactoring

 - [[```cb60046c```](https://github.com/jina-ai/jina/commit/cb60046c090074b569851c32611ce46877472f7f)] __-__ update test and default yaml (*Han Xiao*)
 - [[```705c7ac0```](https://github.com/jina-ai/jina/commit/705c7ac00d055ae903f67d295aa5ece06243c911)] __-__ make compoundindexer as standarad pattern (*Han Xiao*)
 - [[```fb65b5c2```](https://github.com/jina-ai/jina/commit/fb65b5c2e79c18eb635ce12cf7c577cbce5ddef4)] __-__ remove .with.method default value (*Han Xiao*)
 - [[```1005f484```](https://github.com/jina-ai/jina/commit/1005f484178459c7399c71d958bd96fa0d94a073)] __-__ add base driver for each executor (*Han Xiao*)
 - [[```197e6bbc```](https://github.com/jina-ai/jina/commit/197e6bbc2306e05a6769c9470e46e0689051dd83)] __-__ __tests__: rename the indexer (*Nan Wang*)

### 📗 Documentation

 - [[```534a8da7```](https://github.com/jina-ai/jina/commit/534a8da7098be5674d8dfdd13d05659fe38e8fc3)] __-__ trigger doc update again (*Han Xiao*)
 - [[```f5935310```](https://github.com/jina-ai/jina/commit/f593531037a9f791e8badf4c6059851bc7fd2208)] __-__ add dashboard (*Han Xiao*)

### 🍹 Other Improvements

 - [[```e2fffafd```](https://github.com/jina-ai/jina/commit/e2fffafdf55022dfc2ba29e5b33efc8cbef7bed0)] __-__ update gif (*Han Xiao*)
 - [[```11d86b4c```](https://github.com/jina-ai/jina/commit/11d86b4c8aea2dbdd5efeaf14aa2510297f24479)] __-__ test banner image (*Han Xiao*)
 - [[```db295af0```](https://github.com/jina-ai/jina/commit/db295af00e5ac911e00e2e11efd4d193fc7228d4)] __-__ update readme (*Han Xiao*)
 - [[```9600b1b3```](https://github.com/jina-ai/jina/commit/9600b1b3f795bb3c4bdb4ae1a583fa047c5ee83c)] __-__ __version__: bumping version to 0.0.7 (*Jina Dev Bot*)

## Release Note (`0.0.8`)

> Release time: 2020-04-24 15:58:34



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Nan Wang,  hanxiao,  nan-wang,  Jina Dev Bot,  🙇


### 🆕 New Features

 - [[```2a0a5072```](https://github.com/jina-ai/jina/commit/2a0a50726d1ce82e95984c66512d1da5a779aee4)] __-__ __crafters__: add an option to save raw_bytes (*Nan Wang*)
 - [[```6235b100```](https://github.com/jina-ai/jina/commit/6235b1004a2916285fc5326b76042c6cad491583)] __-__ add logserver option in helloworld (*Han Xiao*)
 - [[```59cbba2a```](https://github.com/jina-ai/jina/commit/59cbba2a0db19a11afa723cb25f6014d52baa9af)] __-__ add cli args to hello world (*Han Xiao*)
 - [[```022e508f```](https://github.com/jina-ai/jina/commit/022e508f7dee50278ad9c4872af1275e3f1162f3)] __-__ add hello world yaml (*Han Xiao*)
 - [[```22eb415f```](https://github.com/jina-ai/jina/commit/22eb415f22848753d8651bc04e010b54edf733bf)] __-__ add hello world for jina (*Han Xiao*)
 - [[```9f9e9564```](https://github.com/jina-ai/jina/commit/9f9e95649cd9d5a2b27116e7413c2c91527cbb14)] __-__ add profile endpoint (*Han Xiao*)
 - [[```4d7518b1```](https://github.com/jina-ai/jina/commit/4d7518b1afce2c932734d380cce73fcb9a1074c1)] __-__ add reducing-yaml-path to pod cli (*Han Xiao*)
 - [[```f7ecf473```](https://github.com/jina-ai/jina/commit/f7ecf4739682b3505ae508e1fbf02e2907e1f70a)] __-__ add backend to npindexer (*Han Xiao*)
 - [[```640ca7c8```](https://github.com/jina-ai/jina/commit/640ca7c83fc926d95b3dbd3c97a15999175886e2)] __-__ add description to cli for sphinx (*Han Xiao*)

### 🐞 Bug fixes

 - [[```b135e889```](https://github.com/jina-ai/jina/commit/b135e889275f82b6c443f435f7459ec8f2cc8c35)] __-__ __crafters__: fix the color channel bug (*Nan Wang*)
 - [[```3df6ced3```](https://github.com/jina-ai/jina/commit/3df6ced34cdbf17ab774c1e3926fdfb8b3d7dfbc)] __-__ profile stream of the logger (*Han Xiao*)
 - [[```fa1a4495```](https://github.com/jina-ai/jina/commit/fa1a44954cf0a5967989c13e052d705e698ab46b)] __-__ undo the changes (*Nan Wang*)
 - [[```b1b2c411```](https://github.com/jina-ai/jina/commit/b1b2c4115a34ee5d941b37e53c33749f5a789aa2)] __-__ __drivers__: add handling for blob (*Nan Wang*)
 - [[```cd6a3a49```](https://github.com/jina-ai/jina/commit/cd6a3a4951fd949245d40434009f82d3ec7f7593)] __-__ __rankers__: fix the tfidfRanker (*Nan Wang*)
 - [[```f5609f4f```](https://github.com/jina-ai/jina/commit/f5609f4f7db78fc6accba80321da2b398643f2aa)] __-__ __crafters__: fix the split (*Nan Wang*)
 - [[```8a3fe375```](https://github.com/jina-ai/jina/commit/8a3fe37581c496ca91f982e118dc6fdd96c35bd1)] __-__ __indexers__: clean up imports (*Nan Wang*)
 - [[```1e3d3b76```](https://github.com/jina-ai/jina/commit/1e3d3b76d118734098357e411b1b4c38b7486ed3)] __-__ __indexers__: fix leveldb (*Nan Wang*)
 - [[```866f3cfd```](https://github.com/jina-ai/jina/commit/866f3cfdd6197e8d038005931631f0f932d81a23)] __-__ fix typos (*Nan Wang*)
 - [[```16cc8753```](https://github.com/jina-ai/jina/commit/16cc87532463c645c2b7597a64e8c50304f65044)] __-__ devel docker build (*Han Xiao*)
 - [[```e411e4eb```](https://github.com/jina-ai/jina/commit/e411e4eb5e5c6aeffd095375586477f4ba5bf619)] __-__ remove requests dep (*Han Xiao*)
 - [[```c026e200```](https://github.com/jina-ai/jina/commit/c026e200b2025e09a27bc731b2086fe2110a40b7)] __-__ __tests__: refactoring flair (*Nan Wang*)
 - [[```51fbcced```](https://github.com/jina-ai/jina/commit/51fbcced3b83e02fead53ea5a29bfef4be15cf0c)] __-__ __tests__: refactoring nlp tests (*Nan Wang*)
 - [[```5be32322```](https://github.com/jina-ai/jina/commit/5be323222f842ae7436e8c40235abc52a81d4199)] __-__ __tests__: refactoring numeric tests (*Nan Wang*)
 - [[```b3b8e93f```](https://github.com/jina-ai/jina/commit/b3b8e93fc21e17b220d600eb413beb5de58207c3)] __-__ __tests__: refactoring video tests (*Nan Wang*)
 - [[```ead2d485```](https://github.com/jina-ai/jina/commit/ead2d4850440e57ed1ea795eaf2fbcd0e9eac94d)] __-__ __tests__: refactoring image tests (*Nan Wang*)
 - [[```ff970fd0```](https://github.com/jina-ai/jina/commit/ff970fd0d8fcdf0d7fafaf20598efad97a3f453e)] __-__ __tests__: refactoring tests (*Nan Wang*)
 - [[```8388f4df```](https://github.com/jina-ai/jina/commit/8388f4df2df8f68bc749682a80b4c8f8137f5e37)] __-__ flush on every write safer but slower (*Han Xiao*)
 - [[```f3609cfe```](https://github.com/jina-ai/jina/commit/f3609cfe5b9e480991c627eeed06775bdc690a03)] __-__ __ranker__: fix missing query chunk and float32 (*Nan Wang*)
 - [[```f14b3134```](https://github.com/jina-ai/jina/commit/f14b31347613ac04ec334c577815ea21b2bd19f3)] __-__ fix replica_id behavior (*Han Xiao*)
 - [[```a357e25f```](https://github.com/jina-ai/jina/commit/a357e25f9aaa708ae2fcb3f6401bd8cf8558c906)] __-__ fix broken protoidx for #234 (*Han Xiao*)
 - [[```e4f58e97```](https://github.com/jina-ai/jina/commit/e4f58e972f610048d1ae580dc2cd16153a3df136)] __-__ __indexer__: fix leveldb indexer (*Nan Wang*)
 - [[```c3d1eef4```](https://github.com/jina-ai/jina/commit/c3d1eef414778b1f050660d13866f1f1062ceefe)] __-__ __indexer__: add test for loading exec (*Nan Wang*)
 - [[```ed42519e```](https://github.com/jina-ai/jina/commit/ed42519e94a7d44c223e78cba64ec24791e08f36)] __-__ __driver__: fix the top_k for docs (*Nan Wang*)
 - [[```c705f5c9```](https://github.com/jina-ai/jina/commit/c705f5c937b1ed11efe5e89be635a458ab1bf672)] __-__ __driver__: fix the comments (*Nan Wang*)

### 🚧 Code Refactoring

 - [[```ac74b640```](https://github.com/jina-ai/jina/commit/ac74b6401a290d6e435d902751be4169b3f19280)] __-__ remove build from docstring and tests (*Han Xiao*)
 - [[```0c185cc6```](https://github.com/jina-ai/jina/commit/0c185cc6c451318bbfc9bdf88392bd0ae6d6a0da)] __-__ add gateway in build not in init (*Han Xiao*)
 - [[```fb65b5c2```](https://github.com/jina-ai/jina/commit/fb65b5c2e79c18eb635ce12cf7c577cbce5ddef4)] __-__ remove .with.method default value (*Han Xiao*)

### 📗 Documentation

 - [[```f0e08e41```](https://github.com/jina-ai/jina/commit/f0e08e419d8103f43f5ad2763efa36a39c87ecb4)] __-__ fix license readme (*Han Xiao*)
 - [[```b9a4a769```](https://github.com/jina-ai/jina/commit/b9a4a7696ddfc4bd2a9cc48c32bc40dc0b52ba33)] __-__ add x as service docs (*Han Xiao*)
 - [[```8f2ba32b```](https://github.com/jina-ai/jina/commit/8f2ba32bf1666d9340403cdd8b17463e8aa2d256)] __-__ fix doc link in readme (*Han Xiao*)
 - [[```42895bb8```](https://github.com/jina-ai/jina/commit/42895bb82c97201976162d8ac3b3220bfa2f3ea3)] __-__ add extend doc (*Han Xiao*)
 - [[```7a12a0a2```](https://github.com/jina-ai/jina/commit/7a12a0a2e5646935e0913f6ea8b72d5cfc624fc3)] __-__ add link to readme (*Han Xiao*)
 - [[```2642e049```](https://github.com/jina-ai/jina/commit/2642e049b165821d676311d0bb512370dfc3f564)] __-__ add flow API overview (*Han Xiao*)
 - [[```b3bcdab1```](https://github.com/jina-ai/jina/commit/b3bcdab12453740668d013da3711b9391790997c)] __-__ add list of executors and drivers (*Han Xiao*)
 - [[```243e7a53```](https://github.com/jina-ai/jina/commit/243e7a538eb27aa2e4b6b352d861e44ed83a2ef2)] __-__ add expandable btn (*Han Xiao*)
 - [[```4a2bfaea```](https://github.com/jina-ai/jina/commit/4a2bfaea51fbd3aca73cb6e7f5b774648cccdb62)] __-__ fix styling (*Han Xiao*)
 - [[```fb7a96bb```](https://github.com/jina-ai/jina/commit/fb7a96bb0b338d156835d665098040e951065416)] __-__ update doc toc (*Han Xiao*)
 - [[```986f2b9f```](https://github.com/jina-ai/jina/commit/986f2b9fcd787ea2857322bd98984f5fe872d37d)] __-__ add hello world to docs (*Han Xiao*)
 - [[```5c895c25```](https://github.com/jina-ai/jina/commit/5c895c25570c37a058e9d9e6c859164e62f183bc)] __-__ fix layout in readme (*Han Xiao*)
 - [[```546d68e6```](https://github.com/jina-ai/jina/commit/546d68e6eb635f8b34c06955f3bfe4369729a8ff)] __-__ fix cli docs (*Han Xiao*)
 - [[```534a8da7```](https://github.com/jina-ai/jina/commit/534a8da7098be5674d8dfdd13d05659fe38e8fc3)] __-__ trigger doc update again (*Han Xiao*)
 - [[```f5935310```](https://github.com/jina-ai/jina/commit/f593531037a9f791e8badf4c6059851bc7fd2208)] __-__ add dashboard (*Han Xiao*)

### 🏁 Unit Test and CICD

 - [[```e447b7ef```](https://github.com/jina-ai/jina/commit/e447b7efb7d0033f2016368eec9da7257845d051)] __-__ fix devel-x.x.x to x.x.x-devel (*Han Xiao*)

### 🍹 Other Improvements

 - [[```bb70df7a```](https://github.com/jina-ai/jina/commit/bb70df7a1b6467a42a88155abf9172f5b63f039f)] __-__ fix typo (*Han Xiao*)
 - [[```fc90a5ee```](https://github.com/jina-ai/jina/commit/fc90a5ee10494e01406d2d0deaae02d4b212c44a)] __-__ fix link (*Han Xiao*)
 - [[```51486bb8```](https://github.com/jina-ai/jina/commit/51486bb8dabacadf0855d5134eeecbe9470c8661)] __-__ update links (*Han Xiao*)
 - [[```b295868d```](https://github.com/jina-ai/jina/commit/b295868da2800cce3267718cff8101ecfb2d3fc3)] __-__ fix links in readme (*Han Xiao*)
 - [[```4eaf8dee```](https://github.com/jina-ai/jina/commit/4eaf8deedfbe6990fbabadc2b3fa16b9e647c221)] __-__ update link in readme (*Han Xiao*)
 - [[```7101fb23```](https://github.com/jina-ai/jina/commit/7101fb23d5815529ac84c6557846dde74f154e47)] __-__ __docs__: update TOC (*hanxiao*)
 - [[```2bb38b89```](https://github.com/jina-ai/jina/commit/2bb38b89f09eb28a85fcf638b5b87409fe83dcf5)] __-__ Update README.md (*Han Xiao*)
 - [[```97dd6507```](https://github.com/jina-ai/jina/commit/97dd65074e8b4d4d252b461efd41a9a3dd647eeb)] __-__ update intro (*Han Xiao*)
 - [[```5c6ccdf3```](https://github.com/jina-ai/jina/commit/5c6ccdf3410d638837da9beb6c2617f38658d8c7)] __-__ update image (*Han Xiao*)
 - [[```25ecdafd```](https://github.com/jina-ai/jina/commit/25ecdafdfbfd89e550f0cc6062f72705bd3a67b8)] __-__ update readme structure (*Han Xiao*)
 - [[```fa197fd6```](https://github.com/jina-ai/jina/commit/fa197fd6b91178188596c82ce31279c870353837)] __-__ fix readme typo (*Han Xiao*)
 - [[```d03aff85```](https://github.com/jina-ai/jina/commit/d03aff85b98b3b9c2337a5fb2c99dfec8a262bbc)] __-__ update layout (*Han Xiao*)
 - [[```8c6e1bb1```](https://github.com/jina-ai/jina/commit/8c6e1bb128883a0b709dbb19b255c87aa3bf0bac)] __-__ update jina 101 and theme (*Han Xiao*)
 - [[```7a2f4969```](https://github.com/jina-ai/jina/commit/7a2f4969599f4e3d951328a4fa863ddf63226acc)] __-__ update copyright (*Han Xiao*)
 - [[```f3ab3764```](https://github.com/jina-ai/jina/commit/f3ab37643b1349b014d89f45fdcbeae340914a8a)] __-__ update 101 layout (*Han Xiao*)
 - [[```6e42b8d8```](https://github.com/jina-ai/jina/commit/6e42b8d83bc3f2444ca36dc13d8176afc1e47dc3)] __-__ test 101 doc (*Han Xiao*)
 - [[```9d9db74f```](https://github.com/jina-ai/jina/commit/9d9db74f440ca8bdf9af8c1f75836b5e1bc6158f)] __-__ update 101 (*Han Xiao*)
 - [[```925600fe```](https://github.com/jina-ai/jina/commit/925600fe551b068f7034158dea34d7f51dd1bc67)] __-__ update language order (*Han Xiao*)
 - [[```3d272587```](https://github.com/jina-ai/jina/commit/3d2725874cf6dfd6782afd4b8de4b44df2620c01)] __-__ fix layout (*Han Xiao*)
 - [[```ae4e9db8```](https://github.com/jina-ai/jina/commit/ae4e9db80302584bd49e09f8c5bdac4397e56ec8)] __-__ fix layout 101 (*Han Xiao*)
 - [[```0b0599bf```](https://github.com/jina-ai/jina/commit/0b0599bfc71a72f5a23ef88505218c17141eb587)] __-__ fix 101 layout (*Han Xiao*)
 - [[```b987eafe```](https://github.com/jina-ai/jina/commit/b987eafe428e19cb8aaba6308bfbb3ba36731b3b)] __-__ update jina 101 (*Han Xiao*)
 - [[```1be114be```](https://github.com/jina-ai/jina/commit/1be114bec78529e8e4eb62e2bc4d96117cbc18fe)] __-__ update flow chart (*Han Xiao*)
 - [[```177b89b5```](https://github.com/jina-ai/jina/commit/177b89b52567861c69db16a91869086807744b48)] __-__ fix image size (*Han Xiao*)
 - [[```fd0479a4```](https://github.com/jina-ai/jina/commit/fd0479a43b2838c00fff3b6fc0e2bca01699f48b)] __-__ update gif (*Han Xiao*)
 - [[```d3f18732```](https://github.com/jina-ai/jina/commit/d3f187322998790de576bf9bad94ab07d9ba8260)] __-__ update gif for hello-world (*Han Xiao*)
 - [[```d1203a36```](https://github.com/jina-ai/jina/commit/d1203a36c9a2fd967f2aea08e516a6632b378b34)] __-__ __version__: bumping version to 0.0.8 (*Jina Dev Bot*)

## Release Note (`0.0.9`)

> Release time: 2020-04-27 22:15:31



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Nan Wang,  Jina Dev Bot,  BingHo1013,  xiong-ma,  hanxiao,  🙇


### 🆕 New Features

 - [[```bc68a74b```](https://github.com/jina-ai/jina/commit/bc68a74b2d659df815acf38b8ad53979a21f524d)] __-__ add api for pod args (*Han Xiao*)
 - [[```0964dc6f```](https://github.com/jina-ai/jina/commit/0964dc6f34d4f1e120ee559575119b4a5e8d2e61)] __-__ add cli autocomplete (*Han Xiao*)
 - [[```7b3a75a8```](https://github.com/jina-ai/jina/commit/7b3a75a869bfd4fa9dc267a9ee8e922abc755224)] __-__ __ranker__: refactoring bimatch (*Nan Wang*)
 - [[```84622a51```](https://github.com/jina-ai/jina/commit/84622a51428ec5d7f8a06f21ddefb52f2a22dc6d)] __-__ __ranker__: refactoring rankers (*Nan Wang*)
 - [[```ed6f0e08```](https://github.com/jina-ai/jina/commit/ed6f0e08fd9719d86c71e83e031472fdcb7f1f0b)] __-__ __ranker__: add min/max ranker (*Nan Wang*)
 - [[```0c6c05a6```](https://github.com/jina-ai/jina/commit/0c6c05a6d5da9b076c69a1e5a46ce1b56c69a1d5)] __-__ __crafter__: add jieba requirement (*xiong-ma*)
 - [[```37fba5e1```](https://github.com/jina-ai/jina/commit/37fba5e192a209577bf926ff7e6ecef061866ea4)] __-__ __crafter__: add jieba crafter (*xiong-ma*)
 - [[```1ace3334```](https://github.com/jina-ai/jina/commit/1ace33347eb955abf64e38fd3a6b2f38ce630f2f)] __-__ improve ver-full info (*Han Xiao*)

### 🐞 Bug fixes

 - [[```9a4c9951```](https://github.com/jina-ai/jina/commit/9a4c9951c0306182b5e398067262fcbacbcdfcee)] __-__ add ga to docs (*Han Xiao*)
 - [[```54de20f3```](https://github.com/jina-ai/jina/commit/54de20f3e3589b98d97f0d22e032ba9e21cb70f8)] __-__ __rankers__: add the warnings (*Nan Wang*)
 - [[```bce9beef```](https://github.com/jina-ai/jina/commit/bce9beef8194aef54042ccc9e29c577593251854)] __-__ __rankers__: fix MinRanker (*Nan Wang*)
 - [[```54f9909b```](https://github.com/jina-ai/jina/commit/54f9909b8d5e170e998161d6f396f6c481ac81ff)] __-__ container hanging on tail (*Han Xiao*)
 - [[```38baed54```](https://github.com/jina-ai/jina/commit/38baed54c499fe74d496c767e3d16f04f9ab0b50)] __-__ clean up (*Nan Wang*)
 - [[```699c3c02```](https://github.com/jina-ai/jina/commit/699c3c0219934917ddec5781c331f5f405df5060)] __-__ fix host name for tail peas (*Nan Wang*)
 - [[```cb94b4d7```](https://github.com/jina-ai/jina/commit/cb94b4d76fa0af04d18dd7a5e30cf68dd360db41)] __-__ update parser link (*Han Xiao*)
 - [[```39bad3f3```](https://github.com/jina-ai/jina/commit/39bad3f339d4a666c3c1be52c73d35cb2437dc5b)] __-__ disable log profiling by default (*Han Xiao*)
 - [[```a3ad2e5c```](https://github.com/jina-ai/jina/commit/a3ad2e5c72a30289f8226ecc1d4d89a7a4a44692)] __-__ enable profiling by default (*Han Xiao*)
 - [[```8c77ec2c```](https://github.com/jina-ai/jina/commit/8c77ec2c12c036901004b246d6fb85d0b5eb3fb4)] __-__ slow pulling warning (*Han Xiao*)
 - [[```9676ec15```](https://github.com/jina-ai/jina/commit/9676ec1537711eafd2c8e7528669061ccf2b983a)] __-__ add num_req to profile api (*Han Xiao*)
 - [[```1286db0e```](https://github.com/jina-ai/jina/commit/1286db0eaf8d5fadfdec8d6e6e59e061c66a461c)] __-__ docs add meta tags (*Han Xiao*)
 - [[```fa04366c```](https://github.com/jina-ai/jina/commit/fa04366c31e15e08c267fec47e5020513044f557)] __-__ __crafter__: change class name (*xiong-ma*)
 - [[```c63b4cd0```](https://github.com/jina-ai/jina/commit/c63b4cd0cd97273cec184c0acfda08826300d567)] __-__ __crafter__: change code style (*xiong-ma*)
 - [[```a32b999d```](https://github.com/jina-ai/jina/commit/a32b999dc722fafc59422823ae24ddc879da64f1)] __-__ fix copyright bot (*Han Xiao*)
 - [[```2878389c```](https://github.com/jina-ai/jina/commit/2878389c88df01fc6b9c0c115eddc3987e260896)] __-__ add catch for atexit (*Han Xiao*)
 - [[```5ef91464```](https://github.com/jina-ai/jina/commit/5ef914643954b9b36714ecf73a44415bc811ceb0)] __-__ cname in doc gen (*Han Xiao*)
 - [[```3df6ced3```](https://github.com/jina-ai/jina/commit/3df6ced34cdbf17ab774c1e3926fdfb8b3d7dfbc)] __-__ profile stream of the logger (*Han Xiao*)
 - [[```fa1a4495```](https://github.com/jina-ai/jina/commit/fa1a44954cf0a5967989c13e052d705e698ab46b)] __-__ undo the changes (*Nan Wang*)
 - [[```b1b2c411```](https://github.com/jina-ai/jina/commit/b1b2c4115a34ee5d941b37e53c33749f5a789aa2)] __-__ __drivers__: add handling for blob (*Nan Wang*)
 - [[```cd6a3a49```](https://github.com/jina-ai/jina/commit/cd6a3a4951fd949245d40434009f82d3ec7f7593)] __-__ __rankers__: fix the tfidfRanker (*Nan Wang*)
 - [[```f5609f4f```](https://github.com/jina-ai/jina/commit/f5609f4f7db78fc6accba80321da2b398643f2aa)] __-__ __crafters__: fix the split (*Nan Wang*)
 - [[```8a3fe375```](https://github.com/jina-ai/jina/commit/8a3fe37581c496ca91f982e118dc6fdd96c35bd1)] __-__ __indexers__: clean up imports (*Nan Wang*)
 - [[```1e3d3b76```](https://github.com/jina-ai/jina/commit/1e3d3b76d118734098357e411b1b4c38b7486ed3)] __-__ __indexers__: fix leveldb (*Nan Wang*)

### 🚧 Code Refactoring

 - [[```0c185cc6```](https://github.com/jina-ai/jina/commit/0c185cc6c451318bbfc9bdf88392bd0ae6d6a0da)] __-__ add gateway in build not in init (*Han Xiao*)

### 📗 Documentation

 - [[```e9a2b1f1```](https://github.com/jina-ai/jina/commit/e9a2b1f13819a8dd083a150097f63332e288c288)] __-__ fix img broken links (*Han Xiao*)
 - [[```c898660e```](https://github.com/jina-ai/jina/commit/c898660e28788af5bc0638de820a80a29a5f7832)] __-__ fix broken links in docs (*Han Xiao*)
 - [[```27adc35c```](https://github.com/jina-ai/jina/commit/27adc35c2a1d080ad4c9afa52dec0ffbadf237a1)] __-__ add multi-lang for 101 (*Han Xiao*)
 - [[```85fc7218```](https://github.com/jina-ai/jina/commit/85fc7218a9e14001f8a5652e1b5d1e3093f20de3)] __-__ optimize readme for mt (*Han Xiao*)
 - [[```010c6333```](https://github.com/jina-ai/jina/commit/010c633300362be7cbfde60c45ac053246bd462f)] __-__ fix multi-lang (*Han Xiao*)
 - [[```e92bd7ed```](https://github.com/jina-ai/jina/commit/e92bd7ed2730290b5d33ddf73e59cebbb988ea18)] __-__ fix toc generate (*Han Xiao*)
 - [[```e3af1e00```](https://github.com/jina-ai/jina/commit/e3af1e00fa68eda181c8eb2b772c0bc4b4f20fe4)] __-__ fix issue template (*Han Xiao*)
 - [[```87d0ed48```](https://github.com/jina-ai/jina/commit/87d0ed482d92a493e41f031dcb2a5ca187e2e499)] __-__ fix contributing guide (*Han Xiao*)
 - [[```fec881f6```](https://github.com/jina-ai/jina/commit/fec881f66ef2d20ce6bb4cf152df380c78283182)] __-__ fix issue templates typo (*Han Xiao*)
 - [[```e91ca4f7```](https://github.com/jina-ai/jina/commit/e91ca4f7b533bef7dab524ded9d672413ff13354)] __-__ fix typos in translations (*Nan Wang*)
 - [[```85f695f8```](https://github.com/jina-ai/jina/commit/85f695f841910e52956213b32685bab830d6743e)] __-__ fix typos (*Nan Wang*)
 - [[```96941c0c```](https://github.com/jina-ai/jina/commit/96941c0cb1075916e1f1d8f8e6c63a367b371ebd)] __-__ fix links (*Nan Wang*)
 - [[```3fb4088f```](https://github.com/jina-ai/jina/commit/3fb4088fb48ed45a47d45e5d8206c790d4b90e2d)] __-__ add translations (*Nan Wang*)
 - [[```048aba40```](https://github.com/jina-ai/jina/commit/048aba40174cc1778c13cf63cb59958f20505347)] __-__ add internal exec explain (*Han Xiao*)
 - [[```7a12a0a2```](https://github.com/jina-ai/jina/commit/7a12a0a2e5646935e0913f6ea8b72d5cfc624fc3)] __-__ add link to readme (*Han Xiao*)
 - [[```2642e049```](https://github.com/jina-ai/jina/commit/2642e049b165821d676311d0bb512370dfc3f564)] __-__ add flow API overview (*Han Xiao*)
 - [[```b3bcdab1```](https://github.com/jina-ai/jina/commit/b3bcdab12453740668d013da3711b9391790997c)] __-__ add list of executors and drivers (*Han Xiao*)
 - [[```243e7a53```](https://github.com/jina-ai/jina/commit/243e7a538eb27aa2e4b6b352d861e44ed83a2ef2)] __-__ add expandable btn (*Han Xiao*)
 - [[```4a2bfaea```](https://github.com/jina-ai/jina/commit/4a2bfaea51fbd3aca73cb6e7f5b774648cccdb62)] __-__ fix styling (*Han Xiao*)
 - [[```fb7a96bb```](https://github.com/jina-ai/jina/commit/fb7a96bb0b338d156835d665098040e951065416)] __-__ update doc toc (*Han Xiao*)
 - [[```986f2b9f```](https://github.com/jina-ai/jina/commit/986f2b9fcd787ea2857322bd98984f5fe872d37d)] __-__ add hello world to docs (*Han Xiao*)

### 🏁 Unit Test and CICD

 - [[```2bd1537b```](https://github.com/jina-ai/jina/commit/2bd1537b3646ce0f074afa986484b33d75130f09)] __-__ trigger release script (*Han Xiao*)
 - [[```5135ce60```](https://github.com/jina-ai/jina/commit/5135ce601a65939fedb849eeb36d1b11448da945)] __-__ turn on docker readme (*Han Xiao*)
 - [[```01a3a9a0```](https://github.com/jina-ai/jina/commit/01a3a9a0549e023ce498fa76266d8d273e02cef0)] __-__ fix version line number (*Han Xiao*)
 - [[```4148d5c2```](https://github.com/jina-ai/jina/commit/4148d5c2946dd3c51d1b4e257c3dd7503aba70a5)] __-__ add copyright bot (*Han Xiao*)
 - [[```e447b7ef```](https://github.com/jina-ai/jina/commit/e447b7efb7d0033f2016368eec9da7257845d051)] __-__ fix devel-x.x.x to x.x.x-devel (*Han Xiao*)

### 🍹 Other Improvements

 - [[```62832d90```](https://github.com/jina-ai/jina/commit/62832d900ed4d37e1e4da2fe5c122e2510385686)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```63957e7b```](https://github.com/jina-ai/jina/commit/63957e7b438d210e26314d8a3f1ed391f714e4b7)] __-__ fix zh 101 format (*Han Xiao*)
 - [[```d0a56dd7```](https://github.com/jina-ai/jina/commit/d0a56dd79e6fa8953a9de13264f4b3783ae4bed2)] __-__ Update README.md (*Han Xiao*)
 - [[```63de277b```](https://github.com/jina-ai/jina/commit/63de277b1fe8cca51c1c213c315d7c8c5275c6ab)] __-__ fix 101 link (*Han Xiao*)
 - [[```ade1c6db```](https://github.com/jina-ai/jina/commit/ade1c6db01619b4038e2be2f979c76392655a1ed)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```ed605818```](https://github.com/jina-ai/jina/commit/ed605818a3784113c7865fb568eb197978f815ac)] __-__ fix readme typo (*BingHo1013*)
 - [[```165e21ac```](https://github.com/jina-ai/jina/commit/165e21ac42e722c44894788b284f4048fa464655)] __-__ fix setup script (*Han Xiao*)
 - [[```494ff42f```](https://github.com/jina-ai/jina/commit/494ff42fcb939b5ff3265e253b778ce158e39d31)] __-__ update install section (*Han Xiao*)
 - [[```f36b5f0b```](https://github.com/jina-ai/jina/commit/f36b5f0b8fed38c5b57d3470c3bc46fbf1b3d5b2)] __-__ @policeme has signed the CLA from Pull Request 313 (*Jina Dev Bot*)
 - [[```e22a94a8```](https://github.com/jina-ai/jina/commit/e22a94a8b0413b436d10e3f8241b921c90b670e1)] __-__ replace urbandict with southpark (*Nan Wang*)
 - [[```4fa9ff16```](https://github.com/jina-ai/jina/commit/4fa9ff16dd60f196c82521ef6d35a586e6c31532)] __-__ creating file for storing CLA Signatures (*Jina Dev Bot*)
 - [[```b43dcd4d```](https://github.com/jina-ai/jina/commit/b43dcd4d24d23257ee204fd7cbf5456c7723af2f)] __-__ update issue bot (*Han Xiao*)
 - [[```01021844```](https://github.com/jina-ai/jina/commit/01021844334af595179d635f0fee0fd8b4939cc9)] __-__ add cla bot (*Han Xiao*)
 - [[```bfef77ad```](https://github.com/jina-ai/jina/commit/bfef77ad022c750bf290a893b5ba442d8528756a)] __-__ fix typo in 101 (*BingHo1013*)
 - [[```21e95a17```](https://github.com/jina-ai/jina/commit/21e95a17c278bee77946aceec04c316d77bd6fca)] __-__ add issue bot (*Han Xiao*)
 - [[```6c17dd22```](https://github.com/jina-ai/jina/commit/6c17dd22af9fb5e7fd667b183f1175b135762a23)] __-__ update issue template (*Han Xiao*)
 - [[```13400438```](https://github.com/jina-ai/jina/commit/1340043871885b7098e23fbffd2607176f95da81)] __-__ add issue template (*Han Xiao*)
 - [[```a66884ae```](https://github.com/jina-ai/jina/commit/a66884ae83d897cc4203f961372458c5fde392b0)] __-__ update links (*Han Xiao*)
 - [[```14110d39```](https://github.com/jina-ai/jina/commit/14110d39882973b52d2797533ec2462f9e7ad7a6)] __-__ __version__: bumping version to 0.0.9 (*Jina Dev Bot*)
 - [[```4eaf8dee```](https://github.com/jina-ai/jina/commit/4eaf8deedfbe6990fbabadc2b3fa16b9e647c221)] __-__ update link in readme (*Han Xiao*)
 - [[```97dd6507```](https://github.com/jina-ai/jina/commit/97dd65074e8b4d4d252b461efd41a9a3dd647eeb)] __-__ update intro (*Han Xiao*)
 - [[```5c6ccdf3```](https://github.com/jina-ai/jina/commit/5c6ccdf3410d638837da9beb6c2617f38658d8c7)] __-__ update image (*Han Xiao*)
 - [[```25ecdafd```](https://github.com/jina-ai/jina/commit/25ecdafdfbfd89e550f0cc6062f72705bd3a67b8)] __-__ update readme structure (*Han Xiao*)
 - [[```d03aff85```](https://github.com/jina-ai/jina/commit/d03aff85b98b3b9c2337a5fb2c99dfec8a262bbc)] __-__ update layout (*Han Xiao*)
 - [[```8c6e1bb1```](https://github.com/jina-ai/jina/commit/8c6e1bb128883a0b709dbb19b255c87aa3bf0bac)] __-__ update jina 101 and theme (*Han Xiao*)
 - [[```7a2f4969```](https://github.com/jina-ai/jina/commit/7a2f4969599f4e3d951328a4fa863ddf63226acc)] __-__ update copyright (*Han Xiao*)
 - [[```f3ab3764```](https://github.com/jina-ai/jina/commit/f3ab37643b1349b014d89f45fdcbeae340914a8a)] __-__ update 101 layout (*Han Xiao*)
 - [[```6e42b8d8```](https://github.com/jina-ai/jina/commit/6e42b8d83bc3f2444ca36dc13d8176afc1e47dc3)] __-__ test 101 doc (*Han Xiao*)
 - [[```9d9db74f```](https://github.com/jina-ai/jina/commit/9d9db74f440ca8bdf9af8c1f75836b5e1bc6158f)] __-__ update 101 (*Han Xiao*)
 - [[```925600fe```](https://github.com/jina-ai/jina/commit/925600fe551b068f7034158dea34d7f51dd1bc67)] __-__ update language order (*Han Xiao*)
 - [[```3d272587```](https://github.com/jina-ai/jina/commit/3d2725874cf6dfd6782afd4b8de4b44df2620c01)] __-__ fix layout (*Han Xiao*)
 - [[```ae4e9db8```](https://github.com/jina-ai/jina/commit/ae4e9db80302584bd49e09f8c5bdac4397e56ec8)] __-__ fix layout 101 (*Han Xiao*)

## Release Note (`0.1.0`)

> Release time: 2020-04-27 22:52:04



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  🙇


### 🐞 Bug fixes

 - [[```da3671c1```](https://github.com/jina-ai/jina/commit/da3671c12574813d9ded352a7cb79aba7dcdf1a7)] __-__ setup script (*Han Xiao*)

### 🏁 Unit Test and CICD

 - [[```530bbd09```](https://github.com/jina-ai/jina/commit/530bbd09cdcae564773db76f805eee5699f2fa33)] __-__ revert force tag (*Han Xiao*)
 - [[```1687a058```](https://github.com/jina-ai/jina/commit/1687a058b80db6a887e395d4f6c07e7d690082bd)] __-__ remove force tag (*Han Xiao*)

### 🍹 Other Improvements

 - [[```80a51403```](https://github.com/jina-ai/jina/commit/80a51403144e6ec9958a3058cd70955dedb9b27f)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```7ee1c3e0```](https://github.com/jina-ai/jina/commit/7ee1c3e06c3ee37012d749f046d45af7debef811)] __-__ __version__: bumping version to 0.0.10 (*Jina Dev Bot*)

## Release Note (`0.1.1`)

> Release time: 2020-04-28 09:43:18



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  🙇


### 🐞 Bug fixes

 - [[```e7cc2079```](https://github.com/jina-ai/jina/commit/e7cc2079e644ccfdd053c5c83cf5b0fa4db3175e)] __-__ hello world template (*Han Xiao*)
 - [[```61a0fd43```](https://github.com/jina-ai/jina/commit/61a0fd435f5db6a34fbdaef61693e6cdc61bd5ef)] __-__ badge links (*Han Xiao*)

### 🏁 Unit Test and CICD

 - [[```71581a9e```](https://github.com/jina-ai/jina/commit/71581a9e00ac2d57e0265b85d2717c5823d0f80f)] __-__ trigger first release (*Han Xiao*)

### 🍹 Other Improvements

 - [[```0e9fb9df```](https://github.com/jina-ai/jina/commit/0e9fb9df716661548ed5a859db286add06adc601)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```9ce86752```](https://github.com/jina-ai/jina/commit/9ce86752eac0f6062a30841951351767cfa76ee1)] __-__ __version__: bumping version to 0.1.1 (*Jina Dev Bot*)

## Release Note (`0.1.2`)

> Release time: 2020-04-28 14:21:31



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  🙇


### 🐞 Bug fixes

 - [[```0e605cec```](https://github.com/jina-ai/jina/commit/0e605cec769c2d2406f8f4479a95c6004f1b98fc)] __-__ ar (*Han Xiao*)

### 📗 Documentation

 - [[```f6dc0231```](https://github.com/jina-ai/jina/commit/f6dc02316170ebb37b9515db75c2ef50c4eb1ac8)] __-__ update sphinx 101 (*Han Xiao*)

### 🍹 Other Improvements

 - [[```a947ca45```](https://github.com/jina-ai/jina/commit/a947ca45b1e036e6036570f80a2717f645e9f5c8)] __-__ hotfix cli 3 (*Han Xiao*)
 - [[```281b90a9```](https://github.com/jina-ai/jina/commit/281b90a998aec9a3f268954d90566c4699b6837e)] __-__ hotfix cli 2 (*Han Xiao*)
 - [[```b7b80f0a```](https://github.com/jina-ai/jina/commit/b7b80f0a575f6fa258624e865798cf3f9f49153d)] __-__ hotfix cli (*Han Xiao*)
 - [[```5c9d6f33```](https://github.com/jina-ai/jina/commit/5c9d6f33bf5c13fba1bea862190533402a3451f3)] __-__ fix typo in readme (*Han Xiao*)
 - [[```9157e1a9```](https://github.com/jina-ai/jina/commit/9157e1a9429ccd04c7e5123273d40b136f69d977)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```cad622ef```](https://github.com/jina-ai/jina/commit/cad622ef266c268c4d6406db8d622d393c9ffe66)] __-__ revert back to friday release (*Han Xiao*)
 - [[```f7b6adb5```](https://github.com/jina-ai/jina/commit/f7b6adb5f53363f8b0ce0b585a79877f4ef15f8e)] __-__ fix pypi link (*Han Xiao*)
 - [[```2122b3c2```](https://github.com/jina-ai/jina/commit/2122b3c254f88cfb053f6ee05591932bafcd6534)] __-__ __version__: bumping version to 0.1.2 (*Jina Dev Bot*)

## Release Note (`0.1.3`)

> Release time: 2020-05-01 15:57:27



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Nan Wang,  Jina Dev Bot,  🙇


### 🐞 Bug fixes

 - [[```8279bdc6```](https://github.com/jina-ai/jina/commit/8279bdc68d0ad5a751db5e2702c30f3f350fabc5)] __-__ optimize helloworld network load (*Han Xiao*)
 - [[```a76cdece```](https://github.com/jina-ai/jina/commit/a76cdece9f39de42fec05643776501f6ef893019)] __-__ __docs__: minor fix (*Nan Wang*)
 - [[```9a21b91f```](https://github.com/jina-ai/jina/commit/9a21b91f0115f36f5ad3a60a0e7a1fa6bd588f88)] __-__ __docs__: update cmd in README (*Nan Wang*)

### 📗 Documentation

 - [[```41dfa4b9```](https://github.com/jina-ai/jina/commit/41dfa4b9635c19e5a80cd55859ea3a699176e550)] __-__ add io function explain (*Han Xiao*)
 - [[```79cc8825```](https://github.com/jina-ai/jina/commit/79cc8825cead2de60e1bacf186b38effa73bd996)] __-__ fix pip install instruction (*Han Xiao*)
 - [[```6e8d2d9e```](https://github.com/jina-ai/jina/commit/6e8d2d9ebc73c5868fda3ab62f46464a6e38056e)] __-__ fix link 101 to github (*Han Xiao*)

### 🏁 Unit Test and CICD

 - [[```eaa43dfd```](https://github.com/jina-ai/jina/commit/eaa43dfd8e35cfaa2e7c35fec3f0483b9a0fca68)] __-__ add unit test for quantization (*Han Xiao*)

### 🍹 Other Improvements

 - [[```6a880a1b```](https://github.com/jina-ai/jina/commit/6a880a1b9af2ace9e2cb3346dc017028f6a78114)] __-__ update issue template (*Han Xiao*)
 - [[```3b9c3f5b```](https://github.com/jina-ai/jina/commit/3b9c3f5b6b87c7b93aca482d2273addec8e692b8)] __-__ fix twitter link (*Han Xiao*)
 - [[```13d44e96```](https://github.com/jina-ai/jina/commit/13d44e96d02d8882077c237c9916dc0b8a142e50)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```a66136c9```](https://github.com/jina-ai/jina/commit/a66136c9ca7b48936bb29ead86ec9b3388f56d2d)] __-__ __version__: bumping version to 0.1.3 (*Jina Dev Bot*)

## Release Note (`0.1.4`)

> Release time: 2020-05-01 18:51:49



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  🙇


### 🐞 Bug fixes

 - [[```c037c72f```](https://github.com/jina-ai/jina/commit/c037c72f820feb1a98ac51315a99c022ca9c65cb)] __-__ resource usage in setup #343 (*Han Xiao*)
 - [[```c1f84a75```](https://github.com/jina-ai/jina/commit/c1f84a75ebdabd6b563bf0b2074e7f43f33d5ecb)] __-__ setup version warning (*Han Xiao*)

### 🚧 Code Refactoring

 - [[```77e49eb6```](https://github.com/jina-ai/jina/commit/77e49eb699c382798e0f94b4176f0905c96edbd7)] __-__ rename flow io args (*Han Xiao*)

### 🍹 Other Improvements

 - [[```65fa39a9```](https://github.com/jina-ai/jina/commit/65fa39a9c3cce8150e46a117637a5fd05b1e467b)] __-__ hotfix setup.py (*Han Xiao*)
 - [[```389f6081```](https://github.com/jina-ai/jina/commit/389f6081d19e3b9e473dab7d2eecc67165717b1c)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```14abbbfe```](https://github.com/jina-ai/jina/commit/14abbbfef2b53a70ba8c9ae055257049c5b58f4d)] __-__ __version__: bumping version to 0.1.4 (*Jina Dev Bot*)

## Release Note (`0.1.5`)

> Release time: 2020-05-02 21:47:39



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  🙇


### 🆕 New Features

 - [[```df2c1551```](https://github.com/jina-ai/jina/commit/df2c15519f15b67f6393b665a7836f56a0b2a947)] __-__ __cli__: export api to json and yaml files (*Han Xiao*)
 - [[```4160994d```](https://github.com/jina-ai/jina/commit/4160994d197b8f1103c5f4036cbe3edb6915381c)] __-__ add compression as an option to peapod (*Han Xiao*)

### 🐞 Bug fixes

 - [[```5f4bffd3```](https://github.com/jina-ai/jina/commit/5f4bffd3c0d6580b6220795a3e436d3e24fe9daa)] __-__ __cli__: update cli autocomplete (*Han Xiao*)
 - [[```eda56495```](https://github.com/jina-ai/jina/commit/eda56495813fb8ea26bef3ff73ec2ae5423234ee)] __-__ __docker__: add gcc dependency (*Han Xiao*)
 - [[```eb2eaaf5```](https://github.com/jina-ai/jina/commit/eb2eaaf507cb9bb967abe0d3e3ea61f4367ef6a3)] __-__ __zmqlet__: add import check for lz4 (*Han Xiao*)

### 📗 Documentation

 - [[```cf152c35```](https://github.com/jina-ai/jina/commit/cf152c35ab8efb55dfbf46b3ca637aaa78942885)] __-__ add schema to docs (*Han Xiao*)
 - [[```4caa2c7a```](https://github.com/jina-ai/jina/commit/4caa2c7a2f89348a92417aeb49f4657025e9599f)] __-__ add nightly to release (*Han Xiao*)

### 🏁 Unit Test and CICD

 - [[```1550749a```](https://github.com/jina-ai/jina/commit/1550749a55cd65c64e79901be1f84c111d5376ae)] __-__ fix schema generator (*Han Xiao*)
 - [[```ee6075e7```](https://github.com/jina-ai/jina/commit/ee6075e7b474e9038ae2e225d95de5e4f46edf98)] __-__ add nightly build speedup cd (*Han Xiao*)
 - [[```7f551ed7```](https://github.com/jina-ai/jina/commit/7f551ed725d0367dc9214ea1e7f6145535c68e4c)] __-__ add schema generator (*Han Xiao*)

### 🍹 Other Improvements

 - [[```3e8d881a```](https://github.com/jina-ai/jina/commit/3e8d881af1de74c94f612d1cbc595995684e6653)] __-__ hotfix add schema (*Han Xiao*)
 - [[```9a8d907e```](https://github.com/jina-ai/jina/commit/9a8d907e77388482af47f2575f8039aa61e82cb3)] __-__ fix api schema link (*Han Xiao*)
 - [[```58c79d4e```](https://github.com/jina-ai/jina/commit/58c79d4e1e1f49b6f2504f8825a224006681a8cb)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```4af096dc```](https://github.com/jina-ai/jina/commit/4af096dcebf6a84499bf2e029ca1b400132a956d)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```da8e7e45```](https://github.com/jina-ai/jina/commit/da8e7e452b4b81f00b1e811d37844ecf25d20b69)] __-__ reformat test code (*Han Xiao*)
 - [[```d5052300```](https://github.com/jina-ai/jina/commit/d5052300edf48f3716add36bb92c7190c6be21ad)] __-__ __version__: bumping version to 0.1.5 (*Jina Dev Bot*)

## Release Note (`0.1.6`)

> Release time: 2020-05-02 22:42:12



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  🙇


### 🏁 Unit Test and CICD

 - [[```37ee56db```](https://github.com/jina-ai/jina/commit/37ee56db923e7a45ea5c1b41e884697615f26698)] __-__ fix docker build opt size (*Han Xiao*)

### 🍹 Other Improvements

 - [[```61c97022```](https://github.com/jina-ai/jina/commit/61c97022356bf0a496b76eaa76b78d01484c22af)] __-__ hotfix dockerfile for latest (*Han Xiao*)
 - [[```2e7bf04c```](https://github.com/jina-ai/jina/commit/2e7bf04c94d2a7279b37fe53309562e88ca5c24b)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```5e37d3fe```](https://github.com/jina-ai/jina/commit/5e37d3fe58bf7c808ce836d6a496904a98788b36)] __-__ __version__: bumping version to 0.1.6 (*Jina Dev Bot*)

## Release Note (`0.1.7`)

> Release time: 2020-05-04 14:18:12



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  🙇


### 🐞 Bug fixes

 - [[```6640bb53```](https://github.com/jina-ai/jina/commit/6640bb53ef1bf311c5540f2dbe49325fc2affedb)] __-__ __cli__: remove color imports (*Han Xiao*)
 - [[```01ff133c```](https://github.com/jina-ai/jina/commit/01ff133c26a96fc36f3bd8f0e6310631cd781b04)] __-__ __hello-world__: fix compression dep in hw demo (*Han Xiao*)

### 🍹 Other Improvements

 - [[```f0a5e4d1```](https://github.com/jina-ai/jina/commit/f0a5e4d187d61cd9ef7bf4867d79ce718d5f905b)] __-__ hotfix fix dep for latest (*Han Xiao*)
 - [[```e4d44d45```](https://github.com/jina-ai/jina/commit/e4d44d45ceb3bd85fe80c25edf71cd4a64fddb01)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```df52882e```](https://github.com/jina-ai/jina/commit/df52882e921de8038914b0c5daf02374decec51b)] __-__ __version__: bumping version to 0.1.7 (*Jina Dev Bot*)

## Release Note (`0.1.8`)

> Release time: 2020-05-06 15:15:54



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Nan Wang,  Xiong Ma,  Jina Dev Bot,  🙇


### 🆕 New Features

 - [[```153e2aab```](https://github.com/jina-ai/jina/commit/153e2aab77e08c05b361ddb83a72822d284539f4)] __-__ __peapod__: add logs grouping by pod name (*Han Xiao*)

### 🐞 Bug fixes

 - [[```c78ec6ec```](https://github.com/jina-ai/jina/commit/c78ec6ecf27ea38e1c4ac51fe284ff587af207be)] __-__ __driver__: fix search driver logic in shards (*Han Xiao*)
 - [[```9cc2a050```](https://github.com/jina-ai/jina/commit/9cc2a050dc2cde73910c78af6780ad5aadddffaf)] __-__ style (*Han Xiao*)
 - [[```eb59499e```](https://github.com/jina-ai/jina/commit/eb59499e8787bde83d4f758c3ec0d3be49beffa3)] __-__ __indexer__: fix empty indexer reading (*Han Xiao*)
 - [[```1c1a048c```](https://github.com/jina-ai/jina/commit/1c1a048c036c0e7955e45aa889d5617d64ff1ece)] __-__ add the env var for testing gpu (*Nan Wang*)
 - [[```bea55a59```](https://github.com/jina-ai/jina/commit/bea55a59708ea9a3b6b43ee8e92bbc21b0edff73)] __-__ __logging__: add unittest (*Xiong Ma*)
 - [[```bbbb9e71```](https://github.com/jina-ai/jina/commit/bbbb9e7161ef9905d1b2930029c038a687f615db)] __-__ __logging__: fix success level message (*Xiong Ma*)
 - [[```f072778e```](https://github.com/jina-ai/jina/commit/f072778ef700129c5c8d13b29b325c93d8ca664e)] __-__ remove gpu dependencies (*Nan Wang*)
 - [[```41dd06eb```](https://github.com/jina-ai/jina/commit/41dd06eb51cd3a118909b086ad746442a5e57dec)] __-__ clean up extrarequirements (*Nan Wang*)
 - [[```d797a0a0```](https://github.com/jina-ai/jina/commit/d797a0a011c47a05e09c791b4e3ac1b6e6a9e17a)] __-__ add docs (*Nan Wang*)
 - [[```9a9a838e```](https://github.com/jina-ai/jina/commit/9a9a838e85cee28931e50ee8c654628a177ab33d)] __-__ __shards__: fix shard writing logic when closing (*Han Xiao*)
 - [[```c4fe17d4```](https://github.com/jina-ai/jina/commit/c4fe17d4b4b09b7af7fa401185360a6d76066557)] __-__ refactoring codes (*Nan Wang*)
 - [[```0048f346```](https://github.com/jina-ai/jina/commit/0048f34629230140c4fc1eb7254f9643bbe040e1)] __-__ refactoring class names (*Nan Wang*)
 - [[```eaee9172```](https://github.com/jina-ai/jina/commit/eaee91722a856e04d96d5cd935322b9ff500037a)] __-__ fix extrarequirements (*Nan Wang*)
 - [[```9a44cabe```](https://github.com/jina-ai/jina/commit/9a44cabe6fa6c596e99bc6578c731aebe9a35d67)] __-__ adapt the extrarequirements (*Nan Wang*)
 - [[```4931df1d```](https://github.com/jina-ai/jina/commit/4931df1d6e3a69892926d6837b184cc7616540ec)] __-__ fix flair on gpu (*Nan Wang*)
 - [[```1ddf2480```](https://github.com/jina-ai/jina/commit/1ddf248024d5a92600ae3924c13aed66cc5ba3d6)] __-__ fix transformers on gpu (*Nan Wang*)
 - [[```88982882```](https://github.com/jina-ai/jina/commit/88982882475a605b9e0fa0030f29b12921212778)] __-__ fix video unittests on gpu (*Nan Wang*)
 - [[```d650e72f```](https://github.com/jina-ai/jina/commit/d650e72f97c887e6b1f2ac661d1d881df60479d1)] __-__ fix tensorflow on gpu (*Nan Wang*)
 - [[```a37e9d7b```](https://github.com/jina-ai/jina/commit/a37e9d7b1e472a78caf88669ba5873e319475b5a)] __-__ fix unit tests for torchvision (*Nan Wang*)
 - [[```ab7e663e```](https://github.com/jina-ai/jina/commit/ab7e663e1e7c658605d7dc9731c7e7898f548151)] __-__ fix unit tests for tfkeras (*Nan Wang*)
 - [[```bd0cb496```](https://github.com/jina-ai/jina/commit/bd0cb496383c90b49694a3bcdfb43ae01bee00f5)] __-__ fix the unittests on gpu (*Nan Wang*)
 - [[```9e75d5e0```](https://github.com/jina-ai/jina/commit/9e75d5e0b79bce7aef4d6b86d78054750938095a)] __-__ fix the paddlehub on gpu (*Nan Wang*)
 - [[```a40b185d```](https://github.com/jina-ai/jina/commit/a40b185da15529c05a56b1a2cef6d637d6259c9b)] __-__ rename the classes (*Nan Wang*)
 - [[```4077a182```](https://github.com/jina-ai/jina/commit/4077a18264140e26872e436072ee77b6da886612)] __-__ __hello-world__: add comments to help understand (*Han Xiao*)
 - [[```9e3c8976```](https://github.com/jina-ai/jina/commit/9e3c89767dee31aa8011421a64799741a60ecc7b)] __-__ rename base classes (*Nan Wang*)
 - [[```67cf25fd```](https://github.com/jina-ai/jina/commit/67cf25fd8fb06c5ecd0fa0ce7c884d8b3394d528)] __-__ __executors__: fix gpu supports (*Nan Wang*)
 - [[```01ff133c```](https://github.com/jina-ai/jina/commit/01ff133c26a96fc36f3bd8f0e6310631cd781b04)] __-__ __hello-world__: fix compression dep in hw demo (*Han Xiao*)

### 🏁 Unit Test and CICD

 - [[```1f052743```](https://github.com/jina-ai/jina/commit/1f0527431be244024761767d1e6bfcea3e6fa0aa)] __-__ fix index shard testing (*Han Xiao*)

### 🍹 Other Improvements

 - [[```15a4216e```](https://github.com/jina-ai/jina/commit/15a4216e9b439eb8994809898921e511ee7e9d6f)] __-__ hotfix update env list (*Han Xiao*)
 - [[```0d8d8924```](https://github.com/jina-ai/jina/commit/0d8d89242123a043761093b35f74ba603e4172c7)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```97ab83a9```](https://github.com/jina-ai/jina/commit/97ab83a904474586eaec575a65493bf5176f6790)] __-__ __version__: bumping version to 0.1.8 (*Jina Dev Bot*)
 - [[```df52882e```](https://github.com/jina-ai/jina/commit/df52882e921de8038914b0c5daf02374decec51b)] __-__ __version__: bumping version to 0.1.7 (*Jina Dev Bot*)
 - [[```61c97022```](https://github.com/jina-ai/jina/commit/61c97022356bf0a496b76eaa76b78d01484c22af)] __-__ hotfix dockerfile for latest (*Han Xiao*)

## Release Note (`0.1.9`)

> Release time: 2020-05-08 15:57:49



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Nan Wang,  Jina Dev Bot,  🙇


### 🆕 New Features

 - [[```657b002c```](https://github.com/jina-ai/jina/commit/657b002c687f3b6c85f683986d9bcb4c02b89afd)] __-__ improve python api for client (*Han Xiao*)
 - [[```2b4260f5```](https://github.com/jina-ai/jina/commit/2b4260f5eae8e34d48b212888ecf11e241a8d7e1)] __-__ __encoder__: add farm nlp encoder (*Han Xiao*)

### 🐞 Bug fixes

 - [[```c125fd1f```](https://github.com/jina-ai/jina/commit/c125fd1f644c483d0194d817e15c1ee88fe4a459)] __-__ default args cause ping error (*Han Xiao*)

### 🚧 Code Refactoring

 - [[```b9fab059```](https://github.com/jina-ai/jina/commit/b9fab05941a4442397a73d18cc4765c294ae5917)] __-__ fix the tf version (*Nan Wang*)
 - [[```d6e893c7```](https://github.com/jina-ai/jina/commit/d6e893c7c168111088c0896ccebab256010bbe25)] __-__ __encoders__: refactoring transformers api (*Nan Wang*)
 - [[```b45944c5```](https://github.com/jina-ai/jina/commit/b45944c53dfcfb559584df9109f25b914309aedb)] __-__ __executors__: adapt code blocks (*Nan Wang*)
 - [[```ac4b10ff```](https://github.com/jina-ai/jina/commit/ac4b10ff32ec8972c64fe809ff9dcdaf7efffac9)] __-__ on_gpu and to_device in baseclass (*Han Xiao*)

### 🏁 Unit Test and CICD

 - [[```b427224e```](https://github.com/jina-ai/jina/commit/b427224e3ba368168b774bc6fa5a2d5f5e84c7c4)] __-__ set test timout to 15m (*Han Xiao*)

### 🍹 Other Improvements

 - [[```a0a13c80```](https://github.com/jina-ai/jina/commit/a0a13c80ca45fd5f1dcbf2b45c1695c68015d41e)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```cde8df99```](https://github.com/jina-ai/jina/commit/cde8df9995da626d4c1e41b07432b2d8748c10f1)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```27039e01```](https://github.com/jina-ai/jina/commit/27039e011d3b42a04876220dc964acc8aea1561a)] __-__ fix phrases in performant (*Han Xiao*)
 - [[```cd5e640c```](https://github.com/jina-ai/jina/commit/cd5e640cd76a40afd9f2e118e0edfb418b5274ea)] __-__ __version__: bumping version to 0.1.9 (*Jina Dev Bot*)

## Release Note (`0.1.10`)

> Release time: 2020-05-09 09:37:04



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  Nan Wang,  🙇


### 🆕 New Features

 - [[```ed8fe7e0```](https://github.com/jina-ai/jina/commit/ed8fe7e073b0e48e2012c802f08b66dbe7861933)] __-__ add unary request send/recv handling (*Han Xiao*)
 - [[```30bd550a```](https://github.com/jina-ai/jina/commit/30bd550a460c46ae6de8e13793e7471e5a0a8b94)] __-__ __proto__: add unary grpc endpoint (*Han Xiao*)

### 🐞 Bug fixes

 - [[```d686726e```](https://github.com/jina-ai/jina/commit/d686726e7ee5c30dbcb07dcc3ce8edbff9ddabaf)] __-__ fix the tf devices (*Nan Wang*)
 - [[```61ce7c18```](https://github.com/jina-ai/jina/commit/61ce7c1821c8a94020a2de3bd183a732f5f59b6c)] __-__ fix the unittests (*Nan Wang*)
 - [[```75c71dd6```](https://github.com/jina-ai/jina/commit/75c71dd6adaa05dc847e31832fbeab7e91ec9a2b)] __-__ __executors__: fix the mro issues (*Nan Wang*)
 - [[```bda92d81```](https://github.com/jina-ai/jina/commit/bda92d8174fd59a70188781e725b2fe1b1a7b3df)] __-__ __executors__: fix the mro issue (*Nan Wang*)

### 🚧 Code Refactoring

 - [[```6b3aa7d6```](https://github.com/jina-ai/jina/commit/6b3aa7d6b1458da9c029c6f5c371465a870ddad2)] __-__ add kwargs override in python client io (*Han Xiao*)

### 📗 Documentation

 - [[```dd407191```](https://github.com/jina-ai/jina/commit/dd407191764e477bff7de4a8ed33915aef36f0fa)] __-__ update toc of tutorials (*Han Xiao*)

### 🍹 Other Improvements

 - [[```6927f7fa```](https://github.com/jina-ai/jina/commit/6927f7fa36108cc093fec5bbb2640b90a12a2050)] __-__ hotfix fix encoder inherit map (*Han Xiao*)
 - [[```ef92cb17```](https://github.com/jina-ai/jina/commit/ef92cb1755cc4428ea60b7250cbad51941ff5a86)] __-__ reformat the code and imports (*Han Xiao*)
 - [[```2911a455```](https://github.com/jina-ai/jina/commit/2911a4553bfe45cfbe71bb6b80512c2e8234b0b5)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```2972eb72```](https://github.com/jina-ai/jina/commit/2972eb7203fe854258dfc2fcb9958e7566d5e9d9)] __-__ hotfix the mro issues in executors (*Nan Wang*)
 - [[```55cae572```](https://github.com/jina-ai/jina/commit/55cae572fc4810e6dcc7fe9174ab5f5006bb471a)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```6e60a79e```](https://github.com/jina-ai/jina/commit/6e60a79eb7313510a215540bf5f5298d577bf2fa)] __-__ reformat the code (*Han Xiao*)
 - [[```b7f138b6```](https://github.com/jina-ai/jina/commit/b7f138b681fb2c25c991c0a957a1bfab2a61ae91)] __-__ __version__: bumping version to 0.1.10 (*Jina Dev Bot*)

