














# Change Logs

Jina is released on every Friday evening. The PyPi package and Docker Image will be updated, the changes of the release will be tracked by this file.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Release Note (`0.0.4`)](#release-note-004)
- [Release Note (`0.0.5`)](#release-note-005)
- [Release Note (`0.0.6`)](#release-note-006)
- [Release Note (`0.0.7`)](#release-note-007)

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

