# Refactoring the README

## Why?

See my deck on our readme issues!

## A good README

For a developer, a good README:

- **Interests users** - give elevator pitch high-level overview to make users want to take next step
- **Is short and sweet** - we want users to take action, not get bogged down in minutiae
- **Leads users to take action**: Clear action items
- **Shows (not tells)**: Don't talk about our capability, show it as a gif

From our end, it also:

- **Is easy to maintain**
- **Covers us legally**: Copyright and license block
- **Looks professional to investors**

## What action do we want users to take?

Our README is one step of our developer funnel. And it's the step where we lose them! We want clear action items that we can track:

| Action                       | How track             |
|------------------------------|-----------------------|
| Star our repo                | GitHub analytics      |
| Join our Slack community     | Slack analytics       |
| Download via pip or Docker   | Docker/pypi analytics |
| Visit our docs to learn more | Google analytics      |
| Apply for a job              | HR track              |

If an item in the readme doesn't do at least one of these (directly or indirectly), it gets kicked out.

## "Best Practices"

Technically "there are no best practices for writing a readme". In that case we can look at what others do. That's nearer the end of this doc for now

## Changelog

### Done

From top to bottom

| What                       | Why                                                                                |
|----------------------------|------------------------------------------------------------------------------------|
| Bigger logo                | Catch eye. Common in trending repos                                                |
| Redo slogan                | Shorter, punchier, bigger                                                          |
| Add Slack badge            | Show how many users; get ppl to join immediately                                   |
| Add downloads badge        | Show off our many downloads                                                        |
| Remove CI failing badge    | That badge made us look not-great                                                  |
| Remove codecov badge       | Badge wasn't 100%. Makes us look not-great                                         |
| Elevator pitch tweak       | Focus on the what, now how. Use `data` bc more familiar word                       |
| Animations to the top      | Show Jina in action; catch eye                                                     |
| Why Jina bullets           | Verb-oriented - more action item-y                                                 |
| Installation simplify      | Table was overwhelming                                                             |
| The big long feature list  | Removed. It belongs somewhere else, **not** in the readme                          |
| Remove video links         | Who looks at a repo and thinks "dang, I wish I could watch a video to explain it"? |
| Re-add basics(?)           | They disappeared somewhere in the mess                                             |
| Basics, run demo sections  | Super simple intro stuff                                                           |
| Remove documentation image | It wasn't paying its rent                                                          |

### Todo

| What                    | Why                                      | Why not done yet?                             |
|-------------------------|------------------------------------------|-----------------------------------------------|
| Better animation        | Maybe as one slideshow gif. Look nicer   | Need time/creative support                    |
| Wording polish          | Clarity, persuasion                      | Product support needed                        |
| Fix demo links          | Show working demos                       | We don't yet have demo's domain or live demos |
| Check CRUD, etc in docs | CRUD, etc section wasn't paying its rent | Need time to check and/or docs team to write  |

## "Best Practices": What do other popular repo's do?

### They're short

How many times to hit page-down until reach the end?

| Repo                           | Page-downs |
|--------------------------------|------------|
| Jina (2021/03/23 master)       | 20         |
| Haystack                       | 16         |
| Pandas                         | 5          |
| Tensorflow                     | 6          |
| PyTorch                        | 14.5       |
| Transformers                   | 10.3       |
| **Jina (2021/03/23 refactor)** | **6**      |

### Other

- Big bold logo
- Big bold clear slogan: what it is, value proposition
- Badges that don't show failing
- Animated demo as primary eye grabber
- What is it?
- What can you use it for?
- Features

## What don't they do?

- Video links to explain basic things
- Failing badges
