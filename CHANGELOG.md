


















































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
- [Release Note (`0.1.11`)](#release-note-0111)
- [Release Note (`0.1.12`)](#release-note-0112)
- [Release Note (`0.1.13`)](#release-note-0113)
- [Release Note (`0.1.14`)](#release-note-0114)
- [Release Note (`0.2.0`)](#release-note-020)
- [Release Note (`0.2.1`)](#release-note-021)
- [Release Note (`0.2.2`)](#release-note-022)
- [Release Note (`0.2.3`)](#release-note-023)
- [Release Note (`0.2.4`)](#release-note-024)
- [Release Note (`0.2.5`)](#release-note-025)
- [Release Note (`0.2.6`)](#release-note-026)
- [Release Note (`0.2.7`)](#release-note-027)
- [Release Note (`0.2.8`)](#release-note-028)
- [Release Note (`0.2.9`)](#release-note-029)
- [Release Note (`0.2.10`)](#release-note-0210)
- [Release Note (`0.3.0`)](#release-note-030)
- [Release Note (`0.3.1`)](#release-note-031)
- [Release Note (`0.3.2`)](#release-note-032)
- [Release Note (`0.3.3`)](#release-note-033)
- [Release Note (`0.3.4`)](#release-note-034)
- [Release Note (`0.3.5`)](#release-note-035)
- [Release Note (`0.3.6`)](#release-note-036)

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

## Release Note (`0.1.11`)

> Release time: 2020-05-11 13:56:11



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Nan Wang,  Jina Dev Bot,  xiong-ma,  🙇


### 🐞 Bug fixes

 - [[```482ed876```](https://github.com/jina-ai/jina/commit/482ed876dcdce0d3003800b134ab1ed3960d5e48)] __-__ __transformer__: delete tmp attr (*xiong-ma*)
 - [[```e5756b3c```](https://github.com/jina-ai/jina/commit/e5756b3c169b02f6d5de70c33acce20170929cc2)] __-__ __transformer__: change getattr to hasattr (*xiong-ma*)
 - [[```2370dd6b```](https://github.com/jina-ai/jina/commit/2370dd6b046d7cc7ca14f98055a967e22200bb96)] __-__ __transformer__: fix cls embedding (*xiong-ma*)

### 📗 Documentation

 - [[```b4bf44d4```](https://github.com/jina-ai/jina/commit/b4bf44d441d4a48c485bad499cd6e8c0e276a9da)] __-__ __executors__: fix a typo (*Nan Wang*)
 - [[```db8e00bc```](https://github.com/jina-ai/jina/commit/db8e00bcbd3b057e8b6dba6ce0dc2e022a9dbc23)] __-__ __executors__: add more docs (*Nan Wang*)
 - [[```b147a1ed```](https://github.com/jina-ai/jina/commit/b147a1edccd9e857cda3b4ea66f52741b931382e)] __-__ __executors__: fix the doc for the Sentencizer (*Nan Wang*)

### 🏁 Unit Test and CICD

 - [[```d9f628ad```](https://github.com/jina-ai/jina/commit/d9f628ada4daf191ada631ee1fc204ade853252e)] __-__ fix dir path add dep to contrib md (*Han Xiao*)

### 🍹 Other Improvements

 - [[```15380fa6```](https://github.com/jina-ai/jina/commit/15380fa697d5e88d590fc17472330cd34c6972e7)] __-__ hotfix include extra req to manifest (*Han Xiao*)
 - [[```21e574b9```](https://github.com/jina-ai/jina/commit/21e574b9ed0f4d1f6b2f94cddad3d711ddf95972)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```28202863```](https://github.com/jina-ai/jina/commit/2820286360ad40b4b706488559e713272575c63a)] __-__ __version__: bumping version to 0.1.11 (*Jina Dev Bot*)

## Release Note (`0.1.12`)

> Release time: 2020-05-15 15:57:28



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Nan Wang,  Joan Fontanals Martinez,  Jina Dev Bot,  xiong-ma,  🙇


### 🆕 New Features

 - [[```2a3abaa1```](https://github.com/jina-ai/jina/commit/2a3abaa1e0a1aabe4fb556c51404fed26a28a96b)] __-__ __executors__: add custom torch vision encoder (*Joan Fontanals Martinez*)

### 🐞 Bug fixes

 - [[```24d35375```](https://github.com/jina-ai/jina/commit/24d35375fe7f293976dea0ae0dd0915679941416)] __-__ fix string literals in the forward references (*Nan Wang*)
 - [[```91ca702a```](https://github.com/jina-ai/jina/commit/91ca702ab656b9f503ab38af2e0458651f114e88)] __-__ undo the pylint fix (*Nan Wang*)
 - [[```e999af1d```](https://github.com/jina-ai/jina/commit/e999af1daa59597eb17eec57b15dc38766e52c9b)] __-__ fix the pylint error (*Nan Wang*)
 - [[```b97885aa```](https://github.com/jina-ai/jina/commit/b97885aad08261d4594622b82eeea07f471416f5)] __-__ __flow__: fix the port_grpc bug (*Nan Wang*)
 - [[```fa07110b```](https://github.com/jina-ai/jina/commit/fa07110b06fead2bcbd1213e22896674894d24c6)] __-__ __drivers__: fix the bug in handling empty chunks (*Nan Wang*)
 - [[```5b62c315```](https://github.com/jina-ai/jina/commit/5b62c315d1615835d904584b357ac71e6e0ab4e3)] __-__ __encoders__: fix the broken transformers (*Nan Wang*)
 - [[```482ed876```](https://github.com/jina-ai/jina/commit/482ed876dcdce0d3003800b134ab1ed3960d5e48)] __-__ __transformer__: delete tmp attr (*xiong-ma*)
 - [[```e5756b3c```](https://github.com/jina-ai/jina/commit/e5756b3c169b02f6d5de70c33acce20170929cc2)] __-__ __transformer__: change getattr to hasattr (*xiong-ma*)
 - [[```2370dd6b```](https://github.com/jina-ai/jina/commit/2370dd6b046d7cc7ca14f98055a967e22200bb96)] __-__ __transformer__: fix cls embedding (*xiong-ma*)

### 📗 Documentation

 - [[```b4bf44d4```](https://github.com/jina-ai/jina/commit/b4bf44d441d4a48c485bad499cd6e8c0e276a9da)] __-__ __executors__: fix a typo (*Nan Wang*)
 - [[```db8e00bc```](https://github.com/jina-ai/jina/commit/db8e00bcbd3b057e8b6dba6ce0dc2e022a9dbc23)] __-__ __executors__: add more docs (*Nan Wang*)
 - [[```b147a1ed```](https://github.com/jina-ai/jina/commit/b147a1edccd9e857cda3b4ea66f52741b931382e)] __-__ __executors__: fix the doc for the Sentencizer (*Nan Wang*)

### 🏁 Unit Test and CICD

 - [[```b57685c0```](https://github.com/jina-ai/jina/commit/b57685c058fea07cabece1a3ff62f9061818c62f)] __-__ sync with master (*Han Xiao*)
 - [[```cdd6feff```](https://github.com/jina-ai/jina/commit/cdd6feffd60c0b16735bbc02657a357a37459d0a)] __-__ update cla credentials (*Han Xiao*)
 - [[```4eb393de```](https://github.com/jina-ai/jina/commit/4eb393de86bd0e286e221c6802b5a6e4a81000e1)] __-__ change to github token (*Han Xiao*)
 - [[```adf126f1```](https://github.com/jina-ai/jina/commit/adf126f13d6e4e79a66f7b962d72fb5b06c665b2)] __-__ fix cla.yml (*Han Xiao*)
 - [[```d9f628ad```](https://github.com/jina-ai/jina/commit/d9f628ada4daf191ada631ee1fc204ade853252e)] __-__ fix dir path add dep to contrib md (*Han Xiao*)

### 🍹 Other Improvements

 - [[```d147c519```](https://github.com/jina-ai/jina/commit/d147c519f5622ed8bc76442f804634a2009c6874)] __-__ update credentials (*Han Xiao*)
 - [[```f5651ccc```](https://github.com/jina-ai/jina/commit/f5651cccd79a9efdc6dd69b9d17baacfc4102ec7)] __-__ fix cla dev-bot credentials (*Han Xiao*)
 - [[```49aee4af```](https://github.com/jina-ai/jina/commit/49aee4af3993cc5eeb534f9b08faf7fc1bd21257)] __-__ fix cla-bot credential (*Han Xiao*)
 - [[```340cc59c```](https://github.com/jina-ai/jina/commit/340cc59c16cf1e6e5c9cecc939b582ea44db8177)] __-__ move cla to separate branch (*Han Xiao*)
 - [[```4c6c5ac9```](https://github.com/jina-ai/jina/commit/4c6c5ac95c32ea0910aa1655c6d3db41cdd260de)] __-__ change secrets in all ci pipeline (*Han Xiao*)
 - [[```80224f78```](https://github.com/jina-ai/jina/commit/80224f78d28afa9037807f2bd8526e81b8396ecf)] __-__ add command run for issue (*Han Xiao*)
 - [[```9158e962```](https://github.com/jina-ai/jina/commit/9158e9621fc79ef27fd815f3245ce1da94d0613c)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```c762ae65```](https://github.com/jina-ai/jina/commit/c762ae65e2df3be77e74bc0ad69691c2f4d983cd)] __-__ __version__: bumping version to 0.1.12 (*Jina Dev Bot*)
 - [[```28202863```](https://github.com/jina-ai/jina/commit/2820286360ad40b4b706488559e713272575c63a)] __-__ __version__: bumping version to 0.1.11 (*Jina Dev Bot*)
 - [[```6927f7fa```](https://github.com/jina-ai/jina/commit/6927f7fa36108cc093fec5bbb2640b90a12a2050)] __-__ hotfix fix encoder inherit map (*Han Xiao*)

## Release Note (`0.1.13`)

> Release time: 2020-05-22 15:57:41



🙇 We'd like to thank all contributors for this new release! In particular,
 antonkurenkov,  Han Xiao,  Jina Dev Bot,  Nan Wang,  guiferviz,  phamtrancsek12,  Tracy Pham,  🙇


### 🆕 New Features

 - [[```80f30168```](https://github.com/jina-ai/jina/commit/80f3016807eee059d87303853f49da687d4a3ad1)] __-__ __flow__: add block function pause process (*Han Xiao*)
 - [[```ee318d68```](https://github.com/jina-ai/jina/commit/ee318d685ad9986358aaa52e4700b05a753ffe36)] __-__ __crafter__: add data uri to bytes convert (*Han Xiao*)
 - [[```186e2fe9```](https://github.com/jina-ai/jina/commit/186e2fe9c26334cd3ec002c9f993a082fbeb9e51)] __-__ __proto__: add data uri as content of doc (*Han Xiao*)
 - [[```07c52dd9```](https://github.com/jina-ai/jina/commit/07c52dd9a0dc6d8b57b07af442400fd6f063a4a4)] __-__ __executors__: disable the unittest for grpc (*Nan Wang*)
 - [[```644e69fc```](https://github.com/jina-ai/jina/commit/644e69fc030e95e537f8b60a21b6d2ca2df66742)] __-__ __executors__: refactoring in response to the comments (*Nan Wang*)
 - [[```71739448```](https://github.com/jina-ai/jina/commit/71739448cbbf8ca0e46dd987bc5a4fb66c59d026)] __-__ __executors__: refactoring unit tests (*Nan Wang*)
 - [[```5c0d53cd```](https://github.com/jina-ai/jina/commit/5c0d53cdc5211b29ace7910f9238808658b8cc47)] __-__ __executors__: fix the method_name issues (*Nan Wang*)
 - [[```20563b2a```](https://github.com/jina-ai/jina/commit/20563b2a7c4c0dc6494c9e9102fb0c2dea7f7dee)] __-__ __executors__: add apis for other method_name (*Nan Wang*)
 - [[```15f9f1fb```](https://github.com/jina-ai/jina/commit/15f9f1fb7e715a5371298f74b02066e3ceb9a654)] __-__ __executors__: add typing (*Nan Wang*)
 - [[```ff89b38b```](https://github.com/jina-ai/jina/commit/ff89b38b66394203874a6b732458d6fada5e9824)] __-__ __executors__: add docs (*Nan Wang*)
 - [[```e57293f4```](https://github.com/jina-ai/jina/commit/e57293f429ffc54d005155aaae64114df59119af)] __-__ __executors__: refactoring codes (*Nan Wang*)
 - [[```625b3c70```](https://github.com/jina-ai/jina/commit/625b3c70b4a4371959b16fc5009e06a3c2e4d18b)] __-__ __executors__: add the tfserving client (*Nan Wang*)
 - [[```3470a6bd```](https://github.com/jina-ai/jina/commit/3470a6bd6e3c7f7ad9ca5b299ce31f60d25613e3)] __-__ __executors__: add executors wrapping a tfserving client (*Nan Wang*)
 - [[```48935875```](https://github.com/jina-ai/jina/commit/489358757254ef8b8ee8ade69db7f753aab723ea)] __-__ add rest api gateway (*Han Xiao*)
 - [[```e17f9405```](https://github.com/jina-ai/jina/commit/e17f9405427052dacb60d44ae169dd5708df8e21)] __-__ __executors__: add numeric crafter (*Tracy Pham*)

### 🐞 Bug fixes

 - [[```783ef306```](https://github.com/jina-ai/jina/commit/783ef3062c39a10423a915acf244c5a50b469c84)] __-__ fix pip install info (*Han Xiao*)
 - [[```ba3e1d88```](https://github.com/jina-ai/jina/commit/ba3e1d88f5ee78c0c30e06fa2771ed4efd0ce95c)] __-__ __crafter__: add data uri crafter (*Han Xiao*)
 - [[```17f586f2```](https://github.com/jina-ai/jina/commit/17f586f2d0efcc6fb57f74212110f9fb0379915f)] __-__ __gateway__: fix #435 empty request iterator (*Han Xiao*)
 - [[```ae7ee48c```](https://github.com/jina-ai/jina/commit/ae7ee48cb16ab49a0d2e9363537f948f02bf5068)] __-__ fix ci event (*Han Xiao*)
 - [[```41790109```](https://github.com/jina-ai/jina/commit/417901098cce90b22bc8f6c65b74164d12662e22)] __-__ __executors__: change the class inheritance of array reader (*phamtrancsek12*)
 - [[```5803ee99```](https://github.com/jina-ai/jina/commit/5803ee9981e58dece6ca47003e84c3322255f93f)] __-__ __zmqlet__: fix slow joiner when request is small (*Han Xiao*)
 - [[```1361baa1```](https://github.com/jina-ai/jina/commit/1361baa1e4838e635a96087351ca4a25c3aeac19)] __-__ __executor__: fix sign of condition (*guiferviz*)
 - [[```fa07110b```](https://github.com/jina-ai/jina/commit/fa07110b06fead2bcbd1213e22896674894d24c6)] __-__ __drivers__: fix the bug in handling empty chunks (*Nan Wang*)
 - [[```5b62c315```](https://github.com/jina-ai/jina/commit/5b62c315d1615835d904584b357ac71e6e0ab4e3)] __-__ __encoders__: fix the broken transformers (*Nan Wang*)

### 🚧 Code Refactoring

 - [[```aca3723b```](https://github.com/jina-ai/jina/commit/aca3723b661b1a1462a1cdfb0a78cd95fc08ae01)] __-__ __gateway__: use new data uri field (*Han Xiao*)
 - [[```4d11e113```](https://github.com/jina-ai/jina/commit/4d11e1131cdf5f388dc81c7e0febcd32c10447b1)] __-__ __executors__: rename numeric crafter (*phamtrancsek12*)

### 📗 Documentation

 - [[```d4d55618```](https://github.com/jina-ai/jina/commit/d4d556188872c52906694f9d1f195f502a9cec78)] __-__ add rest api spec (*Han Xiao*)
 - [[```6bdc7ee7```](https://github.com/jina-ai/jina/commit/6bdc7ee7d6fa4f4386b5c0a0fdc571388ab77d2f)] __-__ __executor__: improving docs (*guiferviz*)

### 🏁 Unit Test and CICD

 - [[```7e3dd089```](https://github.com/jina-ai/jina/commit/7e3dd0896a9685872df2d46a20eb5567891b2e64)] __-__ fix dependencies (*antonkurenkov*)
 - [[```60b2ef15```](https://github.com/jina-ai/jina/commit/60b2ef1572c5031034bc45c30d4ec7a112ffedd8)] __-__ add test for data uri crafter (*Han Xiao*)
 - [[```8d3b5940```](https://github.com/jina-ai/jina/commit/8d3b59400a6f0b1fa45f45e8c19af875739bc539)] __-__ __docker__: fix pip in docker (*Han Xiao*)
 - [[```7bb674d0```](https://github.com/jina-ai/jina/commit/7bb674d0f9d59f562a0d4d51eea0ed1b2d3a70d3)] __-__ __docker__: move gevent from pip into apt (*Han Xiao*)
 - [[```d3420d02```](https://github.com/jina-ai/jina/commit/d3420d022d74dce847e135269a1704a2972704f6)] __-__ trigger on published release (*antonkurenkov*)
 - [[```6caca895```](https://github.com/jina-ai/jina/commit/6caca8958df97e40e8108e2ba57fd90004b9fef1)] __-__ __executor__: sentencizer trimming spaces (*guiferviz*)
 - [[```2f028ecb```](https://github.com/jina-ai/jina/commit/2f028ecb39e02200d7a272fb9e55961163221d17)] __-__ trigger on master branch (*antonkurenkov*)
 - [[```fbf66f7f```](https://github.com/jina-ai/jina/commit/fbf66f7f731a8ab5490833b1e9312241ad7c1f01)] __-__ change dependencies locations (*antonkurenkov*)
 - [[```d0b78f6e```](https://github.com/jina-ai/jina/commit/d0b78f6ebb511a68c4584e078cff18c433bcff89)] __-__ change core-release action branch (*antonkurenkov*)
 - [[```28c8d6bd```](https://github.com/jina-ai/jina/commit/28c8d6bd54960eaf363deb213343e6d4402a1c68)] __-__ add core-release (*antonkurenkov*)
 - [[```45c0715e```](https://github.com/jina-ai/jina/commit/45c0715e0b402e75e5f7cb5214acd8d43f8e311d)] __-__ __executor__: extra test to show Sentencizer features (*guiferviz*)
 - [[```bd9fcb2e```](https://github.com/jina-ai/jina/commit/bd9fcb2edc73927411952e3b00cddeb211ab5f72)] __-__ add core-release action (*antonkurenkov*)

### 🍹 Other Improvements

 - [[```99c81051```](https://github.com/jina-ai/jina/commit/99c810511696cc38f0ec2ea5f1345dadda042c8b)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```5e421c09```](https://github.com/jina-ai/jina/commit/5e421c092f9c40324fd0d3348af4ec54b5925a61)] __-__ add session level fix in setup (*Han Xiao*)
 - [[```7aceae3c```](https://github.com/jina-ai/jina/commit/7aceae3c44cb16a28c203c896c562fb74bf8876e)] __-__ __executors__: replace double quotes, add type hint (*phamtrancsek12*)
 - [[```324368e9```](https://github.com/jina-ai/jina/commit/324368e92a2d9200a8051630a542bedb4f5b0338)] __-__ __executor__: improving Sentencizer by a factor of 2.5 (*guiferviz*)
 - [[```99626cb6```](https://github.com/jina-ai/jina/commit/99626cb61a749a46ecf5db8d3946c6dba2d63564)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```87ac02c6```](https://github.com/jina-ai/jina/commit/87ac02c66029cb1e21bc3063152102a1e8106380)] __-__ __version__: bumping version to 0.1.13 (*Jina Dev Bot*)
 - [[```4c6c5ac9```](https://github.com/jina-ai/jina/commit/4c6c5ac95c32ea0910aa1655c6d3db41cdd260de)] __-__ change secrets in all ci pipeline (*Han Xiao*)
 - [[```80224f78```](https://github.com/jina-ai/jina/commit/80224f78d28afa9037807f2bd8526e81b8396ecf)] __-__ add command run for issue (*Han Xiao*)
 - [[```c762ae65```](https://github.com/jina-ai/jina/commit/c762ae65e2df3be77e74bc0ad69691c2f4d983cd)] __-__ __version__: bumping version to 0.1.12 (*Jina Dev Bot*)
 - [[```15380fa6```](https://github.com/jina-ai/jina/commit/15380fa697d5e88d590fc17472330cd34c6972e7)] __-__ hotfix include extra req to manifest (*Han Xiao*)

## Release Note (`0.1.14`)

> Release time: 2020-05-23 23:20:51



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Nan Wang,  Jina Dev Bot,  antonkurenkov,  guiferviz,  phamtrancsek12,  Tracy Pham,  🙇


### 🆕 New Features

 - [[```b6a85495```](https://github.com/jina-ai/jina/commit/b6a8549598c75da710cffa19ebb23990f5560edc)] __-__ __flow__: add change gateway after flow init (*Han Xiao*)
 - [[```ed065fe8```](https://github.com/jina-ai/jina/commit/ed065fe82c342398ec79646b498d55f72551ef56)] __-__ __encoders__: fix the bigtransfer encoders doc (*Nan Wang*)
 - [[```819902c4```](https://github.com/jina-ai/jina/commit/819902c45b528c0404114b4fab9419c9c0c307fa)] __-__ __encoders__: add big_transfer encoders based on tf (*Nan Wang*)
 - [[```80f30168```](https://github.com/jina-ai/jina/commit/80f3016807eee059d87303853f49da687d4a3ad1)] __-__ __flow__: add block function pause process (*Han Xiao*)
 - [[```ee318d68```](https://github.com/jina-ai/jina/commit/ee318d685ad9986358aaa52e4700b05a753ffe36)] __-__ __crafter__: add data uri to bytes convert (*Han Xiao*)
 - [[```186e2fe9```](https://github.com/jina-ai/jina/commit/186e2fe9c26334cd3ec002c9f993a082fbeb9e51)] __-__ __proto__: add data uri as content of doc (*Han Xiao*)
 - [[```07c52dd9```](https://github.com/jina-ai/jina/commit/07c52dd9a0dc6d8b57b07af442400fd6f063a4a4)] __-__ __executors__: disable the unittest for grpc (*Nan Wang*)
 - [[```644e69fc```](https://github.com/jina-ai/jina/commit/644e69fc030e95e537f8b60a21b6d2ca2df66742)] __-__ __executors__: refactoring in response to the comments (*Nan Wang*)
 - [[```71739448```](https://github.com/jina-ai/jina/commit/71739448cbbf8ca0e46dd987bc5a4fb66c59d026)] __-__ __executors__: refactoring unit tests (*Nan Wang*)
 - [[```5c0d53cd```](https://github.com/jina-ai/jina/commit/5c0d53cdc5211b29ace7910f9238808658b8cc47)] __-__ __executors__: fix the method_name issues (*Nan Wang*)
 - [[```20563b2a```](https://github.com/jina-ai/jina/commit/20563b2a7c4c0dc6494c9e9102fb0c2dea7f7dee)] __-__ __executors__: add apis for other method_name (*Nan Wang*)
 - [[```15f9f1fb```](https://github.com/jina-ai/jina/commit/15f9f1fb7e715a5371298f74b02066e3ceb9a654)] __-__ __executors__: add typing (*Nan Wang*)
 - [[```ff89b38b```](https://github.com/jina-ai/jina/commit/ff89b38b66394203874a6b732458d6fada5e9824)] __-__ __executors__: add docs (*Nan Wang*)
 - [[```e57293f4```](https://github.com/jina-ai/jina/commit/e57293f429ffc54d005155aaae64114df59119af)] __-__ __executors__: refactoring codes (*Nan Wang*)
 - [[```625b3c70```](https://github.com/jina-ai/jina/commit/625b3c70b4a4371959b16fc5009e06a3c2e4d18b)] __-__ __executors__: add the tfserving client (*Nan Wang*)
 - [[```3470a6bd```](https://github.com/jina-ai/jina/commit/3470a6bd6e3c7f7ad9ca5b299ce31f60d25613e3)] __-__ __executors__: add executors wrapping a tfserving client (*Nan Wang*)
 - [[```48935875```](https://github.com/jina-ai/jina/commit/489358757254ef8b8ee8ade69db7f753aab723ea)] __-__ add rest api gateway (*Han Xiao*)
 - [[```e17f9405```](https://github.com/jina-ai/jina/commit/e17f9405427052dacb60d44ae169dd5708df8e21)] __-__ __executors__: add numeric crafter (*Tracy Pham*)

### 🐞 Bug fixes

 - [[```f2028fe0```](https://github.com/jina-ai/jina/commit/f2028fe00b586a39f79592ca583f23261af637d5)] __-__ __client__: auto convert str to bytes in raw mode (*Han Xiao*)
 - [[```bca2ab85```](https://github.com/jina-ai/jina/commit/bca2ab856a0fd51043aeedc8baf953164ad968dd)] __-__ __executor__: add version warning and fix typos (*Han Xiao*)
 - [[```db6442a2```](https://github.com/jina-ai/jina/commit/db6442a26358617ca09266817cf821c43eee7b07)] __-__ __gateway__: fix cors issue in the rest gateway (*Han Xiao*)
 - [[```eda4d671```](https://github.com/jina-ai/jina/commit/eda4d67175299823bc342bbb7ae41af14655d761)] __-__ __crafter__: add read from raw_bytes (*Han Xiao*)
 - [[```be58e64a```](https://github.com/jina-ai/jina/commit/be58e64a653031b207dc67257d30b40965b87393)] __-__ __gateway__: add cors to response (*Han Xiao*)
 - [[```783ef306```](https://github.com/jina-ai/jina/commit/783ef3062c39a10423a915acf244c5a50b469c84)] __-__ fix pip install info (*Han Xiao*)
 - [[```ba3e1d88```](https://github.com/jina-ai/jina/commit/ba3e1d88f5ee78c0c30e06fa2771ed4efd0ce95c)] __-__ __crafter__: add data uri crafter (*Han Xiao*)
 - [[```17f586f2```](https://github.com/jina-ai/jina/commit/17f586f2d0efcc6fb57f74212110f9fb0379915f)] __-__ __gateway__: fix #435 empty request iterator (*Han Xiao*)
 - [[```ae7ee48c```](https://github.com/jina-ai/jina/commit/ae7ee48cb16ab49a0d2e9363537f948f02bf5068)] __-__ fix ci event (*Han Xiao*)
 - [[```41790109```](https://github.com/jina-ai/jina/commit/417901098cce90b22bc8f6c65b74164d12662e22)] __-__ __executors__: change the class inheritance of array reader (*phamtrancsek12*)
 - [[```5803ee99```](https://github.com/jina-ai/jina/commit/5803ee9981e58dece6ca47003e84c3322255f93f)] __-__ __zmqlet__: fix slow joiner when request is small (*Han Xiao*)
 - [[```1361baa1```](https://github.com/jina-ai/jina/commit/1361baa1e4838e635a96087351ca4a25c3aeac19)] __-__ __executor__: fix sign of condition (*guiferviz*)
 - [[```fa07110b```](https://github.com/jina-ai/jina/commit/fa07110b06fead2bcbd1213e22896674894d24c6)] __-__ __drivers__: fix the bug in handling empty chunks (*Nan Wang*)
 - [[```5b62c315```](https://github.com/jina-ai/jina/commit/5b62c315d1615835d904584b357ac71e6e0ab4e3)] __-__ __encoders__: fix the broken transformers (*Nan Wang*)

### 🚧 Code Refactoring

 - [[```63e22c4c```](https://github.com/jina-ai/jina/commit/63e22c4c46708c205675fe80ef55130338ec7f71)] __-__ __client__: change str mode to enum (*Han Xiao*)
 - [[```aca3723b```](https://github.com/jina-ai/jina/commit/aca3723b661b1a1462a1cdfb0a78cd95fc08ae01)] __-__ __gateway__: use new data uri field (*Han Xiao*)
 - [[```4d11e113```](https://github.com/jina-ai/jina/commit/4d11e1131cdf5f388dc81c7e0febcd32c10447b1)] __-__ __executors__: rename numeric crafter (*phamtrancsek12*)

### 📗 Documentation

 - [[```8e31eaac```](https://github.com/jina-ai/jina/commit/8e31eaac22f9b72bcfb62f924f1da21e7113f572)] __-__ __pip__: add pip install master with extras (*Han Xiao*)
 - [[```d4d55618```](https://github.com/jina-ai/jina/commit/d4d556188872c52906694f9d1f195f502a9cec78)] __-__ add rest api spec (*Han Xiao*)
 - [[```6bdc7ee7```](https://github.com/jina-ai/jina/commit/6bdc7ee7d6fa4f4386b5c0a0fdc571388ab77d2f)] __-__ __executor__: improving docs (*guiferviz*)

### 🏁 Unit Test and CICD

 - [[```60b2ef15```](https://github.com/jina-ai/jina/commit/60b2ef1572c5031034bc45c30d4ec7a112ffedd8)] __-__ add test for data uri crafter (*Han Xiao*)
 - [[```8d3b5940```](https://github.com/jina-ai/jina/commit/8d3b59400a6f0b1fa45f45e8c19af875739bc539)] __-__ __docker__: fix pip in docker (*Han Xiao*)
 - [[```7bb674d0```](https://github.com/jina-ai/jina/commit/7bb674d0f9d59f562a0d4d51eea0ed1b2d3a70d3)] __-__ __docker__: move gevent from pip into apt (*Han Xiao*)
 - [[```d3420d02```](https://github.com/jina-ai/jina/commit/d3420d022d74dce847e135269a1704a2972704f6)] __-__ trigger on published release (*antonkurenkov*)
 - [[```6caca895```](https://github.com/jina-ai/jina/commit/6caca8958df97e40e8108e2ba57fd90004b9fef1)] __-__ __executor__: sentencizer trimming spaces (*guiferviz*)
 - [[```2f028ecb```](https://github.com/jina-ai/jina/commit/2f028ecb39e02200d7a272fb9e55961163221d17)] __-__ trigger on master branch (*antonkurenkov*)
 - [[```fbf66f7f```](https://github.com/jina-ai/jina/commit/fbf66f7f731a8ab5490833b1e9312241ad7c1f01)] __-__ change dependencies locations (*antonkurenkov*)
 - [[```d0b78f6e```](https://github.com/jina-ai/jina/commit/d0b78f6ebb511a68c4584e078cff18c433bcff89)] __-__ change core-release action branch (*antonkurenkov*)
 - [[```28c8d6bd```](https://github.com/jina-ai/jina/commit/28c8d6bd54960eaf363deb213343e6d4402a1c68)] __-__ add core-release (*antonkurenkov*)
 - [[```45c0715e```](https://github.com/jina-ai/jina/commit/45c0715e0b402e75e5f7cb5214acd8d43f8e311d)] __-__ __executor__: extra test to show Sentencizer features (*guiferviz*)
 - [[```bd9fcb2e```](https://github.com/jina-ai/jina/commit/bd9fcb2edc73927411952e3b00cddeb211ab5f72)] __-__ add core-release action (*antonkurenkov*)

### 🍹 Other Improvements

 - [[```97403ab2```](https://github.com/jina-ai/jina/commit/97403ab2847f8670b8c888a553a369f057563b14)] __-__ hotfix for pokedex (*Han Xiao*)
 - [[```f9257b68```](https://github.com/jina-ai/jina/commit/f9257b68cdbc6e1b5a4464099080b4b5e2cc0e94)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```7e9999f0```](https://github.com/jina-ai/jina/commit/7e9999f01b1e95ec24f614ac4983840fd23ac2cb)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```87d65d3b```](https://github.com/jina-ai/jina/commit/87d65d3b7f9831be3678ee977001614dcb1fd6fc)] __-__ __version__: bumping version to 0.1.14 (*Jina Dev Bot*)
 - [[```5e421c09```](https://github.com/jina-ai/jina/commit/5e421c092f9c40324fd0d3348af4ec54b5925a61)] __-__ add session level fix in setup (*Han Xiao*)
 - [[```7aceae3c```](https://github.com/jina-ai/jina/commit/7aceae3c44cb16a28c203c896c562fb74bf8876e)] __-__ __executors__: replace double quotes, add type hint (*phamtrancsek12*)
 - [[```324368e9```](https://github.com/jina-ai/jina/commit/324368e92a2d9200a8051630a542bedb4f5b0338)] __-__ __executor__: improving Sentencizer by a factor of 2.5 (*guiferviz*)
 - [[```87ac02c6```](https://github.com/jina-ai/jina/commit/87ac02c66029cb1e21bc3063152102a1e8106380)] __-__ __version__: bumping version to 0.1.13 (*Jina Dev Bot*)
 - [[```6733bcb2```](https://github.com/jina-ai/jina/commit/6733bcb2b07d54d9e52152cf843b23ba97410f1d)] __-__ Merge pull request #417 from JoanFM/feat-pytorch-custom-model (*Han Xiao*)
 - [[```4c6c5ac9```](https://github.com/jina-ai/jina/commit/4c6c5ac95c32ea0910aa1655c6d3db41cdd260de)] __-__ change secrets in all ci pipeline (*Han Xiao*)
 - [[```80224f78```](https://github.com/jina-ai/jina/commit/80224f78d28afa9037807f2bd8526e81b8396ecf)] __-__ add command run for issue (*Han Xiao*)
 - [[```c762ae65```](https://github.com/jina-ai/jina/commit/c762ae65e2df3be77e74bc0ad69691c2f4d983cd)] __-__ __version__: bumping version to 0.1.12 (*Jina Dev Bot*)
 - [[```15380fa6```](https://github.com/jina-ai/jina/commit/15380fa697d5e88d590fc17472330cd34c6972e7)] __-__ hotfix include extra req to manifest (*Han Xiao*)

## Release Note (`0.2.0`)

> Release time: 2020-05-28 18:02:11



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  🙇


### 🆕 New Features

 - [[```fda57905```](https://github.com/jina-ai/jina/commit/fda579051f6d58bc13db7ea67b78d1f7f95265b3)] __-__ __client__: auto detect input_type (*Han Xiao*)
 - [[```6702c61c```](https://github.com/jina-ai/jina/commit/6702c61c99e999a8ab5fb733c720304a5dc6d3ad)] __-__ __crafter__: add Any2Buffer convert (*Han Xiao*)
 - [[```9dfe9188```](https://github.com/jina-ai/jina/commit/9dfe9188d8df75cf3fa1220e86d064be1cbd21df)] __-__ __crafter__: add buffer, data_uri, file_path convert (*Han Xiao*)
 - [[```c2d3e819```](https://github.com/jina-ai/jina/commit/c2d3e8199ff38e85754b45d2fca96b28d72a5f8a)] __-__ __proto__: add mime_type to proto (*Han Xiao*)

### 🐞 Bug fixes

 - [[```efd63716```](https://github.com/jina-ai/jina/commit/efd63716e4575477434a70827ba88b2a2d725b0c)] __-__ __drivers__: mime driver now inherit from basedriver (*Han Xiao*)
 - [[```76bd4e63```](https://github.com/jina-ai/jina/commit/76bd4e6341ffcf61481a7f3bc2b465bca36af87b)] __-__ __client__: fix check input function (*Han Xiao*)
 - [[```82c7c52c```](https://github.com/jina-ai/jina/commit/82c7c52c05515db400e4b2f810646195ce89ae9b)] __-__ __client__: raise exception on bad input (*Han Xiao*)
 - [[```963ea7fb```](https://github.com/jina-ai/jina/commit/963ea7fbcd4b51e6dc0b596feaad2e82e0294cfd)] __-__ __client__: fix mime_type warning (*Han Xiao*)
 - [[```b7e472e2```](https://github.com/jina-ai/jina/commit/b7e472e22eb2a35e850da000d62b9492e3c0dac0)] __-__ __crafter__: fix content read when doc is pb already (*Han Xiao*)
 - [[```276e1420```](https://github.com/jina-ai/jina/commit/276e1420bfddbb2f881a7a18659a5d716b3deff9)] __-__ fix typo in tests (*Han Xiao*)

### 🚧 Code Refactoring

 - [[```80adf9c9```](https://github.com/jina-ai/jina/commit/80adf9c98d3075dac9eacbd48a3b03349274c50a)] __-__ __helloworld__: use data uri instead of metainfo (*Han Xiao*)
 - [[```f14c146a```](https://github.com/jina-ai/jina/commit/f14c146a3ebae7b5f420cc430e76753ac993208a)] __-__ __client__: remove client input type (*Han Xiao*)
 - [[```a39371f7```](https://github.com/jina-ai/jina/commit/a39371f750a5172dd9a8a3fbb5eb3bf2c941a7b7)] __-__ __crafter__: move mime type detect to driver (*Han Xiao*)

### 📗 Documentation

 - [[```774e4757```](https://github.com/jina-ai/jina/commit/774e4757522c57eea96eff0e4e13d4bcf59f5ece)] __-__ add google bit model tutorial (*Han Xiao*)

### 🍹 Other Improvements

 - [[```b72ad858```](https://github.com/jina-ai/jina/commit/b72ad858744a0314facbaed27491befdb8dcd3c2)] __-__ hotfix release 0.2.0 (*Han Xiao*)
 - [[```1fdaabbf```](https://github.com/jina-ai/jina/commit/1fdaabbfd9aec7029f22f6cc6e8814f2c79d9ec9)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```25d5797f```](https://github.com/jina-ai/jina/commit/25d5797fa995bee3966686bcd34434d0a87cc342)] __-__ release 0.2.0 (*Han Xiao*)
 - [[```dcb387db```](https://github.com/jina-ai/jina/commit/dcb387db99f5ab5fbf783600aadaa2eed87ad763)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```ff63c7fc```](https://github.com/jina-ai/jina/commit/ff63c7fc18019332207540f397daf5b950dc106d)] __-__ __version__: bumping version to 0.1.15 (*Jina Dev Bot*)

## Release Note (`0.2.1`)

> Release time: 2020-05-29 15:57:53



🙇 We'd like to thank all contributors for this new release! In particular,
 Jina Dev Bot,  🙇


### 🍹 Other Improvements

 - [[```e6ba1682```](https://github.com/jina-ai/jina/commit/e6ba1682a69a2d40c9198f5789e7866f282f37bb)] __-__ __version__: bumping version to 0.2.1 (*Jina Dev Bot*)

## Release Note (`0.2.2`)

> Release time: 2020-06-05 15:57:30



🙇 We'd like to thank all contributors for this new release! In particular,
 Evan Chan,  Han Xiao,  Jina Dev Bot,  redram,  fhaase2,  joaopalotti@gmail.com,  Nan Wang,  YueLiu-jina,  Frederic Haase,  🙇


### 🆕 New Features

 - [[```699ac0aa```](https://github.com/jina-ai/jina/commit/699ac0aa895bd7fe9b922c8cc8e76a473c656d89)] __-__ __gateway__: add convert driver to the gateway (*Han Xiao*)
 - [[```a16277ef```](https://github.com/jina-ai/jina/commit/a16277efbf96362503e9c77a8beab65666103722)] __-__ __flow__: ingest by lines (*Han Xiao*)
 - [[```d0705377```](https://github.com/jina-ai/jina/commit/d07053774dd9b010bc7542f6dcd20b2ed5e2f957)] __-__ __encoders__: add spectral audio encoders (*redram*)
 - [[```5475eef0```](https://github.com/jina-ai/jina/commit/5475eef0d8db0458afa64464f78a5b801e8b7d72)] __-__ __logging__: use gevent as logging server (*fhaase2*)
 - [[```2fa5f458```](https://github.com/jina-ai/jina/commit/2fa5f4587135286a24af193ea7091a4e4ed07cc1)] __-__ __crafters__: update SlidingWindowSegmenter for nlp (*fhaase2*)
 - [[```401faab7```](https://github.com/jina-ai/jina/commit/401faab7f7f9465264aa20352a237615e9864a34)] __-__ __driver__: add override as an option to the driver (*Han Xiao*)
 - [[```f1acce32```](https://github.com/jina-ai/jina/commit/f1acce32f78a0b918edeb65853fa338374272201)] __-__ add more tests (*Nan Wang*)
 - [[```462d28b6```](https://github.com/jina-ai/jina/commit/462d28b610fea6e561ab585660ac3d059f718499)] __-__ fix the index and score drivers (*Nan Wang*)
 - [[```c380214c```](https://github.com/jina-ai/jina/commit/c380214c5c45d976b37dd2927a9b64d1854d87da)] __-__ __crafters__: fix docstring for SlidingWindowSegmenter (*fhaase2*)
 - [[```c6ef697b```](https://github.com/jina-ai/jina/commit/c6ef697b5b21805b328228eded0a41d5011dff08)] __-__ __crafters__: add SlidingWindowSegmenter for nlp (*Frederic Haase*)
 - [[```5ecb5d14```](https://github.com/jina-ai/jina/commit/5ecb5d147122a847ae471d9600773f9ce99bdabb)] __-__ __crafter__: make uri written lazy (*Han Xiao*)
 - [[```4af675f9```](https://github.com/jina-ai/jina/commit/4af675f92e6b4b67b62a980512262cf6f6cc39cc)] __-__ update protobuf files (*Nan Wang*)
 - [[```528d644f```](https://github.com/jina-ai/jina/commit/528d644faf8ee489f0b7bc1825024025ece68753)] __-__ update the protobuf files (*Nan Wang*)
 - [[```ec54bb95```](https://github.com/jina-ai/jina/commit/ec54bb95d8cfa496437a581f3b52c76d825c70c4)] __-__ add a draft for the unittests (*Nan Wang*)
 - [[```7b919360```](https://github.com/jina-ai/jina/commit/7b919360034d2d713abfbcb3c3faab6be1b4fea9)] __-__ add support forthe multi-field search (*Nan Wang*)
 - [[```7146c66d```](https://github.com/jina-ai/jina/commit/7146c66de8e9477f9d819b31dd9d73a0a3b14553)] __-__ clean up (*Nan Wang*)
 - [[```a88c9719```](https://github.com/jina-ai/jina/commit/a88c9719eac68beba3be854ea4b2191366c2da0f)] __-__ update the abstract (*Nan Wang*)
 - [[```b932c744```](https://github.com/jina-ai/jina/commit/b932c744d66c5299981609bfedcc9120262ed5ac)] __-__ update the flow diagram (*Nan Wang*)
 - [[```c48cd974```](https://github.com/jina-ai/jina/commit/c48cd974fc4a464a45c750198efd5b6988cd1a08)] __-__ add an example for the Specification (*Nan Wang*)
 - [[```ece5e21a```](https://github.com/jina-ai/jina/commit/ece5e21a7154355dd305a004c538c42bacfa1b4c)] __-__ refactor the design (*Nan Wang*)
 - [[```f092fe95```](https://github.com/jina-ai/jina/commit/f092fe953924a2fd4d285683c0f543703b37bb73)] __-__ refactoring the overall design (*Nan Wang*)
 - [[```1875eaff```](https://github.com/jina-ai/jina/commit/1875eaffbdb01e88c319c5d965520ab2af071adf)] __-__ __client__: add input function sugar (*Han Xiao*)
 - [[```15cbac1d```](https://github.com/jina-ai/jina/commit/15cbac1dcfcf063e7d088e6750ffe27ddf6ee993)] __-__ __crafters__: add audio crafters (*redram*)
 - [[```5302c162```](https://github.com/jina-ai/jina/commit/5302c162431127690e2bfc03035a3991e00efb7e)] __-__ fix typos (*Nan Wang*)
 - [[```11e9e059```](https://github.com/jina-ai/jina/commit/11e9e059fed854042ba9f09023258bd77fc2f6db)] __-__ add the 1st draft for JEP-3 (*Nan Wang*)
 - [[```9dfe9188```](https://github.com/jina-ai/jina/commit/9dfe9188d8df75cf3fa1220e86d064be1cbd21df)] __-__ __crafter__: add buffer, data_uri, file_path convert (*Han Xiao*)
 - [[```c2d3e819```](https://github.com/jina-ai/jina/commit/c2d3e8199ff38e85754b45d2fca96b28d72a5f8a)] __-__ __proto__: add mime_type to proto (*Han Xiao*)

### 🐞 Bug fixes

 - [[```aea4a5b7```](https://github.com/jina-ai/jina/commit/aea4a5b7541daf48e01536717b5fccc179bb8628)] __-__ __gateway__: add message field to gateway (*Han Xiao*)
 - [[```2e7a4043```](https://github.com/jina-ai/jina/commit/2e7a40438991abd890c0f40ed679bcb0c21e760f)] __-__ __encoder__: fix embeds returns (*Han Xiao*)
 - [[```59c6175b```](https://github.com/jina-ai/jina/commit/59c6175b543b7f47c84f5c2ed3bfac14548dad67)] __-__ __encoder__: remove np array convert (*Han Xiao*)
 - [[```39a97c73```](https://github.com/jina-ai/jina/commit/39a97c73ebf6a9e643dc8eea221286181480d75e)] __-__ pb indexer flush (*Han Xiao*)
 - [[```c48b56fd```](https://github.com/jina-ai/jina/commit/c48b56fdd4e8e3ff280369bcce76df80023aad24)] __-__ __docs__: suggestions for the flow docs (*joaopalotti@gmail.com*)
 - [[```aaa3a10f```](https://github.com/jina-ai/jina/commit/aaa3a10f181cb35e65ebe21caf7db6961934fa65)] __-__ rename default yaml for pbindex (*Han Xiao*)
 - [[```4b3753af```](https://github.com/jina-ai/jina/commit/4b3753af08e30ba9ccadd53f2fcd3f191f268f49)] __-__ __docs__: fixed minor typos in jina&#39;s 101 page (*joaopalotti@gmail.com*)
 - [[```aee8ee91```](https://github.com/jina-ai/jina/commit/aee8ee91aff81b21c1169174cd51ecef82bd179f)] __-__ fix the unittest (*Nan Wang*)
 - [[```3f395b80```](https://github.com/jina-ai/jina/commit/3f395b80fdaa40f9002dcaf6976d1ba4cbf176a9)] __-__ fix the broken proto (*Nan Wang*)
 - [[```93a91b57```](https://github.com/jina-ai/jina/commit/93a91b578acd249095e95940d51ff46175143295)] __-__ __flow__: update docstring in flow (*YueLiu-jina*)
 - [[```5f68014f```](https://github.com/jina-ai/jina/commit/5f68014fb082cfa1d7672ce48768cbbf1ec2b5db)] __-__ clean up the codes (*Nan Wang*)
 - [[```04b07080```](https://github.com/jina-ai/jina/commit/04b070802c9ebcfd539fec3382dafa36591f1b6a)] __-__ improve the docs on updating protobuf (*Nan Wang*)
 - [[```5a57f166```](https://github.com/jina-ai/jina/commit/5a57f16666c705247fdb7e8f08f268a20b0aefc0)] __-__ fix unittests (*Nan Wang*)
 - [[```0c18fdb0```](https://github.com/jina-ai/jina/commit/0c18fdb09cb12c737e8a18fa7c710ebb7b2b18d4)] __-__ fix the unittests (*Nan Wang*)
 - [[```73d17bac```](https://github.com/jina-ai/jina/commit/73d17bac19956d517a1443b0169507244f439ba3)] __-__ fix the client cli parser (*Nan Wang*)
 - [[```aa8d5183```](https://github.com/jina-ai/jina/commit/aa8d51839f0a79366e99c3301cc34eadada9c775)] __-__ __crafter__: fix args of the crafter (*Han Xiao*)
 - [[```8c04c14d```](https://github.com/jina-ai/jina/commit/8c04c14d2960196e1a7e0ee78a72ef4a77c210e5)] __-__ __cli__: update CLI autocomplete (*Han Xiao*)
 - [[```63a58484```](https://github.com/jina-ai/jina/commit/63a584846594b15cebec93fe5f584e0c0939f805)] __-__ __crafter__: fix type hinting for numeric crafter (*redram*)
 - [[```3b83bad1```](https://github.com/jina-ai/jina/commit/3b83bad1fd3b6378073e06947b3a56df2955d66c)] __-__ __crafter__: fix length in chunks of jieba crafter (*redram*)
 - [[```963ea7fb```](https://github.com/jina-ai/jina/commit/963ea7fbcd4b51e6dc0b596feaad2e82e0294cfd)] __-__ __client__: fix mime_type warning (*Han Xiao*)
 - [[```b7e472e2```](https://github.com/jina-ai/jina/commit/b7e472e22eb2a35e850da000d62b9492e3c0dac0)] __-__ __crafter__: fix content read when doc is pb already (*Han Xiao*)
 - [[```276e1420```](https://github.com/jina-ai/jina/commit/276e1420bfddbb2f881a7a18659a5d716b3deff9)] __-__ fix typo in tests (*Han Xiao*)

### 🚧 Code Refactoring

 - [[```e28a5ba5```](https://github.com/jina-ai/jina/commit/e28a5ba556e3daf701cde510da1fc5bd2bb62867)] __-__ __driver__: move convert crafter to driver (*Han Xiao*)
 - [[```66dfe75d```](https://github.com/jina-ai/jina/commit/66dfe75dc9a07bc687202da7ffcdffc279ae5115)] __-__ __proto__: add doc-level uri out of oneof content (*Han Xiao*)
 - [[```9de7dfd5```](https://github.com/jina-ai/jina/commit/9de7dfd5613b6f304d3f707d2fc2c76338b10e7c)] __-__ make BaseRanker abstract (*Han Xiao*)
 - [[```36efe799```](https://github.com/jina-ai/jina/commit/36efe79965af82bdcb72709c70d7490a8b5eba24)] __-__ __crafter__: remove unnecessary set (*Han Xiao*)
 - [[```46d786c6```](https://github.com/jina-ai/jina/commit/46d786c6b30573002ebb04e11c08b9358995fbf3)] __-__ fix formats in JEP-3 (*Nan Wang*)
 - [[```0d69a09f```](https://github.com/jina-ai/jina/commit/0d69a09f84124ec7cfa2fd0a0610d3c3ba520147)] __-__ merge with master (*Han Xiao*)
 - [[```a39371f7```](https://github.com/jina-ai/jina/commit/a39371f750a5172dd9a8a3fbb5eb3bf2c941a7b7)] __-__ __crafter__: move mime type detect to driver (*Han Xiao*)

### 📗 Documentation

 - [[```7a719bc3```](https://github.com/jina-ai/jina/commit/7a719bc334e55868456f220a9d2642e27afd7336)] __-__ __readme__: fix link (*Evan Chan*)
 - [[```8e9bff43```](https://github.com/jina-ai/jina/commit/8e9bff43d6329679e7e2cfe6f3767f0ef791e284)] __-__ remove whitespace and fix typo  chapter io (*Frederic Haase*)
 - [[```08ff87dd```](https://github.com/jina-ai/jina/commit/08ff87dda239177fb7396a0511cde7411763a5ed)] __-__ added support to the Portuguese language for 101 (*joaopalotti@gmail.com*)
 - [[```774e4757```](https://github.com/jina-ai/jina/commit/774e4757522c57eea96eff0e4e13d4bcf59f5ece)] __-__ add google bit model tutorial (*Han Xiao*)

### 🏁 Unit Test and CICD

 - [[```8dae4456```](https://github.com/jina-ai/jina/commit/8dae445609de447234f0ec891a7571813d97a623)] __-__ add a test for numpy indexing (*Han Xiao*)
 - [[```79e5f203```](https://github.com/jina-ai/jina/commit/79e5f20328738d5c0ed960c21f79838e0a43cefe)] __-__ add test for unarydriver (*Han Xiao*)

### 🍹 Other Improvements

 - [[```bd914b82```](https://github.com/jina-ai/jina/commit/bd914b827b0f4ba3b4ac91dc214f3fcea7098e41)] __-__ Revert &#34;feat: add the support for multi-field search&#34; (*Han Xiao*)
 - [[```d7ad9fde```](https://github.com/jina-ai/jina/commit/d7ad9fde97f02db79233ba93400e0bda74597580)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```788be928```](https://github.com/jina-ai/jina/commit/788be928b68bb8e0ad1d5d1061997c8a09eb0df5)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```a704586a```](https://github.com/jina-ai/jina/commit/a704586a48adc32c2146b73dfe92b10565b7f1dd)] __-__ __version__: bumping version to 0.2.2 (*Jina Dev Bot*)
 - [[```b72ad858```](https://github.com/jina-ai/jina/commit/b72ad858744a0314facbaed27491befdb8dcd3c2)] __-__ hotfix release 0.2.0 (*Han Xiao*)
 - [[```25d5797f```](https://github.com/jina-ai/jina/commit/25d5797fa995bee3966686bcd34434d0a87cc342)] __-__ release 0.2.0 (*Han Xiao*)
 - [[```ff63c7fc```](https://github.com/jina-ai/jina/commit/ff63c7fc18019332207540f397daf5b950dc106d)] __-__ __version__: bumping version to 0.1.15 (*Jina Dev Bot*)
 - [[```97403ab2```](https://github.com/jina-ai/jina/commit/97403ab2847f8670b8c888a553a369f057563b14)] __-__ hotfix for pokedex (*Han Xiao*)

## Release Note (`0.2.3`)

> Release time: 2020-06-07 17:27:26



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  joaopalotti@gmail.com,  redram,  fhaase2,  YueLiu-jina,  Frederic Haase,  Nan Wang,  🙇


### 🆕 New Features

 - [[```0c70bec9```](https://github.com/jina-ai/jina/commit/0c70bec998c6e1c10f90127b949c855440603174)] __-__ __helloworld__: add option to change logserver (*joaopalotti@gmail.com*)
 - [[```5a54bb86```](https://github.com/jina-ai/jina/commit/5a54bb8674bbed45156fa08b3c11d255a0202b93)] __-__ multi-field search (*Han Xiao*)
 - [[```699ac0aa```](https://github.com/jina-ai/jina/commit/699ac0aa895bd7fe9b922c8cc8e76a473c656d89)] __-__ __gateway__: add convert driver to the gateway (*Han Xiao*)
 - [[```a16277ef```](https://github.com/jina-ai/jina/commit/a16277efbf96362503e9c77a8beab65666103722)] __-__ __flow__: ingest by lines (*Han Xiao*)
 - [[```d0705377```](https://github.com/jina-ai/jina/commit/d07053774dd9b010bc7542f6dcd20b2ed5e2f957)] __-__ __encoders__: add spectral audio encoders (*redram*)
 - [[```5475eef0```](https://github.com/jina-ai/jina/commit/5475eef0d8db0458afa64464f78a5b801e8b7d72)] __-__ __logging__: use gevent as logging server (*fhaase2*)
 - [[```2fa5f458```](https://github.com/jina-ai/jina/commit/2fa5f4587135286a24af193ea7091a4e4ed07cc1)] __-__ __crafters__: update SlidingWindowSegmenter for nlp (*fhaase2*)
 - [[```401faab7```](https://github.com/jina-ai/jina/commit/401faab7f7f9465264aa20352a237615e9864a34)] __-__ __driver__: add override as an option to the driver (*Han Xiao*)
 - [[```c380214c```](https://github.com/jina-ai/jina/commit/c380214c5c45d976b37dd2927a9b64d1854d87da)] __-__ __crafters__: fix docstring for SlidingWindowSegmenter (*fhaase2*)
 - [[```c6ef697b```](https://github.com/jina-ai/jina/commit/c6ef697b5b21805b328228eded0a41d5011dff08)] __-__ __crafters__: add SlidingWindowSegmenter for nlp (*Frederic Haase*)
 - [[```5ecb5d14```](https://github.com/jina-ai/jina/commit/5ecb5d147122a847ae471d9600773f9ce99bdabb)] __-__ __crafter__: make uri written lazy (*Han Xiao*)
 - [[```7146c66d```](https://github.com/jina-ai/jina/commit/7146c66de8e9477f9d819b31dd9d73a0a3b14553)] __-__ clean up (*Nan Wang*)
 - [[```a88c9719```](https://github.com/jina-ai/jina/commit/a88c9719eac68beba3be854ea4b2191366c2da0f)] __-__ update the abstract (*Nan Wang*)
 - [[```b932c744```](https://github.com/jina-ai/jina/commit/b932c744d66c5299981609bfedcc9120262ed5ac)] __-__ update the flow diagram (*Nan Wang*)
 - [[```c48cd974```](https://github.com/jina-ai/jina/commit/c48cd974fc4a464a45c750198efd5b6988cd1a08)] __-__ add an example for the Specification (*Nan Wang*)
 - [[```ece5e21a```](https://github.com/jina-ai/jina/commit/ece5e21a7154355dd305a004c538c42bacfa1b4c)] __-__ refactor the design (*Nan Wang*)
 - [[```f092fe95```](https://github.com/jina-ai/jina/commit/f092fe953924a2fd4d285683c0f543703b37bb73)] __-__ refactoring the overall design (*Nan Wang*)
 - [[```1875eaff```](https://github.com/jina-ai/jina/commit/1875eaffbdb01e88c319c5d965520ab2af071adf)] __-__ __client__: add input function sugar (*Han Xiao*)
 - [[```15cbac1d```](https://github.com/jina-ai/jina/commit/15cbac1dcfcf063e7d088e6750ffe27ddf6ee993)] __-__ __crafters__: add audio crafters (*redram*)
 - [[```5302c162```](https://github.com/jina-ai/jina/commit/5302c162431127690e2bfc03035a3991e00efb7e)] __-__ fix typos (*Nan Wang*)
 - [[```11e9e059```](https://github.com/jina-ai/jina/commit/11e9e059fed854042ba9f09023258bd77fc2f6db)] __-__ add the 1st draft for JEP-3 (*Nan Wang*)
 - [[```9dfe9188```](https://github.com/jina-ai/jina/commit/9dfe9188d8df75cf3fa1220e86d064be1cbd21df)] __-__ __crafter__: add buffer, data_uri, file_path convert (*Han Xiao*)
 - [[```c2d3e819```](https://github.com/jina-ai/jina/commit/c2d3e8199ff38e85754b45d2fca96b28d72a5f8a)] __-__ __proto__: add mime_type to proto (*Han Xiao*)

### 🐞 Bug fixes

 - [[```76059773```](https://github.com/jina-ai/jina/commit/760597737557bce10b3df4804fcc6870c71a1f28)] __-__ logic on set reducing-yaml-path (*Han Xiao*)
 - [[```a660a5ba```](https://github.com/jina-ai/jina/commit/a660a5bafd1ed23d6d3f549602ae2e003016268c)] __-__ hide num_part and set default to 0 (*Han Xiao*)
 - [[```2e7a4043```](https://github.com/jina-ai/jina/commit/2e7a40438991abd890c0f40ed679bcb0c21e760f)] __-__ __encoder__: fix embeds returns (*Han Xiao*)
 - [[```59c6175b```](https://github.com/jina-ai/jina/commit/59c6175b543b7f47c84f5c2ed3bfac14548dad67)] __-__ __encoder__: remove np array convert (*Han Xiao*)
 - [[```39a97c73```](https://github.com/jina-ai/jina/commit/39a97c73ebf6a9e643dc8eea221286181480d75e)] __-__ pb indexer flush (*Han Xiao*)
 - [[```c48b56fd```](https://github.com/jina-ai/jina/commit/c48b56fdd4e8e3ff280369bcce76df80023aad24)] __-__ __docs__: suggestions for the flow docs (*joaopalotti@gmail.com*)
 - [[```aaa3a10f```](https://github.com/jina-ai/jina/commit/aaa3a10f181cb35e65ebe21caf7db6961934fa65)] __-__ rename default yaml for pbindex (*Han Xiao*)
 - [[```4b3753af```](https://github.com/jina-ai/jina/commit/4b3753af08e30ba9ccadd53f2fcd3f191f268f49)] __-__ __docs__: fixed minor typos in jina&#39;s 101 page (*joaopalotti@gmail.com*)
 - [[```93a91b57```](https://github.com/jina-ai/jina/commit/93a91b578acd249095e95940d51ff46175143295)] __-__ __flow__: update docstring in flow (*YueLiu-jina*)
 - [[```aa8d5183```](https://github.com/jina-ai/jina/commit/aa8d51839f0a79366e99c3301cc34eadada9c775)] __-__ __crafter__: fix args of the crafter (*Han Xiao*)
 - [[```8c04c14d```](https://github.com/jina-ai/jina/commit/8c04c14d2960196e1a7e0ee78a72ef4a77c210e5)] __-__ __cli__: update CLI autocomplete (*Han Xiao*)
 - [[```63a58484```](https://github.com/jina-ai/jina/commit/63a584846594b15cebec93fe5f584e0c0939f805)] __-__ __crafter__: fix type hinting for numeric crafter (*redram*)
 - [[```3b83bad1```](https://github.com/jina-ai/jina/commit/3b83bad1fd3b6378073e06947b3a56df2955d66c)] __-__ __crafter__: fix length in chunks of jieba crafter (*redram*)
 - [[```963ea7fb```](https://github.com/jina-ai/jina/commit/963ea7fbcd4b51e6dc0b596feaad2e82e0294cfd)] __-__ __client__: fix mime_type warning (*Han Xiao*)
 - [[```b7e472e2```](https://github.com/jina-ai/jina/commit/b7e472e22eb2a35e850da000d62b9492e3c0dac0)] __-__ __crafter__: fix content read when doc is pb already (*Han Xiao*)
 - [[```276e1420```](https://github.com/jina-ai/jina/commit/276e1420bfddbb2f881a7a18659a5d716b3deff9)] __-__ fix typo in tests (*Han Xiao*)

### 🚧 Code Refactoring

 - [[```d045ca07```](https://github.com/jina-ai/jina/commit/d045ca07c9f33a7f37483d6e59c1d850e95c6c85)] __-__ move num_part from args to proto (*Han Xiao*)
 - [[```e28a5ba5```](https://github.com/jina-ai/jina/commit/e28a5ba556e3daf701cde510da1fc5bd2bb62867)] __-__ __driver__: move convert crafter to driver (*Han Xiao*)
 - [[```66dfe75d```](https://github.com/jina-ai/jina/commit/66dfe75dc9a07bc687202da7ffcdffc279ae5115)] __-__ __proto__: add doc-level uri out of oneof content (*Han Xiao*)
 - [[```9de7dfd5```](https://github.com/jina-ai/jina/commit/9de7dfd5613b6f304d3f707d2fc2c76338b10e7c)] __-__ make BaseRanker abstract (*Han Xiao*)
 - [[```36efe799```](https://github.com/jina-ai/jina/commit/36efe79965af82bdcb72709c70d7490a8b5eba24)] __-__ __crafter__: remove unnecessary set (*Han Xiao*)
 - [[```0d69a09f```](https://github.com/jina-ai/jina/commit/0d69a09f84124ec7cfa2fd0a0610d3c3ba520147)] __-__ merge with master (*Han Xiao*)
 - [[```a39371f7```](https://github.com/jina-ai/jina/commit/a39371f750a5172dd9a8a3fbb5eb3bf2c941a7b7)] __-__ __crafter__: move mime type detect to driver (*Han Xiao*)

### 📗 Documentation

 - [[```8e9bff43```](https://github.com/jina-ai/jina/commit/8e9bff43d6329679e7e2cfe6f3767f0ef791e284)] __-__ remove whitespace and fix typo  chapter io (*Frederic Haase*)
 - [[```08ff87dd```](https://github.com/jina-ai/jina/commit/08ff87dda239177fb7396a0511cde7411763a5ed)] __-__ added support to the Portuguese language for 101 (*joaopalotti@gmail.com*)
 - [[```774e4757```](https://github.com/jina-ai/jina/commit/774e4757522c57eea96eff0e4e13d4bcf59f5ece)] __-__ add google bit model tutorial (*Han Xiao*)

### 🏁 Unit Test and CICD

 - [[```8dae4456```](https://github.com/jina-ai/jina/commit/8dae445609de447234f0ec891a7571813d97a623)] __-__ add a test for numpy indexing (*Han Xiao*)
 - [[```79e5f203```](https://github.com/jina-ai/jina/commit/79e5f20328738d5c0ed960c21f79838e0a43cefe)] __-__ add test for unarydriver (*Han Xiao*)

### 🍹 Other Improvements

 - [[```8fc81fef```](https://github.com/jina-ai/jina/commit/8fc81fef46cfa5cd79c9403dbed28f9f60b88822)] __-__ hotfix new num_part algo (*Han Xiao*)
 - [[```8f73cba3```](https://github.com/jina-ai/jina/commit/8f73cba3c627143ea973fb3d28b9d04b640821b2)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```8d428d19```](https://github.com/jina-ai/jina/commit/8d428d19b10e0fd07e136086b3ea7ceae45194bd)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```a2ccb20c```](https://github.com/jina-ai/jina/commit/a2ccb20cbb1ef6084050b162b8b986c055b5e48c)] __-__ __version__: bumping version to 0.2.3 (*Jina Dev Bot*)
 - [[```a704586a```](https://github.com/jina-ai/jina/commit/a704586a48adc32c2146b73dfe92b10565b7f1dd)] __-__ __version__: bumping version to 0.2.2 (*Jina Dev Bot*)
 - [[```e6ba1682```](https://github.com/jina-ai/jina/commit/e6ba1682a69a2d40c9198f5789e7866f282f37bb)] __-__ __version__: bumping version to 0.2.1 (*Jina Dev Bot*)
 - [[```b72ad858```](https://github.com/jina-ai/jina/commit/b72ad858744a0314facbaed27491befdb8dcd3c2)] __-__ hotfix release 0.2.0 (*Han Xiao*)
 - [[```25d5797f```](https://github.com/jina-ai/jina/commit/25d5797fa995bee3966686bcd34434d0a87cc342)] __-__ release 0.2.0 (*Han Xiao*)
 - [[```ff63c7fc```](https://github.com/jina-ai/jina/commit/ff63c7fc18019332207540f397daf5b950dc106d)] __-__ __version__: bumping version to 0.1.15 (*Jina Dev Bot*)
 - [[```97403ab2```](https://github.com/jina-ai/jina/commit/97403ab2847f8670b8c888a553a369f057563b14)] __-__ hotfix for pokedex (*Han Xiao*)

## Release Note (`0.2.4`)

> Release time: 2020-06-10 18:52:20



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  YueLiu-jina,  Jina Dev Bot,  boussoffara,  fhaase2,  joaopalotti@gmail.com,  redram,  Frederic Haase,  Nan Wang,  🙇


### 🆕 New Features

 - [[```0c70bec9```](https://github.com/jina-ai/jina/commit/0c70bec998c6e1c10f90127b949c855440603174)] __-__ __helloworld__: add option to change logserver (*joaopalotti@gmail.com*)
 - [[```5a54bb86```](https://github.com/jina-ai/jina/commit/5a54bb8674bbed45156fa08b3c11d255a0202b93)] __-__ multi-field search (*Han Xiao*)
 - [[```699ac0aa```](https://github.com/jina-ai/jina/commit/699ac0aa895bd7fe9b922c8cc8e76a473c656d89)] __-__ __gateway__: add convert driver to the gateway (*Han Xiao*)
 - [[```a16277ef```](https://github.com/jina-ai/jina/commit/a16277efbf96362503e9c77a8beab65666103722)] __-__ __flow__: ingest by lines (*Han Xiao*)
 - [[```d0705377```](https://github.com/jina-ai/jina/commit/d07053774dd9b010bc7542f6dcd20b2ed5e2f957)] __-__ __encoders__: add spectral audio encoders (*redram*)
 - [[```5475eef0```](https://github.com/jina-ai/jina/commit/5475eef0d8db0458afa64464f78a5b801e8b7d72)] __-__ __logging__: use gevent as logging server (*fhaase2*)
 - [[```2fa5f458```](https://github.com/jina-ai/jina/commit/2fa5f4587135286a24af193ea7091a4e4ed07cc1)] __-__ __crafters__: update SlidingWindowSegmenter for nlp (*fhaase2*)
 - [[```401faab7```](https://github.com/jina-ai/jina/commit/401faab7f7f9465264aa20352a237615e9864a34)] __-__ __driver__: add override as an option to the driver (*Han Xiao*)
 - [[```c380214c```](https://github.com/jina-ai/jina/commit/c380214c5c45d976b37dd2927a9b64d1854d87da)] __-__ __crafters__: fix docstring for SlidingWindowSegmenter (*fhaase2*)
 - [[```c6ef697b```](https://github.com/jina-ai/jina/commit/c6ef697b5b21805b328228eded0a41d5011dff08)] __-__ __crafters__: add SlidingWindowSegmenter for nlp (*Frederic Haase*)
 - [[```5ecb5d14```](https://github.com/jina-ai/jina/commit/5ecb5d147122a847ae471d9600773f9ce99bdabb)] __-__ __crafter__: make uri written lazy (*Han Xiao*)
 - [[```7146c66d```](https://github.com/jina-ai/jina/commit/7146c66de8e9477f9d819b31dd9d73a0a3b14553)] __-__ clean up (*Nan Wang*)
 - [[```a88c9719```](https://github.com/jina-ai/jina/commit/a88c9719eac68beba3be854ea4b2191366c2da0f)] __-__ update the abstract (*Nan Wang*)
 - [[```b932c744```](https://github.com/jina-ai/jina/commit/b932c744d66c5299981609bfedcc9120262ed5ac)] __-__ update the flow diagram (*Nan Wang*)
 - [[```c48cd974```](https://github.com/jina-ai/jina/commit/c48cd974fc4a464a45c750198efd5b6988cd1a08)] __-__ add an example for the Specification (*Nan Wang*)
 - [[```ece5e21a```](https://github.com/jina-ai/jina/commit/ece5e21a7154355dd305a004c538c42bacfa1b4c)] __-__ refactor the design (*Nan Wang*)
 - [[```f092fe95```](https://github.com/jina-ai/jina/commit/f092fe953924a2fd4d285683c0f543703b37bb73)] __-__ refactoring the overall design (*Nan Wang*)
 - [[```1875eaff```](https://github.com/jina-ai/jina/commit/1875eaffbdb01e88c319c5d965520ab2af071adf)] __-__ __client__: add input function sugar (*Han Xiao*)
 - [[```15cbac1d```](https://github.com/jina-ai/jina/commit/15cbac1dcfcf063e7d088e6750ffe27ddf6ee993)] __-__ __crafters__: add audio crafters (*redram*)
 - [[```5302c162```](https://github.com/jina-ai/jina/commit/5302c162431127690e2bfc03035a3991e00efb7e)] __-__ fix typos (*Nan Wang*)
 - [[```11e9e059```](https://github.com/jina-ai/jina/commit/11e9e059fed854042ba9f09023258bd77fc2f6db)] __-__ add the 1st draft for JEP-3 (*Nan Wang*)
 - [[```9dfe9188```](https://github.com/jina-ai/jina/commit/9dfe9188d8df75cf3fa1220e86d064be1cbd21df)] __-__ __crafter__: add buffer, data_uri, file_path convert (*Han Xiao*)
 - [[```c2d3e819```](https://github.com/jina-ai/jina/commit/c2d3e8199ff38e85754b45d2fca96b28d72a5f8a)] __-__ __proto__: add mime_type to proto (*Han Xiao*)

### 🐞 Bug fixes

 - [[```660bd8be```](https://github.com/jina-ai/jina/commit/660bd8be715adec4b082191291d727a8b8f06ad5)] __-__ __crafter__: image reader (*Han Xiao*)
 - [[```ecf1321f```](https://github.com/jina-ai/jina/commit/ecf1321f1bd48f3d13486becc7c76f89486e09cd)] __-__ __clients__: update docstring in clients (*YueLiu-jina*)
 - [[```76059773```](https://github.com/jina-ai/jina/commit/760597737557bce10b3df4804fcc6870c71a1f28)] __-__ logic on set reducing-yaml-path (*Han Xiao*)
 - [[```a660a5ba```](https://github.com/jina-ai/jina/commit/a660a5bafd1ed23d6d3f549602ae2e003016268c)] __-__ hide num_part and set default to 0 (*Han Xiao*)
 - [[```2e7a4043```](https://github.com/jina-ai/jina/commit/2e7a40438991abd890c0f40ed679bcb0c21e760f)] __-__ __encoder__: fix embeds returns (*Han Xiao*)
 - [[```59c6175b```](https://github.com/jina-ai/jina/commit/59c6175b543b7f47c84f5c2ed3bfac14548dad67)] __-__ __encoder__: remove np array convert (*Han Xiao*)
 - [[```39a97c73```](https://github.com/jina-ai/jina/commit/39a97c73ebf6a9e643dc8eea221286181480d75e)] __-__ pb indexer flush (*Han Xiao*)
 - [[```c48b56fd```](https://github.com/jina-ai/jina/commit/c48b56fdd4e8e3ff280369bcce76df80023aad24)] __-__ __docs__: suggestions for the flow docs (*joaopalotti@gmail.com*)
 - [[```aaa3a10f```](https://github.com/jina-ai/jina/commit/aaa3a10f181cb35e65ebe21caf7db6961934fa65)] __-__ rename default yaml for pbindex (*Han Xiao*)
 - [[```4b3753af```](https://github.com/jina-ai/jina/commit/4b3753af08e30ba9ccadd53f2fcd3f191f268f49)] __-__ __docs__: fixed minor typos in jina&#39;s 101 page (*joaopalotti@gmail.com*)
 - [[```93a91b57```](https://github.com/jina-ai/jina/commit/93a91b578acd249095e95940d51ff46175143295)] __-__ __flow__: update docstring in flow (*YueLiu-jina*)
 - [[```aa8d5183```](https://github.com/jina-ai/jina/commit/aa8d51839f0a79366e99c3301cc34eadada9c775)] __-__ __crafter__: fix args of the crafter (*Han Xiao*)
 - [[```8c04c14d```](https://github.com/jina-ai/jina/commit/8c04c14d2960196e1a7e0ee78a72ef4a77c210e5)] __-__ __cli__: update CLI autocomplete (*Han Xiao*)
 - [[```63a58484```](https://github.com/jina-ai/jina/commit/63a584846594b15cebec93fe5f584e0c0939f805)] __-__ __crafter__: fix type hinting for numeric crafter (*redram*)
 - [[```3b83bad1```](https://github.com/jina-ai/jina/commit/3b83bad1fd3b6378073e06947b3a56df2955d66c)] __-__ __crafter__: fix length in chunks of jieba crafter (*redram*)
 - [[```963ea7fb```](https://github.com/jina-ai/jina/commit/963ea7fbcd4b51e6dc0b596feaad2e82e0294cfd)] __-__ __client__: fix mime_type warning (*Han Xiao*)
 - [[```b7e472e2```](https://github.com/jina-ai/jina/commit/b7e472e22eb2a35e850da000d62b9492e3c0dac0)] __-__ __crafter__: fix content read when doc is pb already (*Han Xiao*)
 - [[```276e1420```](https://github.com/jina-ai/jina/commit/276e1420bfddbb2f881a7a18659a5d716b3deff9)] __-__ fix typo in tests (*Han Xiao*)

### 🚧 Code Refactoring

 - [[```92b491c0```](https://github.com/jina-ai/jina/commit/92b491c07e4a5a7dc6ce7e2356b866395ccc0e60)] __-__ __flow__: refactor build inplace param (*fhaase2*)
 - [[```d045ca07```](https://github.com/jina-ai/jina/commit/d045ca07c9f33a7f37483d6e59c1d850e95c6c85)] __-__ move num_part from args to proto (*Han Xiao*)
 - [[```e28a5ba5```](https://github.com/jina-ai/jina/commit/e28a5ba556e3daf701cde510da1fc5bd2bb62867)] __-__ __driver__: move convert crafter to driver (*Han Xiao*)
 - [[```66dfe75d```](https://github.com/jina-ai/jina/commit/66dfe75dc9a07bc687202da7ffcdffc279ae5115)] __-__ __proto__: add doc-level uri out of oneof content (*Han Xiao*)
 - [[```9de7dfd5```](https://github.com/jina-ai/jina/commit/9de7dfd5613b6f304d3f707d2fc2c76338b10e7c)] __-__ make BaseRanker abstract (*Han Xiao*)
 - [[```36efe799```](https://github.com/jina-ai/jina/commit/36efe79965af82bdcb72709c70d7490a8b5eba24)] __-__ __crafter__: remove unnecessary set (*Han Xiao*)
 - [[```0d69a09f```](https://github.com/jina-ai/jina/commit/0d69a09f84124ec7cfa2fd0a0610d3c3ba520147)] __-__ merge with master (*Han Xiao*)
 - [[```a39371f7```](https://github.com/jina-ai/jina/commit/a39371f750a5172dd9a8a3fbb5eb3bf2c941a7b7)] __-__ __crafter__: move mime type detect to driver (*Han Xiao*)

### 📗 Documentation

 - [[```b2cec94b```](https://github.com/jina-ai/jina/commit/b2cec94b14c58a9d4217f36cc89bd6b7775e4f85)] __-__ add arabic 101 link (*boussoffara*)
 - [[```ad97be6f```](https://github.com/jina-ai/jina/commit/ad97be6f567fcd20afe8b9b072f01aa0bcc85b9c)] __-__ __101 ar__: added arabic translation to jina 101 (*boussoffara*)
 - [[```8e9bff43```](https://github.com/jina-ai/jina/commit/8e9bff43d6329679e7e2cfe6f3767f0ef791e284)] __-__ remove whitespace and fix typo  chapter io (*Frederic Haase*)
 - [[```08ff87dd```](https://github.com/jina-ai/jina/commit/08ff87dda239177fb7396a0511cde7411763a5ed)] __-__ added support to the Portuguese language for 101 (*joaopalotti@gmail.com*)
 - [[```774e4757```](https://github.com/jina-ai/jina/commit/774e4757522c57eea96eff0e4e13d4bcf59f5ece)] __-__ add google bit model tutorial (*Han Xiao*)

### 🏁 Unit Test and CICD

 - [[```8dae4456```](https://github.com/jina-ai/jina/commit/8dae445609de447234f0ec891a7571813d97a623)] __-__ add a test for numpy indexing (*Han Xiao*)
 - [[```79e5f203```](https://github.com/jina-ai/jina/commit/79e5f20328738d5c0ed960c21f79838e0a43cefe)] __-__ add test for unarydriver (*Han Xiao*)

### 🍹 Other Improvements

 - [[```dde1cd51```](https://github.com/jina-ai/jina/commit/dde1cd51fd2e31e5f609a539811350fcb60a0904)] __-__ hotfix image reader (*Han Xiao*)
 - [[```baa7ef93```](https://github.com/jina-ai/jina/commit/baa7ef93e76a96b65b5166ba34678f30509b55e2)] __-__ fix format (*Han Xiao*)
 - [[```0a9c30e6```](https://github.com/jina-ai/jina/commit/0a9c30e6ca47cba30ed3d5017961af302f83472a)] __-__ Update README.md (*Han Xiao*)
 - [[```3773f9ec```](https://github.com/jina-ai/jina/commit/3773f9ec8a72a90552b74f00728aa8b4222ba3dc)] __-__ __readme__: add start from cookiecutter template (*Han Xiao*)
 - [[```5ae682a6```](https://github.com/jina-ai/jina/commit/5ae682a62885f90134daa26666f6643f0b9bf01c)] __-__ fix format in readme (*Han Xiao*)
 - [[```b28bfc48```](https://github.com/jina-ai/jina/commit/b28bfc48cc820063a8e9aab2397a093035431347)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```7136d6b4```](https://github.com/jina-ai/jina/commit/7136d6b41584348fd2a16d008ce2989f38dc27ed)] __-__ __version__: bumping version to 0.2.4 (*Jina Dev Bot*)
 - [[```8f73cba3```](https://github.com/jina-ai/jina/commit/8f73cba3c627143ea973fb3d28b9d04b640821b2)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```a2ccb20c```](https://github.com/jina-ai/jina/commit/a2ccb20cbb1ef6084050b162b8b986c055b5e48c)] __-__ __version__: bumping version to 0.2.3 (*Jina Dev Bot*)
 - [[```a704586a```](https://github.com/jina-ai/jina/commit/a704586a48adc32c2146b73dfe92b10565b7f1dd)] __-__ __version__: bumping version to 0.2.2 (*Jina Dev Bot*)
 - [[```e6ba1682```](https://github.com/jina-ai/jina/commit/e6ba1682a69a2d40c9198f5789e7866f282f37bb)] __-__ __version__: bumping version to 0.2.1 (*Jina Dev Bot*)
 - [[```b72ad858```](https://github.com/jina-ai/jina/commit/b72ad858744a0314facbaed27491befdb8dcd3c2)] __-__ hotfix release 0.2.0 (*Han Xiao*)
 - [[```25d5797f```](https://github.com/jina-ai/jina/commit/25d5797fa995bee3966686bcd34434d0a87cc342)] __-__ release 0.2.0 (*Han Xiao*)
 - [[```ff63c7fc```](https://github.com/jina-ai/jina/commit/ff63c7fc18019332207540f397daf5b950dc106d)] __-__ __version__: bumping version to 0.1.15 (*Jina Dev Bot*)
 - [[```97403ab2```](https://github.com/jina-ai/jina/commit/97403ab2847f8670b8c888a553a369f057563b14)] __-__ hotfix for pokedex (*Han Xiao*)

## Release Note (`0.2.5`)

> Release time: 2020-06-11 20:14:36



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  🙇


### 🆕 New Features

 - [[```52d0bbe7```](https://github.com/jina-ai/jina/commit/52d0bbe73ff1bc652211ffd1e88f4818b0f32388)] __-__ __indexer__: add binary KVIndexer with better perf (*Han Xiao*)

### 🚧 Code Refactoring

 - [[```86a625d7```](https://github.com/jina-ai/jina/commit/86a625d7cf1814abdb180326d0b059609f3bc27c)] __-__ __leveldb__: fix to new basepbindexer (*Han Xiao*)

### 📗 Documentation

 - [[```2aa59bd4```](https://github.com/jina-ai/jina/commit/2aa59bd4693d97f64fa30ecf86a34c91c92ddbdb)] __-__ add explain on JINA_BINARY_DELIMITER (*Han Xiao*)

### 🍹 Other Improvements

 - [[```2ff9bbad```](https://github.com/jina-ai/jina/commit/2ff9bbad79c485aaa46061d05e5be8500c0520a6)] __-__ hotfix improved chunkpbindexer (*Han Xiao*)
 - [[```352434dd```](https://github.com/jina-ai/jina/commit/352434dd2ffd6db684c23b0c9572a6008b5b2bc1)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```f43d7563```](https://github.com/jina-ai/jina/commit/f43d7563c7488e5e471328e58e368388892e3d68)] __-__ __version__: bumping version to 0.2.5 (*Jina Dev Bot*)

## Release Note (`0.2.6`)

> Release time: 2020-06-12 15:58:02



🙇 We'd like to thank all contributors for this new release! In particular,
 Jina Dev Bot,  fhaase2,  Han Xiao,  Nan Wang,  redram,  joaopalotti@gmail.com,  🙇


### 🆕 New Features

 - [[```249201aa```](https://github.com/jina-ai/jina/commit/249201aa590916e32b1068893d1092b1692e2ab1)] __-__ restore the unittests (*Nan Wang*)
 - [[```71a2023c```](https://github.com/jina-ai/jina/commit/71a2023cd7a3185fc34730cf644aea6106e87bd1)] __-__ __encoder__: add wav2vec speech encoder (*redram*)
 - [[```7146c66d```](https://github.com/jina-ai/jina/commit/7146c66de8e9477f9d819b31dd9d73a0a3b14553)] __-__ clean up (*Nan Wang*)
 - [[```a88c9719```](https://github.com/jina-ai/jina/commit/a88c9719eac68beba3be854ea4b2191366c2da0f)] __-__ update the abstract (*Nan Wang*)
 - [[```b932c744```](https://github.com/jina-ai/jina/commit/b932c744d66c5299981609bfedcc9120262ed5ac)] __-__ update the flow diagram (*Nan Wang*)
 - [[```c48cd974```](https://github.com/jina-ai/jina/commit/c48cd974fc4a464a45c750198efd5b6988cd1a08)] __-__ add an example for the Specification (*Nan Wang*)
 - [[```ece5e21a```](https://github.com/jina-ai/jina/commit/ece5e21a7154355dd305a004c538c42bacfa1b4c)] __-__ refactor the design (*Nan Wang*)
 - [[```f092fe95```](https://github.com/jina-ai/jina/commit/f092fe953924a2fd4d285683c0f543703b37bb73)] __-__ refactoring the overall design (*Nan Wang*)
 - [[```1875eaff```](https://github.com/jina-ai/jina/commit/1875eaffbdb01e88c319c5d965520ab2af071adf)] __-__ __client__: add input function sugar (*Han Xiao*)
 - [[```15cbac1d```](https://github.com/jina-ai/jina/commit/15cbac1dcfcf063e7d088e6750ffe27ddf6ee993)] __-__ __crafters__: add audio crafters (*redram*)
 - [[```5302c162```](https://github.com/jina-ai/jina/commit/5302c162431127690e2bfc03035a3991e00efb7e)] __-__ fix typos (*Nan Wang*)
 - [[```11e9e059```](https://github.com/jina-ai/jina/commit/11e9e059fed854042ba9f09023258bd77fc2f6db)] __-__ add the 1st draft for JEP-3 (*Nan Wang*)
 - [[```9dfe9188```](https://github.com/jina-ai/jina/commit/9dfe9188d8df75cf3fa1220e86d064be1cbd21df)] __-__ __crafter__: add buffer, data_uri, file_path convert (*Han Xiao*)
 - [[```c2d3e819```](https://github.com/jina-ai/jina/commit/c2d3e8199ff38e85754b45d2fca96b28d72a5f8a)] __-__ __proto__: add mime_type to proto (*Han Xiao*)

### 🐞 Bug fixes

 - [[```f1530791```](https://github.com/jina-ai/jina/commit/f1530791fd14e466a852e1fa01f9bc3d06f04568)] __-__ debug the unittest failures (*Nan Wang*)
 - [[```63a58484```](https://github.com/jina-ai/jina/commit/63a584846594b15cebec93fe5f584e0c0939f805)] __-__ __crafter__: fix type hinting for numeric crafter (*redram*)
 - [[```3b83bad1```](https://github.com/jina-ai/jina/commit/3b83bad1fd3b6378073e06947b3a56df2955d66c)] __-__ __crafter__: fix length in chunks of jieba crafter (*redram*)
 - [[```963ea7fb```](https://github.com/jina-ai/jina/commit/963ea7fbcd4b51e6dc0b596feaad2e82e0294cfd)] __-__ __client__: fix mime_type warning (*Han Xiao*)
 - [[```b7e472e2```](https://github.com/jina-ai/jina/commit/b7e472e22eb2a35e850da000d62b9492e3c0dac0)] __-__ __crafter__: fix content read when doc is pb already (*Han Xiao*)
 - [[```276e1420```](https://github.com/jina-ai/jina/commit/276e1420bfddbb2f881a7a18659a5d716b3deff9)] __-__ fix typo in tests (*Han Xiao*)

### 🚧 Code Refactoring

 - [[```7239d6ab```](https://github.com/jina-ai/jina/commit/7239d6abc05c18a664bf92d3163462312e259dd1)] __-__ string formatting (*fhaase2*)
 - [[```9de7dfd5```](https://github.com/jina-ai/jina/commit/9de7dfd5613b6f304d3f707d2fc2c76338b10e7c)] __-__ make BaseRanker abstract (*Han Xiao*)
 - [[```36efe799```](https://github.com/jina-ai/jina/commit/36efe79965af82bdcb72709c70d7490a8b5eba24)] __-__ __crafter__: remove unnecessary set (*Han Xiao*)
 - [[```0d69a09f```](https://github.com/jina-ai/jina/commit/0d69a09f84124ec7cfa2fd0a0610d3c3ba520147)] __-__ merge with master (*Han Xiao*)
 - [[```a39371f7```](https://github.com/jina-ai/jina/commit/a39371f750a5172dd9a8a3fbb5eb3bf2c941a7b7)] __-__ __crafter__: move mime type detect to driver (*Han Xiao*)

### 📗 Documentation

 - [[```08ff87dd```](https://github.com/jina-ai/jina/commit/08ff87dda239177fb7396a0511cde7411763a5ed)] __-__ added support to the Portuguese language for 101 (*joaopalotti@gmail.com*)
 - [[```774e4757```](https://github.com/jina-ai/jina/commit/774e4757522c57eea96eff0e4e13d4bcf59f5ece)] __-__ add google bit model tutorial (*Han Xiao*)

### 🏁 Unit Test and CICD

 - [[```87d90768```](https://github.com/jina-ai/jina/commit/87d907684ac623ad09a72616e4bbd3e230b7f464)] __-__ fix cyclic imports (*Han Xiao*)
 - [[```8dae4456```](https://github.com/jina-ai/jina/commit/8dae445609de447234f0ec891a7571813d97a623)] __-__ add a test for numpy indexing (*Han Xiao*)
 - [[```79e5f203```](https://github.com/jina-ai/jina/commit/79e5f20328738d5c0ed960c21f79838e0a43cefe)] __-__ add test for unarydriver (*Han Xiao*)

### 🍹 Other Improvements

 - [[```f92a914e```](https://github.com/jina-ai/jina/commit/f92a914ec260729123ad4783fc4223618db7e6cb)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```ccc7f4be```](https://github.com/jina-ai/jina/commit/ccc7f4be6bbc3dee90f41c304b50f90a21707d1e)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```ffa9397b```](https://github.com/jina-ai/jina/commit/ffa9397b028aba44f7f2c2250fbaacdbb37e11e6)] __-__ __version__: bumping version to 0.2.6 (*Jina Dev Bot*)
 - [[```f43d7563```](https://github.com/jina-ai/jina/commit/f43d7563c7488e5e471328e58e368388892e3d68)] __-__ __version__: bumping version to 0.2.5 (*Jina Dev Bot*)
 - [[```dde1cd51```](https://github.com/jina-ai/jina/commit/dde1cd51fd2e31e5f609a539811350fcb60a0904)] __-__ hotfix image reader (*Han Xiao*)
 - [[```a704586a```](https://github.com/jina-ai/jina/commit/a704586a48adc32c2146b73dfe92b10565b7f1dd)] __-__ __version__: bumping version to 0.2.2 (*Jina Dev Bot*)
 - [[```e6ba1682```](https://github.com/jina-ai/jina/commit/e6ba1682a69a2d40c9198f5789e7866f282f37bb)] __-__ __version__: bumping version to 0.2.1 (*Jina Dev Bot*)
 - [[```b72ad858```](https://github.com/jina-ai/jina/commit/b72ad858744a0314facbaed27491befdb8dcd3c2)] __-__ hotfix release 0.2.0 (*Han Xiao*)
 - [[```25d5797f```](https://github.com/jina-ai/jina/commit/25d5797fa995bee3966686bcd34434d0a87cc342)] __-__ release 0.2.0 (*Han Xiao*)
 - [[```ff63c7fc```](https://github.com/jina-ai/jina/commit/ff63c7fc18019332207540f397daf5b950dc106d)] __-__ __version__: bumping version to 0.1.15 (*Jina Dev Bot*)
 - [[```97403ab2```](https://github.com/jina-ai/jina/commit/97403ab2847f8670b8c888a553a369f057563b14)] __-__ hotfix for pokedex (*Han Xiao*)

## Release Note (`0.2.7`)

> Release time: 2020-06-15 22:01:52



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  Rutuja Surve,  redram,  fhaase2,  🙇


### 🆕 New Features

 - [[```0c0c8fef```](https://github.com/jina-ai/jina/commit/0c0c8fefed3fc2005cb1ffd8c589e39d75faabcf)] __-__ __proto__: add details to error status (*Han Xiao*)
 - [[```08e9ddee```](https://github.com/jina-ai/jina/commit/08e9ddee3fd1facf5b1b0503fb70520ef64511aa)] __-__ __peapod__: add function to propagate error message through workflow (*Rutuja Surve*)
 - [[```6dcdd488```](https://github.com/jina-ai/jina/commit/6dcdd48862049ed3fe8b0cfe3bb671e6f0b77467)] __-__ add if expr to basedriver (*Han Xiao*)
 - [[```29aef4e3```](https://github.com/jina-ai/jina/commit/29aef4e30493d84e7332042b3ba674dba47752bf)] __-__ __encoder__: improve wav2vec encoder with signal resampling (*redram*)

### 🐞 Bug fixes

 - [[```46d4f454```](https://github.com/jina-ai/jina/commit/46d4f45458190d9f1e70efc47af5c2acbedffef7)] __-__ __proto__: move status outside of envelope (*Han Xiao*)
 - [[```633b92bb```](https://github.com/jina-ai/jina/commit/633b92bbb55129a58d85ba37550bb0c4c9d568dc)] __-__ __logging__: profile and log streams non-blocking (*fhaase2*)

### 🚧 Code Refactoring

 - [[```74062a62```](https://github.com/jina-ai/jina/commit/74062a6248c6f7ba0806292fc9f3e204aea430df)] __-__ __except__: reorganize the excepts (*Han Xiao*)
 - [[```b12f70a3```](https://github.com/jina-ai/jina/commit/b12f70a35394027f172de151380f4a9949de3f07)] __-__ __pea__: improve error catch logic (*Han Xiao*)
 - [[```aca19304```](https://github.com/jina-ai/jina/commit/aca19304dd322090b82b6b07db5f24af173a591b)] __-__ __pea__: improve error catching logics (*Han Xiao*)
 - [[```ca83488e```](https://github.com/jina-ai/jina/commit/ca83488e4f9356b75c06f47411bed92c6a3ac495)] __-__ __crafter__: extract set_chunk method (*Han Xiao*)

### 📗 Documentation

 - [[```09f4c37d```](https://github.com/jina-ai/jina/commit/09f4c37d45462cfc9f237c84ba21e5c6a0a1d601)] __-__ __driver__: add if to docstring (*Han Xiao*)

### 🍹 Other Improvements

 - [[```9ea6ca96```](https://github.com/jina-ai/jina/commit/9ea6ca96b1d48540b404a7a78c3fe0d08139d217)] __-__ hotfix error catching (*Han Xiao*)
 - [[```0c573044```](https://github.com/jina-ai/jina/commit/0c573044b9b229b5e6ad1f5688fb9f0b16339e46)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```0fc81f80```](https://github.com/jina-ai/jina/commit/0fc81f809114699a7dd35b13ce0e90b8f944afd8)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```ca6ac545```](https://github.com/jina-ai/jina/commit/ca6ac545937521b1e499e15b7073ee33a3b4b3de)] __-__ __version__: bumping version to 0.2.7 (*Jina Dev Bot*)

## Release Note (`0.2.8`)

> Release time: 2020-06-19 15:57:17



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Yue Liu,  Jina Dev Bot,  Nan Wang,  Alex C-G,  fhaase2,  🙇


### 🆕 New Features

 - [[```ae42091a```](https://github.com/jina-ai/jina/commit/ae42091a016188cc90b64c77f0546ded2aa58d69)] __-__ __driver__: add uri2text convert (*Han Xiao*)
 - [[```df91778c```](https://github.com/jina-ai/jina/commit/df91778c769f26a80b2947408e449cf45995644d)] __-__ __crafter__: add deepsegment (*Han Xiao*)

### 🐞 Bug fixes

 - [[```7577d3b7```](https://github.com/jina-ai/jina/commit/7577d3b76da390425d274ca93fd1dcf4e5c75dc3)] __-__ __cla__: add employee to cla whitelist (*Han Xiao*)
 - [[```a579df5d```](https://github.com/jina-ai/jina/commit/a579df5dfe7ede825113bbf9e75f9c0e67cd5719)] __-__ __docs__: add 404 page generation (*Han Xiao*)
 - [[```d970b118```](https://github.com/jina-ai/jina/commit/d970b118413bb8f433c3dba9cd6cee33578fc9f5)] __-__ add support for npy training data (*Nan Wang*)
 - [[```7c99b7e9```](https://github.com/jina-ai/jina/commit/7c99b7e9dcd9e03f5b769e0483a07e5471a7d701)] __-__ __logging__: profile and log streams non-blocking (*fhaase2*)
 - [[```e515e2ba```](https://github.com/jina-ai/jina/commit/e515e2bac029ce5fb96cd1a4d052d94f27e63933)] __-__ __driver__: improve efficiency of topk filter (*Han Xiao*)
 - [[```089b9342```](https://github.com/jina-ai/jina/commit/089b93422efcfafbd20d6b435f92d8bcb0d390ef)] __-__ __except__: move inherit from oserror to syserror (*Han Xiao*)
 - [[```4fa99d7f```](https://github.com/jina-ai/jina/commit/4fa99d7fcd57e423c50fbd570cba7798d6207139)] __-__ clean up imports (*Nan Wang*)
 - [[```5eabbb46```](https://github.com/jina-ai/jina/commit/5eabbb46f2bec40ae6c27626db7041081d9db6ee)] __-__ add docs (*Nan Wang*)
 - [[```5ec57d6d```](https://github.com/jina-ai/jina/commit/5ec57d6dddf85c5edff632f620c3fdba35b27072)] __-__ fix the query bug in faiss (*Nan Wang*)

### 📗 Documentation

 - [[```e8e7a6bf```](https://github.com/jina-ai/jina/commit/e8e7a6bf0269b33cd8bc949bd8da72cea08e6afb)] __-__ __readme__: zh (*Yue Liu*)
 - [[```517d01ad```](https://github.com/jina-ai/jina/commit/517d01ad27b5fdbd39145e635cacf59b352d9641)] __-__ __readme__: ru (*Yue Liu*)
 - [[```6dcf3dfa```](https://github.com/jina-ai/jina/commit/6dcf3dfa314d72741682191ceaf70db815294734)] __-__ __readme__: en (*Yue Liu*)
 - [[```71208c23```](https://github.com/jina-ai/jina/commit/71208c23d97a31c62373819b5dceaef1c1c05eb0)] __-__ __readme__: ja (*Yue Liu*)
 - [[```95a05e6a```](https://github.com/jina-ai/jina/commit/95a05e6a09cb8ac6d4ba8c93a643f48a58423b1f)] __-__ __readme__: fr (*Yue Liu*)
 - [[```8d3965ac```](https://github.com/jina-ai/jina/commit/8d3965ac0ad2a4b4261e221a9b74a092deaf7b7d)] __-__ __readme__: de (*Yue Liu*)
 - [[```53c56e55```](https://github.com/jina-ai/jina/commit/53c56e55f4e83fe693f664166223ee22a668ecaf)] __-__ __101__: restructure, rewrite (*Alex C-G*)
 - [[```df499241```](https://github.com/jina-ai/jina/commit/df499241785d76ab37906b38a1e5afa3ec3eceef)] __-__ __101__: get up and running (*Alex C-G*)
 - [[```7ac80fb1```](https://github.com/jina-ai/jina/commit/7ac80fb1867f1d8a939a7809eeb3940ca09048f2)] __-__ __101__: spacing (*Alex C-G*)
 - [[```a411b321```](https://github.com/jina-ai/jina/commit/a411b3212da8929b635efa37c99ea46fd617f670)] __-__ __101__: Improve analogy (*Alex C-G*)
 - [[```802af445```](https://github.com/jina-ai/jina/commit/802af4457bb459ed18a7149a922c977a90f6582c)] __-__ __101__: Pancake analogy in chunk section (*Alex C-G*)
 - [[```4d9103c7```](https://github.com/jina-ai/jina/commit/4d9103c749566749a7d53dcbd26ac670511156b4)] __-__ __101__: rewording, formatting (*Alex C-G*)
 - [[```9ce44431```](https://github.com/jina-ai/jina/commit/9ce44431c364b37c3aad1ac218ebba9a362c0f00)] __-__ __101__: what is jina/why neural search sections (*Alex C-G*)
 - [[```b6caa5dd```](https://github.com/jina-ai/jina/commit/b6caa5dddf2ebc49d596a2a0f5e88aaad5d8528e)] __-__ __101__: link for yaml (*Alex C-G*)
 - [[```a0b88c90```](https://github.com/jina-ai/jina/commit/a0b88c90c7c837296d0b77b208b3bb1a35380039)] __-__ __101__: delete huge spacing (*Alex C-G*)
 - [[```78216f26```](https://github.com/jina-ai/jina/commit/78216f2686154331494a14dc19b82e92bf680dd7)] __-__ __101__: center all images (*Alex C-G*)
 - [[```11626bcd```](https://github.com/jina-ai/jina/commit/11626bcda7e6e39c656b4f15a6f7b6fb38953dd6)] __-__ __101__: image center test 3 (*Alex C-G*)
 - [[```ec5464e8```](https://github.com/jina-ai/jina/commit/ec5464e8709cf5735c1addf95f85369349241873)] __-__ __101__: image center test 2 (*Alex C-G*)
 - [[```628b0fc8```](https://github.com/jina-ai/jina/commit/628b0fc8481f381ca5325b54825659d8eec963cb)] __-__ __101__: image center test (*Alex C-G*)
 - [[```7797b23a```](https://github.com/jina-ai/jina/commit/7797b23a8541725c8c2ec97960ee99838cbc88ea)] __-__ __101__: edits, test image moving (*Alex C-G*)
 - [[```41c9a144```](https://github.com/jina-ai/jina/commit/41c9a1441639f677bf71fc24da377535f7c94d78)] __-__ __101__: More rewording and editing; some pics removed (*Alex C-G*)
 - [[```ca42d9df```](https://github.com/jina-ai/jina/commit/ca42d9dfa5245e36487b15e636e92f2d382d7405)] __-__ __101__: Comment out PDF button that doesnt link to PDF (*Alex C-G*)
 - [[```0a7a3b46```](https://github.com/jina-ai/jina/commit/0a7a3b46dd2a48d0d578dba53e7531963543392f)] __-__ __101__: Rewriting (*Alex C-G*)
 - [[```d20b00dd```](https://github.com/jina-ai/jina/commit/d20b00dd6cf4bfa524bc1ee3ab576609cccb5bcd)] __-__ __101__: Redo headings (*Alex C-G*)
 - [[```4f94c371```](https://github.com/jina-ai/jina/commit/4f94c3719d3fb581a3716fb4602e35f7b4c55d00)] __-__ __101__: New section (*Alex C-G*)

### 🍹 Other Improvements

 - [[```22f29e39```](https://github.com/jina-ai/jina/commit/22f29e39df2ea37b221c4ccbebe8326130970c3a)] __-__ 101 (*Han Xiao*)
 - [[```ffddeb04```](https://github.com/jina-ai/jina/commit/ffddeb049ea057ece2a5f916e97b304ee80dbf6c)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```fb8a68fa```](https://github.com/jina-ai/jina/commit/fb8a68fa166fa744d46045a48b2e4e043448e42b)] __-__ __version__: bumping version to 0.2.8 (*Jina Dev Bot*)
 - [[```ca6ac545```](https://github.com/jina-ai/jina/commit/ca6ac545937521b1e499e15b7073ee33a3b4b3de)] __-__ __version__: bumping version to 0.2.7 (*Jina Dev Bot*)
 - [[```f92a914e```](https://github.com/jina-ai/jina/commit/f92a914ec260729123ad4783fc4223618db7e6cb)] __-__ update copyright header (*Jina Dev Bot*)

## Release Note (`0.2.9`)

> Release time: 2020-06-21 10:06:44



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  fhaase2,  🙇


### 🆕 New Features

 - [[```bf231280```](https://github.com/jina-ai/jina/commit/bf23128094f523bb781ba046dfa14df64cad8ce3)] __-__ __encoders__: add universal sentence encoder (*fhaase2*)

### 🐞 Bug fixes

 - [[```020c92b2```](https://github.com/jina-ai/jina/commit/020c92b26c5c28c149356a603f86c4ecb4e7d100)] __-__ __pea__: fix except handling in pea (*Han Xiao*)

### 🏁 Unit Test and CICD

 - [[```88a67412```](https://github.com/jina-ai/jina/commit/88a6741245e76186e707e5d1481b9a37273b4034)] __-__ __drivers__: add test for prune driver (*fhaase2*)

### 🍹 Other Improvements

 - [[```94322a8d```](https://github.com/jina-ai/jina/commit/94322a8d50b6e0b666c04ca4a3c43c108fa8bb57)] __-__ hotfix error handling (*Han Xiao*)
 - [[```ae9832e8```](https://github.com/jina-ai/jina/commit/ae9832e842bcf8436ee6490d6f0a0963f9e8b167)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```cd57b690```](https://github.com/jina-ai/jina/commit/cd57b690a3d4a492475314ad64a90f8da568b352)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```4ab91693```](https://github.com/jina-ai/jina/commit/4ab91693c2d51a35eca3cf6c187034e0568b0ac9)] __-__ __version__: bumping version to 0.2.9 (*Jina Dev Bot*)

## Release Note (`0.2.10`)

> Release time: 2020-06-23 19:36:22



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  fhaase2,  Yue Liu,  🙇


### 🆕 New Features

 - [[```1e7d3b6b```](https://github.com/jina-ai/jina/commit/1e7d3b6b6dc7f4a46baabaf70f16d60955f4c0db)] __-__ add password from stdin (*Han Xiao*)

### 🐞 Bug fixes

 - [[```7a648ea3```](https://github.com/jina-ai/jina/commit/7a648ea3d099d7f2b128bf300ce693001c5a368c)] __-__ __indexer__: is trained set on train call (*fhaase2*)

### 🏁 Unit Test and CICD

 - [[```d0be9f32```](https://github.com/jina-ai/jina/commit/d0be9f32649eaab17627d64405a8d2f46e638b2b)] __-__ delete empty space in a filename (*Yue Liu*)

### 🍹 Other Improvements

 - [[```4a98575a```](https://github.com/jina-ai/jina/commit/4a98575a414a467b82726af6f231e85d35712f6b)] __-__ hotfix add jina hub command (*Han Xiao*)
 - [[```b18aa902```](https://github.com/jina-ai/jina/commit/b18aa902b91e0252bee03d4b0d5dfe59779aab0c)] __-__ add jina hub command (*Han Xiao*)
 - [[```f84bca6b```](https://github.com/jina-ai/jina/commit/f84bca6b2efce0458d378ecc058fd629e5939363)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```7764f053```](https://github.com/jina-ai/jina/commit/7764f05356579bd2aab098a342018dee96d5903a)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```79b302c9```](https://github.com/jina-ai/jina/commit/79b302c93b01689e82cf4b52f46522eb7497c404)] __-__ __version__: bumping version to 0.2.10 (*Jina Dev Bot*)

## Release Note (`0.3.0`)

> Release time: 2020-06-24 14:26:50



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  Alex C-G,  fhaase2,  Yue Liu,  🙇


### 🆕 New Features

 - [[```3e983307```](https://github.com/jina-ai/jina/commit/3e983307fb71a209de81a874a9e6bd6914b801fc)] __-__ __hub__: add docker readme (*Han Xiao*)
 - [[```33a944a4```](https://github.com/jina-ai/jina/commit/33a944a44a7f5605933f643966845c0d59d793fc)] __-__ __hub__: add success html page (*Han Xiao*)
 - [[```df91778c```](https://github.com/jina-ai/jina/commit/df91778c769f26a80b2947408e449cf45995644d)] __-__ __crafter__: add deepsegment (*Han Xiao*)

### 🐞 Bug fixes

 - [[```23905c13```](https://github.com/jina-ai/jina/commit/23905c134629f06edcd73741191ed4fd14234026)] __-__ fix password-stdin (*Han Xiao*)
 - [[```7a648ea3```](https://github.com/jina-ai/jina/commit/7a648ea3d099d7f2b128bf300ce693001c5a368c)] __-__ __indexer__: is trained set on train call (*fhaase2*)
 - [[```e515e2ba```](https://github.com/jina-ai/jina/commit/e515e2bac029ce5fb96cd1a4d052d94f27e63933)] __-__ __driver__: improve efficiency of topk filter (*Han Xiao*)
 - [[```089b9342```](https://github.com/jina-ai/jina/commit/089b93422efcfafbd20d6b435f92d8bcb0d390ef)] __-__ __except__: move inherit from oserror to syserror (*Han Xiao*)

### 📗 Documentation

 - [[```7bb1d691```](https://github.com/jina-ai/jina/commit/7bb1d691a522fea76d6d967873b972749d28156b)] __-__ __contributing__: before starting section (*Alex C-G*)
 - [[```40a01d9b```](https://github.com/jina-ai/jina/commit/40a01d9b720e78acea50e78ee929f26721dc8040)] __-__ __contributing__: info on string length (*Alex C-G*)
 - [[```92b81843```](https://github.com/jina-ai/jina/commit/92b81843997d4c80dd00cd9c738206112cf238c6)] __-__ __contributing__: remove duplicated naming conventions (*Alex C-G*)
 - [[```06bb4fbb```](https://github.com/jina-ai/jina/commit/06bb4fbbe8324c35bffeebf812f235f61d6a88f1)] __-__ __contributing__: remove duplicated bad examples (*Alex C-G*)
 - [[```6ce0ed53```](https://github.com/jina-ai/jina/commit/6ce0ed53f6f9f83ebb1fa7d8fc241bbb7cbf1137)] __-__ __contributing__: info from pinned issue, rewrite for easy use (*Alex C-G*)
 - [[```f1288681```](https://github.com/jina-ai/jina/commit/f1288681c1448e58691464051bd2f085b407b494)] __-__ __101__: capitalization, remove pancake analogy (*Alex C-G*)
 - [[```5f3ba6c3```](https://github.com/jina-ai/jina/commit/5f3ba6c35ba03436f875dbc9c3caa5bb03a50987)] __-__ __101__: punctuation (*Alex C-G*)
 - [[```79fbf2bd```](https://github.com/jina-ai/jina/commit/79fbf2bd3e3d7be5a1036cefc092aa29aa017400)] __-__ __101__: remove question from text that i added before (*Alex C-G*)
 - [[```07a5d90f```](https://github.com/jina-ai/jina/commit/07a5d90f92ea05d558c075872a8bd46000430aab)] __-__ __101__: heading capitalization, formatting (*Alex C-G*)
 - [[```9ff5e3cb```](https://github.com/jina-ai/jina/commit/9ff5e3cbae6fe0af0fbf59d8a80461e85482eff3)] __-__ __101__: cherry-pick updated text (*Alex C-G*)

### 🏁 Unit Test and CICD

 - [[```d0be9f32```](https://github.com/jina-ai/jina/commit/d0be9f32649eaab17627d64405a8d2f46e638b2b)] __-__ delete empty space in a filename (*Yue Liu*)

### 🍹 Other Improvements

 - [[```4ceb5fde```](https://github.com/jina-ai/jina/commit/4ceb5fde70d3dcd87af8784a3a3a690b5c6ad69e)] __-__ hotfix password stdin (*Han Xiao*)
 - [[```cabf4bdd```](https://github.com/jina-ai/jina/commit/cabf4bddf29c11e0249bb709a278f073e40591d6)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```14de9429```](https://github.com/jina-ai/jina/commit/14de9429ca8225b83136f638fed9b8e3d8e32d0e)] __-__ __version__: bumping version to 0.2.11 (*Jina Dev Bot*)
 - [[```79b302c9```](https://github.com/jina-ai/jina/commit/79b302c93b01689e82cf4b52f46522eb7497c404)] __-__ __version__: bumping version to 0.2.10 (*Jina Dev Bot*)
 - [[```94322a8d```](https://github.com/jina-ai/jina/commit/94322a8d50b6e0b666c04ca4a3c43c108fa8bb57)] __-__ hotfix error handling (*Han Xiao*)
 - [[```fb8a68fa```](https://github.com/jina-ai/jina/commit/fb8a68fa166fa744d46045a48b2e4e043448e42b)] __-__ __version__: bumping version to 0.2.8 (*Jina Dev Bot*)
 - [[```9ea6ca96```](https://github.com/jina-ai/jina/commit/9ea6ca96b1d48540b404a7a78c3fe0d08139d217)] __-__ hotfix error catching (*Han Xiao*)

## Release Note (`0.3.1`)

> Release time: 2020-06-25 21:38:52



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  Alex C-G,  🙇


### 🆕 New Features

 - [[```012e9e13```](https://github.com/jina-ai/jina/commit/012e9e136b5e8a42995954ca2a16e9e359c4a394)] __-__ __peapods__: add error skipping strategy (*Han Xiao*)

### 🐞 Bug fixes

 - [[```bed4f556```](https://github.com/jina-ai/jina/commit/bed4f556a0cd3b5b93177acef532746d017611dc)] __-__ __driver__: remove pub driver with post_hook (*Han Xiao*)

### 📗 Documentation

 - [[```2fd88767```](https://github.com/jina-ai/jina/commit/2fd88767d7c29b560eeb0d92a16f4e752f290bb7)] __-__ __readme__: wording improvement (*Alex C-G*)
 - [[```767dddb4```](https://github.com/jina-ai/jina/commit/767dddb443aa0c63e15cd3848288c9f981cd9eb4)] __-__ __code-of-conduct__: initial commit (*Alex C-G*)

### 🍹 Other Improvements

 - [[```0db4bd9f```](https://github.com/jina-ai/jina/commit/0db4bd9fee7c6403b93de5a72fd652e76c275a35)] __-__ hotfix publish driver (*Han Xiao*)
 - [[```358bfec1```](https://github.com/jina-ai/jina/commit/358bfec1c327a24624461bfdbcf79ed54346e0b6)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```49de8711```](https://github.com/jina-ai/jina/commit/49de87113b665341c588329f9c54ba2f379b4ebd)] __-__ __version__: the next version will be 0.3.1 (*Jina Dev Bot*)

## Release Note (`0.3.2`)

> Release time: 2020-06-26 15:57:23



🙇 We'd like to thank all contributors for this new release! In particular,
 Jina Dev Bot,  🙇


### 🍹 Other Improvements

 - [[```60000083```](https://github.com/jina-ai/jina/commit/60000083c57a6cf17f77fc50e6fc496089516f13)] __-__ __version__: the next version will be 0.3.2 (*Jina Dev Bot*)

## Release Note (`0.3.3`)

> Release time: 2020-06-30 00:25:56



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Morry Wang,  fhaase2,  Jina Dev Bot,  BingHo1013,  🙇


### 🆕 New Features

 - [[```7e592805```](https://github.com/jina-ai/jina/commit/7e592805cef3fd1fef8b93783a5f569a7e555dd9)] __-__ __helloworld__: add cli arg &#39;download-proxy&#39; (*Morry Wang*)
 - [[```5ac225e8```](https://github.com/jina-ai/jina/commit/5ac225e809adf266837ac372f56b80e19b59353b)] __-__ __indexer__: allow user switch indexer in query time (*Han Xiao*)
 - [[```6158ce3d```](https://github.com/jina-ai/jina/commit/6158ce3d188c50163e8d4d2595b52e5232ad483a)] __-__ __indexer__: add size (*Han Xiao*)
 - [[```66bef2c1```](https://github.com/jina-ai/jina/commit/66bef2c1ff30caff5306d91da63020bed1d93d1b)] __-__ __proto__: add location info to chunk (*Han Xiao*)

### 🐞 Bug fixes

 - [[```f67fdf1b```](https://github.com/jina-ai/jina/commit/f67fdf1bb3ff8b7c6aeae532bb6c09389ab6496a)] __-__ __indexer__: fix ref_indexer in ChunkIndexer (*Han Xiao*)
 - [[```11f80552```](https://github.com/jina-ai/jina/commit/11f8055285753ae28deb7593bfaf2ed571d68270)] __-__ __indexer__: fix index size logging (*Han Xiao*)
 - [[```487f5bad```](https://github.com/jina-ai/jina/commit/487f5badf922973b2ba2cfa901817ab1ed930362)] __-__ __driver__: fix del in topkfilter (*Han Xiao*)
 - [[```e4c5aca4```](https://github.com/jina-ai/jina/commit/e4c5aca4b85068f31b0ddc284b00924305f6241a)] __-__ __driver__: topkfilter now remove irrelevant chunks (*Han Xiao*)
 - [[```ea8c1fec```](https://github.com/jina-ai/jina/commit/ea8c1fecd52359e1abbe59f62d8399e0e8505feb)] __-__ __driver__: move topkfilter to ranker (*Han Xiao*)

### 🚧 Code Refactoring

 - [[```1b67d379```](https://github.com/jina-ai/jina/commit/1b67d3794d7335210d9e8e533edeabd7760ab9e8)] __-__ __indexer__: abstract rw ndarray from numpyindexer (*Han Xiao*)

### 🏁 Unit Test and CICD

 - [[```0e4c4c1e```](https://github.com/jina-ai/jina/commit/0e4c4c1e17ffa7ea99b563dc280e7de23ce69cad)] __-__ __gateway__: concurrency test for rest gateway (*fhaase2*)

### 🍹 Other Improvements

 - [[```29bbb28b```](https://github.com/jina-ai/jina/commit/29bbb28b935067f2241c3cab35483c1ce3fcbc2c)] __-__ hotfix feature wrap indexer (*Han Xiao*)
 - [[```57600153```](https://github.com/jina-ai/jina/commit/576001536ced8ae411e9c7a29873cf989563ddae)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```d985f4d6```](https://github.com/jina-ai/jina/commit/d985f4d66a71d4926a35216f68022a840bfdf74a)] __-__ Delete 1500x667 new.gif (*BingHo1013*)
 - [[```a4618512```](https://github.com/jina-ai/jina/commit/a4618512623e2422ceed564071273344446fe182)] __-__ update readme gif (*BingHo1013*)
 - [[```6e3ece22```](https://github.com/jina-ai/jina/commit/6e3ece22d7c58819ebdf4fe792ac5ea0a29dc8f1)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```80100ca2```](https://github.com/jina-ai/jina/commit/80100ca22196d03c731c796c4e42246e35694023)] __-__ __version__: the next version will be 0.3.3 (*Jina Dev Bot*)
 - [[```0db4bd9f```](https://github.com/jina-ai/jina/commit/0db4bd9fee7c6403b93de5a72fd652e76c275a35)] __-__ hotfix publish driver (*Han Xiao*)

## Release Note (`0.3.4`)

> Release time: 2020-07-03 15:57:20



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  fhaase2,  Jina Dev Bot,  Nan Wang,  hanxiao,  BingHo1013,  Andrey Vasnetsov,  Morry Wang,  coolmian,  JamesTang616,  🙇


### 🆕 New Features

 - [[```7abe42ad```](https://github.com/jina-ai/jina/commit/7abe42ad39bf112e84a6ec0a4de554a604882ebc)] __-__ __peapods__: add uvloop as an alternative event loop (*Han Xiao*)
 - [[```6af3f1fb```](https://github.com/jina-ai/jina/commit/6af3f1fb782c0d5f99b2a16a7572b1b0ea28d730)] __-__ rename port grpc (*fhaase2*)
 - [[```7e592805```](https://github.com/jina-ai/jina/commit/7e592805cef3fd1fef8b93783a5f569a7e555dd9)] __-__ __helloworld__: add cli arg &#39;download-proxy&#39; (*Morry Wang*)
 - [[```5ac225e8```](https://github.com/jina-ai/jina/commit/5ac225e809adf266837ac372f56b80e19b59353b)] __-__ __indexer__: allow user switch indexer in query time (*Han Xiao*)
 - [[```7cb893a7```](https://github.com/jina-ai/jina/commit/7cb893a78a7655797cef3f12d0c507e940c9825a)] __-__ __encoder__: add fastica to numeric encoders (*JamesTang616*)
 - [[```6158ce3d```](https://github.com/jina-ai/jina/commit/6158ce3d188c50163e8d4d2595b52e5232ad483a)] __-__ __indexer__: add size (*Han Xiao*)
 - [[```66bef2c1```](https://github.com/jina-ai/jina/commit/66bef2c1ff30caff5306d91da63020bed1d93d1b)] __-__ __proto__: add location info to chunk (*Han Xiao*)

### 🐞 Bug fixes

 - [[```d535c5ec```](https://github.com/jina-ai/jina/commit/d535c5ec472f10d7656547593eb171d19f9c1483)] __-__ __flow__: fix the mismatched arguments (*Nan Wang*)
 - [[```ab123027```](https://github.com/jina-ai/jina/commit/ab1230279309f0bac2559aeb5c67edce89c9fb73)] __-__ __docs__: correct the mismatched parameter value (*coolmian*)
 - [[```11f80552```](https://github.com/jina-ai/jina/commit/11f8055285753ae28deb7593bfaf2ed571d68270)] __-__ __indexer__: fix index size logging (*Han Xiao*)
 - [[```487f5bad```](https://github.com/jina-ai/jina/commit/487f5badf922973b2ba2cfa901817ab1ed930362)] __-__ __driver__: fix del in topkfilter (*Han Xiao*)
 - [[```e4c5aca4```](https://github.com/jina-ai/jina/commit/e4c5aca4b85068f31b0ddc284b00924305f6241a)] __-__ __driver__: topkfilter now remove irrelevant chunks (*Han Xiao*)
 - [[```ea8c1fec```](https://github.com/jina-ai/jina/commit/ea8c1fecd52359e1abbe59f62d8399e0e8505feb)] __-__ __driver__: move topkfilter to ranker (*Han Xiao*)

### 🚧 Code Refactoring

 - [[```1b67d379```](https://github.com/jina-ai/jina/commit/1b67d3794d7335210d9e8e533edeabd7760ab9e8)] __-__ __indexer__: abstract rw ndarray from numpyindexer (*Han Xiao*)

### 📗 Documentation

 - [[```f2f523e1```](https://github.com/jina-ai/jina/commit/f2f523e153ee912596c8cc04216cfba1a1b2fcc5)] __-__ __io__: add shortcut to flow io (*hanxiao*)
 - [[```d5d23395```](https://github.com/jina-ai/jina/commit/d5d23395e74e11ac4989e91cbeef86652f1aabb2)] __-__ __readme__: improve russian readme (*Andrey Vasnetsov*)
 - [[```f18fcfe8```](https://github.com/jina-ai/jina/commit/f18fcfe8db605b9ec3a029954b1405403d429603)] __-__ __contributing__: instructions for github association (*Morry Wang*)

### 🏁 Unit Test and CICD

 - [[```ee84d174```](https://github.com/jina-ai/jina/commit/ee84d174e30dc7f4f9d56550605c673c1c2526bc)] __-__ use image built from pr in tests (*fhaase2*)

### 🍹 Other Improvements

 - [[```76980af4```](https://github.com/jina-ai/jina/commit/76980af4ea2b9ea699524d3f6e5043c3481cfdd5)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```61d243f8```](https://github.com/jina-ai/jina/commit/61d243f86c16eae60ede43c3a2bb6ccda764196c)] __-__ fix link (*Han Xiao*)
 - [[```7bdea9c7```](https://github.com/jina-ai/jina/commit/7bdea9c774a7659b19419df79f64c3014bebdd5c)] __-__ update readme gif banner (*BingHo1013*)
 - [[```f9dca5b2```](https://github.com/jina-ai/jina/commit/f9dca5b2b7bf8da3b53614909024aac7d88dd59f)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```19e0f3fa```](https://github.com/jina-ai/jina/commit/19e0f3fadbe7d8a20999740ec239c0a51b98f356)] __-__ __version__: the next version will be 0.3.4 (*Jina Dev Bot*)
 - [[```9016b4d4```](https://github.com/jina-ai/jina/commit/9016b4d40edda3dfefed1565a601a87ab28eb23a)] __-__ update readme gif (*BingHo1013*)
 - [[```d985f4d6```](https://github.com/jina-ai/jina/commit/d985f4d66a71d4926a35216f68022a840bfdf74a)] __-__ Delete 1500x667 new.gif (*BingHo1013*)
 - [[```80100ca2```](https://github.com/jina-ai/jina/commit/80100ca22196d03c731c796c4e42246e35694023)] __-__ __version__: the next version will be 0.3.3 (*Jina Dev Bot*)
 - [[```60000083```](https://github.com/jina-ai/jina/commit/60000083c57a6cf17f77fc50e6fc496089516f13)] __-__ __version__: the next version will be 0.3.2 (*Jina Dev Bot*)
 - [[```0db4bd9f```](https://github.com/jina-ai/jina/commit/0db4bd9fee7c6403b93de5a72fd652e76c275a35)] __-__ hotfix publish driver (*Han Xiao*)

## Release Note (`0.3.5`)

> Release time: 2020-07-04 17:33:55



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  Jina Dev Bot,  Anish Pawar,  Anish,  🙇


### 🆕 New Features

 - [[```a793a1e4```](https://github.com/jina-ai/jina/commit/a793a1e467b70de8921e1b6f7a72984aa9f83bef)] __-__ __executor__: add image custom keras (*Anish*)

### 🐞 Bug fixes

 - [[```9890883a```](https://github.com/jina-ai/jina/commit/9890883a0d3bc8cda364bda5f4152eff110a3005)] __-__ __gpu__: auto degrade when gpu not available (*Han Xiao*)
 - [[```4fd2ff2a```](https://github.com/jina-ai/jina/commit/4fd2ff2aceab00e97e82c7d4a2e835fe9a16d23c)] __-__ __executor__: fix init (*Anish*)
 - [[```ca23ea7a```](https://github.com/jina-ai/jina/commit/ca23ea7a2e22a42b4d24a84a5bab41cd03c2308a)] __-__ __executor__: fix encode axis (*Anish*)
 - [[```f46e678e```](https://github.com/jina-ai/jina/commit/f46e678e8155e4ff7dcab29a8ff1d019a3f94b80)] __-__ __executor__: add device support (*Anish*)

### 🚧 Code Refactoring

 - [[```29315644```](https://github.com/jina-ai/jina/commit/29315644a93f569ea5ce06920fee8f023f96722c)] __-__ __executor__: change imports (*Anish Pawar*)
 - [[```505bacb4```](https://github.com/jina-ai/jina/commit/505bacb46161e8d16fb497909cc4e77a217f05e8)] __-__ __executor__: var name custom keras (*Anish*)

### 🏁 Unit Test and CICD

 - [[```b988e6e4```](https://github.com/jina-ai/jina/commit/b988e6e4de374cb661eecbee33b20f65ec5fc708)] __-__ __executor__: add custom keras test (*Anish Pawar*)

### 🍹 Other Improvements

 - [[```c4e07596```](https://github.com/jina-ai/jina/commit/c4e075968c84393b9bebea4c746395c4ff20a593)] __-__ hotfix prep for new zmq feature (*Han Xiao*)
 - [[```6a10ab4d```](https://github.com/jina-ai/jina/commit/6a10ab4d18984143d49e1347483da0e6c3e87bb9)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```5a4195aa```](https://github.com/jina-ai/jina/commit/5a4195aae688b5ab7ba5dd400845121e565ba4bd)] __-__ __version__: the next version will be 0.3.5 (*Jina Dev Bot*)
 - [[```49de8711```](https://github.com/jina-ai/jina/commit/49de87113b665341c588329f9c54ba2f379b4ebd)] __-__ __version__: the next version will be 0.3.1 (*Jina Dev Bot*)
 - [[```4ceb5fde```](https://github.com/jina-ai/jina/commit/4ceb5fde70d3dcd87af8784a3a3a690b5c6ad69e)] __-__ hotfix password stdin (*Han Xiao*)

## Release Note (`0.3.6`)

> Release time: 2020-07-05 19:21:46



🙇 We'd like to thank all contributors for this new release! In particular,
 Han Xiao,  fhaase2,  Jina Dev Bot,  Joan Fontanals Martinez,  Anish Pawar,  Nan Wang,  hanxiao,  BingHo1013,  Andrey Vasnetsov,  Morry Wang,  coolmian,  JamesTang616,  Anish,  🙇


### 🆕 New Features

 - [[```b06bef4a```](https://github.com/jina-ai/jina/commit/b06bef4a98aeab831c9e9a6d3ce5a88170861fc6)] __-__ __encoder__: transformers truncation strategy (*fhaase2*)
 - [[```c4761110```](https://github.com/jina-ai/jina/commit/c47611100622aac135750d9863bf16dffa9bf348)] __-__ __dockerfile__: add prebuilt packages (*Han Xiao*)
 - [[```6650da6a```](https://github.com/jina-ai/jina/commit/6650da6a80ed52c1d4f1fea92a242c4c5f3f29d6)] __-__ __setup!__: make tornado as a base dependency (*Han Xiao*)
 - [[```eab1a393```](https://github.com/jina-ai/jina/commit/eab1a3933cfefac5887cbd8bf46084d1731067a2)] __-__ __zmq__: use zmqstream as default zmqlet (*Han Xiao*)
 - [[```6af3f1fb```](https://github.com/jina-ai/jina/commit/6af3f1fb782c0d5f99b2a16a7572b1b0ea28d730)] __-__ rename port grpc (*fhaase2*)
 - [[```7e592805```](https://github.com/jina-ai/jina/commit/7e592805cef3fd1fef8b93783a5f569a7e555dd9)] __-__ __helloworld__: add cli arg &#39;download-proxy&#39; (*Morry Wang*)
 - [[```5ac225e8```](https://github.com/jina-ai/jina/commit/5ac225e809adf266837ac372f56b80e19b59353b)] __-__ __indexer__: allow user switch indexer in query time (*Han Xiao*)
 - [[```7cb893a7```](https://github.com/jina-ai/jina/commit/7cb893a78a7655797cef3f12d0c507e940c9825a)] __-__ __encoder__: add fastica to numeric encoders (*JamesTang616*)
 - [[```6158ce3d```](https://github.com/jina-ai/jina/commit/6158ce3d188c50163e8d4d2595b52e5232ad483a)] __-__ __indexer__: add size (*Han Xiao*)
 - [[```66bef2c1```](https://github.com/jina-ai/jina/commit/66bef2c1ff30caff5306d91da63020bed1d93d1b)] __-__ __proto__: add location info to chunk (*Han Xiao*)
 - [[```a793a1e4```](https://github.com/jina-ai/jina/commit/a793a1e467b70de8921e1b6f7a72984aa9f83bef)] __-__ __executor__: add image custom keras (*Anish*)

### 🐞 Bug fixes

 - [[```6d201a8b```](https://github.com/jina-ai/jina/commit/6d201a8b72abcef6217f9176688df806e480d88e)] __-__ __peapods__: got events closed stream (*fhaase2*)
 - [[```90a4fce1```](https://github.com/jina-ai/jina/commit/90a4fce171302208f32da79b56e800cc82866cdb)] __-__ __ci__: remove redundant print (*Han Xiao*)
 - [[```f22420fd```](https://github.com/jina-ai/jina/commit/f22420fd1dd9205c9207888231b57e1969500223)] __-__ __unittest__: adapt extra requirements (*Joan Fontanals Martinez*)
 - [[```ed8b97c0```](https://github.com/jina-ai/jina/commit/ed8b97c00c36ab576ef7f683ce28a5d249f51c41)] __-__ __unittest__: install extra libsndfile lib dependency (*Joan Fontanals Martinez*)
 - [[```bcbf4f1b```](https://github.com/jina-ai/jina/commit/bcbf4f1b485af9ceded0a951157550065e2a39f1)] __-__ __unittest__: fix segmenter test (*Joan Fontanals Martinez*)
 - [[```9890883a```](https://github.com/jina-ai/jina/commit/9890883a0d3bc8cda364bda5f4152eff110a3005)] __-__ __gpu__: auto degrade when gpu not available (*Han Xiao*)
 - [[```a7578f9d```](https://github.com/jina-ai/jina/commit/a7578f9d62910a8e3cfe93b40ae2cf0ec1e99eb1)] __-__ __unittest__: fix sentencizer output for chinese language (*Joan Fontanals Martinez*)
 - [[```ee7a2274```](https://github.com/jina-ai/jina/commit/ee7a22749c61c0ec5a5aede2e480fb189a450fd0)] __-__ __unittest__: check ranker is not none when testing (*Joan Fontanals Martinez*)
 - [[```d535c5ec```](https://github.com/jina-ai/jina/commit/d535c5ec472f10d7656547593eb171d19f9c1483)] __-__ __flow__: fix the mismatched arguments (*Nan Wang*)
 - [[```ab123027```](https://github.com/jina-ai/jina/commit/ab1230279309f0bac2559aeb5c67edce89c9fb73)] __-__ __docs__: correct the mismatched parameter value (*coolmian*)
 - [[```11f80552```](https://github.com/jina-ai/jina/commit/11f8055285753ae28deb7593bfaf2ed571d68270)] __-__ __indexer__: fix index size logging (*Han Xiao*)
 - [[```487f5bad```](https://github.com/jina-ai/jina/commit/487f5badf922973b2ba2cfa901817ab1ed930362)] __-__ __driver__: fix del in topkfilter (*Han Xiao*)
 - [[```4fd2ff2a```](https://github.com/jina-ai/jina/commit/4fd2ff2aceab00e97e82c7d4a2e835fe9a16d23c)] __-__ __executor__: fix init (*Anish*)
 - [[```e4c5aca4```](https://github.com/jina-ai/jina/commit/e4c5aca4b85068f31b0ddc284b00924305f6241a)] __-__ __driver__: topkfilter now remove irrelevant chunks (*Han Xiao*)
 - [[```ea8c1fec```](https://github.com/jina-ai/jina/commit/ea8c1fecd52359e1abbe59f62d8399e0e8505feb)] __-__ __driver__: move topkfilter to ranker (*Han Xiao*)
 - [[```ca23ea7a```](https://github.com/jina-ai/jina/commit/ca23ea7a2e22a42b4d24a84a5bab41cd03c2308a)] __-__ __executor__: fix encode axis (*Anish*)
 - [[```f46e678e```](https://github.com/jina-ai/jina/commit/f46e678e8155e4ff7dcab29a8ff1d019a3f94b80)] __-__ __executor__: add device support (*Anish*)

### 🚧 Code Refactoring

 - [[```29315644```](https://github.com/jina-ai/jina/commit/29315644a93f569ea5ce06920fee8f023f96722c)] __-__ __executor__: change imports (*Anish Pawar*)
 - [[```1b67d379```](https://github.com/jina-ai/jina/commit/1b67d3794d7335210d9e8e533edeabd7760ab9e8)] __-__ __indexer__: abstract rw ndarray from numpyindexer (*Han Xiao*)
 - [[```505bacb4```](https://github.com/jina-ai/jina/commit/505bacb46161e8d16fb497909cc4e77a217f05e8)] __-__ __executor__: var name custom keras (*Anish*)

### 📗 Documentation

 - [[```f2f523e1```](https://github.com/jina-ai/jina/commit/f2f523e153ee912596c8cc04216cfba1a1b2fcc5)] __-__ __io__: add shortcut to flow io (*hanxiao*)
 - [[```d5d23395```](https://github.com/jina-ai/jina/commit/d5d23395e74e11ac4989e91cbeef86652f1aabb2)] __-__ __readme__: improve russian readme (*Andrey Vasnetsov*)
 - [[```f18fcfe8```](https://github.com/jina-ai/jina/commit/f18fcfe8db605b9ec3a029954b1405403d429603)] __-__ __contributing__: instructions for github association (*Morry Wang*)

### 🏁 Unit Test and CICD

 - [[```16242579```](https://github.com/jina-ai/jina/commit/16242579a0a07a953f3cd28bd04190e349560f8a)] __-__ __cla__: add new colleagues (*Han Xiao*)
 - [[```54c12d16```](https://github.com/jina-ai/jina/commit/54c12d16b5588effc34dc2daa7af8f248acc3a57)] __-__ __unittest__: change relative paths in tests (*Joan Fontanals Martinez*)
 - [[```f3e74b23```](https://github.com/jina-ai/jina/commit/f3e74b23f5be12fab1d6f62b2c677e35269246ee)] __-__ __crafters__: fix missing parameter in image crafter test (*Joan Fontanals Martinez*)
 - [[```249674d5```](https://github.com/jina-ai/jina/commit/249674d51552e76444ee6cd51a03004b67a5b869)] __-__ __audio__: add numba version extra dependency (*Joan Fontanals Martinez*)
 - [[```ee84d174```](https://github.com/jina-ai/jina/commit/ee84d174e30dc7f4f9d56550605c673c1c2526bc)] __-__ use image built from pr in tests (*fhaase2*)
 - [[```868a8d10```](https://github.com/jina-ai/jina/commit/868a8d10d7bf911289fb98caef96a7e7cc5a513c)] __-__ __indexers__: adapt keyvalue test_leveldb (*Joan Fontanals Martinez*)
 - [[```8b5dd603```](https://github.com/jina-ai/jina/commit/8b5dd603e836d3d3edfa820532265c398649b194)] __-__ __crafters__: adapt test file name to standard (*Joan Fontanals Martinez*)
 - [[```cd2727e2```](https://github.com/jina-ai/jina/commit/cd2727e2a4b705a0dd88a5c243e90152b2811553)] __-__ __unittest__: allow test discovery from unittest (*Joan Fontanals Martinez*)
 - [[```b988e6e4```](https://github.com/jina-ai/jina/commit/b988e6e4de374cb661eecbee33b20f65ec5fc708)] __-__ __executor__: add custom keras test (*Anish Pawar*)

### 🍹 Other Improvements

 - [[```3e6489de```](https://github.com/jina-ai/jina/commit/3e6489dec6d8bfd02a0a08fe7e35897d52a422e6)] __-__ hotfix fix resource warning (*Han Xiao*)
 - [[```a0673912```](https://github.com/jina-ai/jina/commit/a0673912ef564af7e2f506ddfd81470443a4782a)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```2afe3852```](https://github.com/jina-ai/jina/commit/2afe385284c707ae1baaa4f64bae1166a4494d8d)] __-__ __version__: the next version will be 0.3.6 (*Jina Dev Bot*)
 - [[```5a4195aa```](https://github.com/jina-ai/jina/commit/5a4195aae688b5ab7ba5dd400845121e565ba4bd)] __-__ __version__: the next version will be 0.3.5 (*Jina Dev Bot*)
 - [[```7bff1f75```](https://github.com/jina-ai/jina/commit/7bff1f75601f7e7a8e5bcb8fdfe6069da0259718)] __-__ Merge pull request #615 from jina-ai/feat-uvloop (*Han Xiao*)
 - [[```61d243f8```](https://github.com/jina-ai/jina/commit/61d243f86c16eae60ede43c3a2bb6ccda764196c)] __-__ fix link (*Han Xiao*)
 - [[```7bdea9c7```](https://github.com/jina-ai/jina/commit/7bdea9c774a7659b19419df79f64c3014bebdd5c)] __-__ update readme gif banner (*BingHo1013*)
 - [[```f9dca5b2```](https://github.com/jina-ai/jina/commit/f9dca5b2b7bf8da3b53614909024aac7d88dd59f)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```19e0f3fa```](https://github.com/jina-ai/jina/commit/19e0f3fadbe7d8a20999740ec239c0a51b98f356)] __-__ __version__: the next version will be 0.3.4 (*Jina Dev Bot*)
 - [[```29bbb28b```](https://github.com/jina-ai/jina/commit/29bbb28b935067f2241c3cab35483c1ce3fcbc2c)] __-__ hotfix feature wrap indexer (*Han Xiao*)
 - [[```9016b4d4```](https://github.com/jina-ai/jina/commit/9016b4d40edda3dfefed1565a601a87ab28eb23a)] __-__ update readme gif (*BingHo1013*)
 - [[```80100ca2```](https://github.com/jina-ai/jina/commit/80100ca22196d03c731c796c4e42246e35694023)] __-__ __version__: the next version will be 0.3.3 (*Jina Dev Bot*)
 - [[```60000083```](https://github.com/jina-ai/jina/commit/60000083c57a6cf17f77fc50e6fc496089516f13)] __-__ __version__: the next version will be 0.3.2 (*Jina Dev Bot*)
 - [[```0db4bd9f```](https://github.com/jina-ai/jina/commit/0db4bd9fee7c6403b93de5a72fd652e76c275a35)] __-__ hotfix publish driver (*Han Xiao*)
 - [[```49de8711```](https://github.com/jina-ai/jina/commit/49de87113b665341c588329f9c54ba2f379b4ebd)] __-__ __version__: the next version will be 0.3.1 (*Jina Dev Bot*)
 - [[```4ceb5fde```](https://github.com/jina-ai/jina/commit/4ceb5fde70d3dcd87af8784a3a3a690b5c6ad69e)] __-__ hotfix password stdin (*Han Xiao*)

## Release Note (`0.3.7`)

> Release time: 2020-07-10 15:57:32



🙇 We'd like to thank all contributors for this new release! In particular,
 Jina Dev Bot,  Han Xiao,  Joan Fontanals Martinez,  Alex C-G,  fhaase2,  Anish Pawar,  Nan Wang,  hanxiao,  BingHo1013,  Andrey Vasnetsov,  Morry Wang,  coolmian,  JamesTang616,  Anish,  🙇


### 🆕 New Features

 - [[```f20b8e30```](https://github.com/jina-ai/jina/commit/f20b8e304dcc4e3266e1143e53e722d8c0c4c9c2)] __-__ __frameworks__: add faiss framework to be able to move index to gpu (*Joan Fontanals Martinez*)
 - [[```95e036e6```](https://github.com/jina-ai/jina/commit/95e036e670e659337755f3c3a0f430d6426c6eb5)] __-__ __flow__: change search_numpy to search_ndarray for consistency (*Joan Fontanals Martinez*)
 - [[```ee6df32e```](https://github.com/jina-ai/jina/commit/ee6df32ea165b8b7623273a7d2c542de39d04b08)] __-__ __drivers__: add unaryencodedriver (*Joan Fontanals Martinez*)
 - [[```aba01f94```](https://github.com/jina-ai/jina/commit/aba01f948327f7f12a0b10323b0fe1c7d86f8371)] __-__ __flow__: dryrun is running by default (*Han Xiao*)
 - [[```d86d821c```](https://github.com/jina-ai/jina/commit/d86d821c96e0c12a71b6584f07cdaaf5c85af5d1)] __-__ __crafter__: add crafter arraybytesreader (*Joan Fontanals Martinez*)
 - [[```6af3f1fb```](https://github.com/jina-ai/jina/commit/6af3f1fb782c0d5f99b2a16a7572b1b0ea28d730)] __-__ rename port grpc (*fhaase2*)
 - [[```7e592805```](https://github.com/jina-ai/jina/commit/7e592805cef3fd1fef8b93783a5f569a7e555dd9)] __-__ __helloworld__: add cli arg &#39;download-proxy&#39; (*Morry Wang*)
 - [[```5ac225e8```](https://github.com/jina-ai/jina/commit/5ac225e809adf266837ac372f56b80e19b59353b)] __-__ __indexer__: allow user switch indexer in query time (*Han Xiao*)
 - [[```7cb893a7```](https://github.com/jina-ai/jina/commit/7cb893a78a7655797cef3f12d0c507e940c9825a)] __-__ __encoder__: add fastica to numeric encoders (*JamesTang616*)
 - [[```6158ce3d```](https://github.com/jina-ai/jina/commit/6158ce3d188c50163e8d4d2595b52e5232ad483a)] __-__ __indexer__: add size (*Han Xiao*)
 - [[```66bef2c1```](https://github.com/jina-ai/jina/commit/66bef2c1ff30caff5306d91da63020bed1d93d1b)] __-__ __proto__: add location info to chunk (*Han Xiao*)
 - [[```a793a1e4```](https://github.com/jina-ai/jina/commit/a793a1e467b70de8921e1b6f7a72984aa9f83bef)] __-__ __executor__: add image custom keras (*Anish*)

### 🐞 Bug fixes

 - [[```63204742```](https://github.com/jina-ai/jina/commit/63204742a923205c15a176c8f5fb73c728213cee)] __-__ __helloworld__: remove unused component (*Joan Fontanals Martinez*)
 - [[```e0ed7e4c```](https://github.com/jina-ai/jina/commit/e0ed7e4c2e29aea4163afbb96652d310b18ff131)] __-__ __ci__: remove redundant print (*Han Xiao*)
 - [[```4546a608```](https://github.com/jina-ai/jina/commit/4546a6084ded65c3d8bad384b3c033a9bb0bf310)] __-__ __encoders__: fix mask prune creation (*Joan Fontanals Martinez*)
 - [[```8a70c7f5```](https://github.com/jina-ai/jina/commit/8a70c7f52dc0c66904037c9e11d51a624fbb44e6)] __-__ __driver__: use copyfrom in doc craft driver (*Joan Fontanals Martinez*)
 - [[```efa1cc86```](https://github.com/jina-ai/jina/commit/efa1cc86b4b5d2372ccae07d70f595a97e12b48d)] __-__ __crafter__: document does not have offset (*Joan Fontanals Martinez*)
 - [[```f22420fd```](https://github.com/jina-ai/jina/commit/f22420fd1dd9205c9207888231b57e1969500223)] __-__ __unittest__: adapt extra requirements (*Joan Fontanals Martinez*)
 - [[```ed8b97c0```](https://github.com/jina-ai/jina/commit/ed8b97c00c36ab576ef7f683ce28a5d249f51c41)] __-__ __unittest__: install extra libsndfile lib dependency (*Joan Fontanals Martinez*)
 - [[```bcbf4f1b```](https://github.com/jina-ai/jina/commit/bcbf4f1b485af9ceded0a951157550065e2a39f1)] __-__ __unittest__: fix segmenter test (*Joan Fontanals Martinez*)
 - [[```9890883a```](https://github.com/jina-ai/jina/commit/9890883a0d3bc8cda364bda5f4152eff110a3005)] __-__ __gpu__: auto degrade when gpu not available (*Han Xiao*)
 - [[```a7578f9d```](https://github.com/jina-ai/jina/commit/a7578f9d62910a8e3cfe93b40ae2cf0ec1e99eb1)] __-__ __unittest__: fix sentencizer output for chinese language (*Joan Fontanals Martinez*)
 - [[```ee7a2274```](https://github.com/jina-ai/jina/commit/ee7a22749c61c0ec5a5aede2e480fb189a450fd0)] __-__ __unittest__: check ranker is not none when testing (*Joan Fontanals Martinez*)
 - [[```d535c5ec```](https://github.com/jina-ai/jina/commit/d535c5ec472f10d7656547593eb171d19f9c1483)] __-__ __flow__: fix the mismatched arguments (*Nan Wang*)
 - [[```ab123027```](https://github.com/jina-ai/jina/commit/ab1230279309f0bac2559aeb5c67edce89c9fb73)] __-__ __docs__: correct the mismatched parameter value (*coolmian*)
 - [[```11f80552```](https://github.com/jina-ai/jina/commit/11f8055285753ae28deb7593bfaf2ed571d68270)] __-__ __indexer__: fix index size logging (*Han Xiao*)
 - [[```487f5bad```](https://github.com/jina-ai/jina/commit/487f5badf922973b2ba2cfa901817ab1ed930362)] __-__ __driver__: fix del in topkfilter (*Han Xiao*)
 - [[```4fd2ff2a```](https://github.com/jina-ai/jina/commit/4fd2ff2aceab00e97e82c7d4a2e835fe9a16d23c)] __-__ __executor__: fix init (*Anish*)
 - [[```e4c5aca4```](https://github.com/jina-ai/jina/commit/e4c5aca4b85068f31b0ddc284b00924305f6241a)] __-__ __driver__: topkfilter now remove irrelevant chunks (*Han Xiao*)
 - [[```ea8c1fec```](https://github.com/jina-ai/jina/commit/ea8c1fecd52359e1abbe59f62d8399e0e8505feb)] __-__ __driver__: move topkfilter to ranker (*Han Xiao*)
 - [[```ca23ea7a```](https://github.com/jina-ai/jina/commit/ca23ea7a2e22a42b4d24a84a5bab41cd03c2308a)] __-__ __executor__: fix encode axis (*Anish*)
 - [[```f46e678e```](https://github.com/jina-ai/jina/commit/f46e678e8155e4ff7dcab29a8ff1d019a3f94b80)] __-__ __executor__: add device support (*Anish*)

### 🚧 Code Refactoring

 - [[```e4556d32```](https://github.com/jina-ai/jina/commit/e4556d327e4967f0d98433e092b78e15dfc2cd7f)] __-__ __proto__: remove dry run command (*Han Xiao*)
 - [[```feb41bdb```](https://github.com/jina-ai/jina/commit/feb41bdb7d3f889caa8b77aa1af98920f3e6039b)] __-__ __client__: trigger dry_run from client not the flow (*Han Xiao*)
 - [[```ac6175a7```](https://github.com/jina-ai/jina/commit/ac6175a7d4ca90d8a49ae93a0f1ec61390ec0abf)] __-__ __crafters__: io crafters should craft documents (*Joan Fontanals Martinez*)
 - [[```29315644```](https://github.com/jina-ai/jina/commit/29315644a93f569ea5ce06920fee8f023f96722c)] __-__ __executor__: change imports (*Anish Pawar*)
 - [[```1b67d379```](https://github.com/jina-ai/jina/commit/1b67d3794d7335210d9e8e533edeabd7760ab9e8)] __-__ __indexer__: abstract rw ndarray from numpyindexer (*Han Xiao*)
 - [[```505bacb4```](https://github.com/jina-ai/jina/commit/505bacb46161e8d16fb497909cc4e77a217f05e8)] __-__ __executor__: var name custom keras (*Anish*)

### 📗 Documentation

 - [[```d4e006d6```](https://github.com/jina-ai/jina/commit/d4e006d63644dcc4ff4ce6b454507216810c208a)] __-__ __readme__: promote tutorials heading (*Alex C-G*)
 - [[```caeb6268```](https://github.com/jina-ai/jina/commit/caeb6268f189ee3a60000b254e016455e7946c7b)] __-__ __readme__: tweaks based on hans feedback (*Alex C-G*)
 - [[```7cd44a61```](https://github.com/jina-ai/jina/commit/7cd44a61e0473d414e0e650ba228ec7af7cb48f5)] __-__ __101__: add link to explain basics of neural search (*Alex C-G*)
 - [[```f2f523e1```](https://github.com/jina-ai/jina/commit/f2f523e153ee912596c8cc04216cfba1a1b2fcc5)] __-__ __io__: add shortcut to flow io (*hanxiao*)
 - [[```d5d23395```](https://github.com/jina-ai/jina/commit/d5d23395e74e11ac4989e91cbeef86652f1aabb2)] __-__ __readme__: improve russian readme (*Andrey Vasnetsov*)
 - [[```f18fcfe8```](https://github.com/jina-ai/jina/commit/f18fcfe8db605b9ec3a029954b1405403d429603)] __-__ __contributing__: instructions for github association (*Morry Wang*)

### 🏁 Unit Test and CICD

 - [[```c3f6138c```](https://github.com/jina-ai/jina/commit/c3f6138c28f1cd6b493b024a7f33e5b0bf4959fa)] __-__ __indexers__: split indexer tests  and add faiss indexer test (*Joan Fontanals Martinez*)
 - [[```1588cfd2```](https://github.com/jina-ai/jina/commit/1588cfd2df34fe3971941d58ce119b0b2d75c541)] __-__ __flow__: improved log server tests (*fhaase2*)
 - [[```6d2056f7```](https://github.com/jina-ai/jina/commit/6d2056f70152fc8cf15ce07cbe5be098a96284cf)] __-__ __crafters__: add tests for array bytes reader (*Joan Fontanals Martinez*)
 - [[```54c12d16```](https://github.com/jina-ai/jina/commit/54c12d16b5588effc34dc2daa7af8f248acc3a57)] __-__ __unittest__: change relative paths in tests (*Joan Fontanals Martinez*)
 - [[```f3e74b23```](https://github.com/jina-ai/jina/commit/f3e74b23f5be12fab1d6f62b2c677e35269246ee)] __-__ __crafters__: fix missing parameter in image crafter test (*Joan Fontanals Martinez*)
 - [[```249674d5```](https://github.com/jina-ai/jina/commit/249674d51552e76444ee6cd51a03004b67a5b869)] __-__ __audio__: add numba version extra dependency (*Joan Fontanals Martinez*)
 - [[```ee84d174```](https://github.com/jina-ai/jina/commit/ee84d174e30dc7f4f9d56550605c673c1c2526bc)] __-__ use image built from pr in tests (*fhaase2*)
 - [[```868a8d10```](https://github.com/jina-ai/jina/commit/868a8d10d7bf911289fb98caef96a7e7cc5a513c)] __-__ __indexers__: adapt keyvalue test_leveldb (*Joan Fontanals Martinez*)
 - [[```8b5dd603```](https://github.com/jina-ai/jina/commit/8b5dd603e836d3d3edfa820532265c398649b194)] __-__ __crafters__: adapt test file name to standard (*Joan Fontanals Martinez*)
 - [[```cd2727e2```](https://github.com/jina-ai/jina/commit/cd2727e2a4b705a0dd88a5c243e90152b2811553)] __-__ __unittest__: allow test discovery from unittest (*Joan Fontanals Martinez*)
 - [[```b988e6e4```](https://github.com/jina-ai/jina/commit/b988e6e4de374cb661eecbee33b20f65ec5fc708)] __-__ __executor__: add custom keras test (*Anish Pawar*)

### 🍹 Other Improvements

 - [[```714604ef```](https://github.com/jina-ai/jina/commit/714604ef3c4a3c1c8b830b825cf5283425ec3ad1)] __-__ update copyright header (*Jina Dev Bot*)
 - [[```95a535e1```](https://github.com/jina-ai/jina/commit/95a535e1170f8dddffbba9a9a0e1e7f311b36555)] __-__ fix typo in readme (*Han Xiao*)
 - [[```2186a43f```](https://github.com/jina-ai/jina/commit/2186a43f0f83978f3a6825a313822e2e1795e2bd)] __-__ __docs__: update TOC (*Jina Dev Bot*)
 - [[```0245bcd9```](https://github.com/jina-ai/jina/commit/0245bcd91dae4117cff45a8725ec287e93f3215a)] __-__ __version__: the next version will be 0.3.7 (*Jina Dev Bot*)
 - [[```2afe3852```](https://github.com/jina-ai/jina/commit/2afe385284c707ae1baaa4f64bae1166a4494d8d)] __-__ __version__: the next version will be 0.3.6 (*Jina Dev Bot*)
 - [[```c4e07596```](https://github.com/jina-ai/jina/commit/c4e075968c84393b9bebea4c746395c4ff20a593)] __-__ hotfix prep for new zmq feature (*Han Xiao*)
 - [[```5a4195aa```](https://github.com/jina-ai/jina/commit/5a4195aae688b5ab7ba5dd400845121e565ba4bd)] __-__ __version__: the next version will be 0.3.5 (*Jina Dev Bot*)
 - [[```7bff1f75```](https://github.com/jina-ai/jina/commit/7bff1f75601f7e7a8e5bcb8fdfe6069da0259718)] __-__ Merge pull request #615 from jina-ai/feat-uvloop (*Han Xiao*)
 - [[```61d243f8```](https://github.com/jina-ai/jina/commit/61d243f86c16eae60ede43c3a2bb6ccda764196c)] __-__ fix link (*Han Xiao*)
 - [[```7bdea9c7```](https://github.com/jina-ai/jina/commit/7bdea9c774a7659b19419df79f64c3014bebdd5c)] __-__ update readme gif banner (*BingHo1013*)
 - [[```19e0f3fa```](https://github.com/jina-ai/jina/commit/19e0f3fadbe7d8a20999740ec239c0a51b98f356)] __-__ __version__: the next version will be 0.3.4 (*Jina Dev Bot*)
 - [[```29bbb28b```](https://github.com/jina-ai/jina/commit/29bbb28b935067f2241c3cab35483c1ce3fcbc2c)] __-__ hotfix feature wrap indexer (*Han Xiao*)
 - [[```9016b4d4```](https://github.com/jina-ai/jina/commit/9016b4d40edda3dfefed1565a601a87ab28eb23a)] __-__ update readme gif (*BingHo1013*)
 - [[```80100ca2```](https://github.com/jina-ai/jina/commit/80100ca22196d03c731c796c4e42246e35694023)] __-__ __version__: the next version will be 0.3.3 (*Jina Dev Bot*)
 - [[```60000083```](https://github.com/jina-ai/jina/commit/60000083c57a6cf17f77fc50e6fc496089516f13)] __-__ __version__: the next version will be 0.3.2 (*Jina Dev Bot*)
 - [[```0db4bd9f```](https://github.com/jina-ai/jina/commit/0db4bd9fee7c6403b93de5a72fd652e76c275a35)] __-__ hotfix publish driver (*Han Xiao*)
 - [[```49de8711```](https://github.com/jina-ai/jina/commit/49de87113b665341c588329f9c54ba2f379b4ebd)] __-__ __version__: the next version will be 0.3.1 (*Jina Dev Bot*)
 - [[```4ceb5fde```](https://github.com/jina-ai/jina/commit/4ceb5fde70d3dcd87af8784a3a3a690b5c6ad69e)] __-__ hotfix password stdin (*Han Xiao*)

