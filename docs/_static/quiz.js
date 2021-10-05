const rawMarkdown = `## Document

### 1. What can kind of data can a Document contain?

- Just plain text
- Numpy array
- Any kind of data

> [A Document can contain *any* kind of data that can be stored digitally](https://docs.jina.ai/fundamentals/document/document-api/#document-content). Text, graphics, audio, video, amino acids, 3D meshes, Numpy arrays, you name it.
`


const app = new Vue({
    el: '#quiz-container',
    delimiters: ['${', '}'],
    data: {
      rawMarkdown 
    },
    computed: {
        htmlContent:  () => {
            return marked(rawMarkdown)
        }
    },
    methods: {
       
    }
})