#!/usr/bin/env bash

# yarn all-contributors check
unset IFS
cont="hanxiao, nan-wang, JoanFM, jina-bot, alexcg1, fhaase2, policeme, shivam-raj, YueLiu-jina, allcontributors[bot], anish2197, antonkurenkov, BingHo1013, maanavshah, guiferviz, redram, joaopalotti, Morriaty-The-Murderer, festeh, phamtrancsek12, Kavan72, boussoffara, roccia, generall, emmaadesile, ericsyh, YikSanChan, JamesTang-jinaai, JamesTang616, rohan1chaudhari, rutujasurve94, tracy-propertyguru, Zenahr, coolmian"
IFS=" "
for v in ${cont//,/}
do
  yarn all-contributors add "${v//[[:blank:]]/}" code
done
yarn all-contributors generate