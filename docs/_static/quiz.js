const rawMarkdown = `## Document

### 1. What can kind of data can a Document contain?

- Just plain text
- Numpy array
- Any kind of data

> [A Document can contain *any* kind of data that can be stored digitally](https://docs.jina.ai/fundamentals/document/document-api/#document-content). Text, graphics, audio, video, amino acids, 3D meshes, Numpy arrays, you name it.
`
const renderer = {
    blockquote(quote) {
        return (
            `<details>
                <summary>Reveal explanation</summary>
                <p>
                    ${quote}
                </p>
            </details>`
        )
    },
    listitem(text) {
        return (
            `
                <p> <input type="checkbox"> ${text} </p>
            `
        )
    }
}


marked.use({renderer})

const application = new Vue({
    el: '#quiz-container',
    data: {
      rawMarkdown 
    },
    computed: {
        quizContent:  () => {
            return marked(rawMarkdown)
        }
    },
    methods: {
       
    }
})