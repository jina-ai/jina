const fs = require("fs")
const path = require("path")
const marked = require("marked")

const renderer = {
  heading(text, level) {
    if(level === 1) return `# ${text}\n`
    return `<h${level}> ${text} </h${level}>\n`
  },
  blockquote(quote) {
      return (
`<details>
<summary>Reveal explanation</summary>
<p>
${quote}
</p>
</details>\n`
      )
  },
  listitem(text) {
    const correctAnswerClasses = text.includes('--correct-answer--') ? 'correct-answer' : 'incorrect-answer'
    text = text.replace('--correct-answer--', '')
    return( `<li class="flex my-2"> <input class="${correctAnswerClasses} mr-4 mt-1" type="checkbox"><div class="option"> ${text} </div> </li>\n`)
  }
}
marked.use({renderer})

const getAllFiles = function(dirPath, arrayOfFiles) {
  files = fs.readdirSync(dirPath)

  arrayOfFiles = arrayOfFiles || []

  files.forEach(function(file) {
    if (fs.statSync(dirPath + "/" + file).isDirectory()) {
      // Don't process files in directories starting with _
      if(file[0] === '_')  return
      arrayOfFiles = getAllFiles(dirPath + "/" + file, arrayOfFiles)
    } else {
      arrayOfFiles.push(path.join(__dirname, dirPath, "/", file))
    }
  })

  return arrayOfFiles
}

const quizFiles = getAllFiles('./').filter(file => file.endsWith('quiz-source.md'))

quizFiles.forEach(function(file) {
  fs.readFile(file, 'utf8', function (err,data) {
    if (err) {
      return console.log(err);
    }
    fs.writeFile(file.replace('quiz-source.md', 'quiz.md'), marked(data), function (err) {
      if (err) return console.log(err)
    })
  })
})