const rawMarkdown = `## Document

### 1. What can kind of data can a Document contain?

- Just plain text
- Numpy array
- <!---correct---> Any kind of data

> [A Document can contain *any* kind of data that can be stored digitally](https://docs.jina.ai/fundamentals/document/document-api/#document-content). Text, graphics, audio, video, amino acids, 3D meshes, Numpy arrays, you name it.

### 2. Given a Document \`doc\`, what does \`doc.content\` refer to?


- \`doc.buffer\`
- <!---correct---> \`doc.blob\`
- \`doc.text\`
- Any of the above as long as the field is not empty

> [\`doc.content\`](https://docs.jina.ai/fundamentals/document/document-api/#document-content) is an alias that points to whatever attribute contains data. At any given point only \`.buffer\`, \`.blob\` or \`.text\` can contain data. Setting one of these attributes will unset any of the others that were previously in use.

### 3. How do you convert \`doc.uri\` to \`doc.blob\`?

- <!---correct--->
    \`\`\`python
    from jina.Document import convert_uri_to_blob

    doc = Document(uri="foo.txt")
    doc.blob = convert_uri_to_blob(doc)
    \`\`\`

-   \`\`\`python
    from jina.Document import blob

    doc = Document(uri="foo.txt")
    doc.blob = blob(doc.uri)
    \`\`\`

-   \`\`\`python
    doc = Document(uri="foo.txt")
    doc.convert_uri_to_blob()
    \`\`\`


> Converting to a blob is a built-in method of a \`Document\` object (as are many other [\`.convert_x_to_y\` methods](https://docs.jina.ai/fundamentals/document/document-api/#conversion-from-uri-to-content))


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

const app = new Vue({
    el: '#quiz-container',
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