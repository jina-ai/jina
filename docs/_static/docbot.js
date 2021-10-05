const app = new Vue({
    el: '#jina-docbot',
    delimiters: ['${', '}'],
    data: {
        is_busy: false,
        is_conn_broken: false,
        general_config: {
            server_address: server_address || 'https://docsbot.jina.ai',
            search_endpoint: '/search',
            slack_endpoint: '/slack'
        },
        qa_pairs: [],
        cur_question: '',
        root_url: 'http://docs.jina.ai/'
    },
    computed: {
        host_address: function () {
            return `${this.general_config.server_address}` // :${this.general_config.server_port}
        },
        search_address: function () {
            return `${this.host_address}${this.general_config.search_endpoint}`
        },
        slack_address: function () {
            return `${this.host_address}${this.general_config.slack_endpoint}`
        },
    },
    methods: {
        notify_slack: function (question, answer, thumbup) {
            $.ajax({
                type: "POST",
                url: app.slack_address,
                data: JSON.stringify({
                    data: [],
                    parameters: {
                        "question": question,
                        "answer": answer.text,
                        "answer_uri": `${app.root_url}${answer.uri}`,
                        "thumbup": thumbup,
                    },
                }),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function (data, textStatus, jqXHR) {
                    // reset current question to empty
                    if (thumbup !== null) {
                        Array.from(document.getElementsByClassName("answer-bubble")).slice(-1)[0].scrollIntoView({
                            block: "nearest",
                            inline: "nearest"
                        });
                    }
                },
                error: function (request, status, error) {
                    console.error(error)
                }
            });
        },
        submit_rating: function (qa, val) {
            qa.rating = val;
            app.qa_pairs.push({
                "answer": {
                    "text": "Thanks for your feedback! We will improve 🙇‍♂️",
                    "uri": ""
                }
            })
            app.notify_slack(qa.question, qa.answer, val);
        },
        submit_q: function () {
            app.is_busy = true
            app.is_conn_broken = false
            app.qa_pairs.push({"question": app.cur_question, "rating": null})
            $.ajax({
                type: "POST",
                url: app.search_address,
                data: JSON.stringify({
                    data: [{'text': app.cur_question}],
                }),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function (data, textStatus, jqXHR) {
                    // reset current question to empty
                    const answer = data['data'].docs[0].matches[0]
                    app.qa_pairs.slice(-1)[0]['answer'] = answer
                    app.notify_slack(app.cur_question, answer, null)
                    app.cur_question = ""
                },
                error: function (xhr, status, error) {
                    app.qa_pairs.slice(-1)[0]['answer'] = {'text': `Connection error: ${xhr.responseText}. Please report this issue via Slack.`}
                    app.is_conn_broken = true
                },
                complete: function () {
                    app.is_busy = false
                    Array.from(document.getElementsByClassName("answer-bubble")).slice(-1)[0].scrollIntoView({
                        block: "nearest",
                        inline: "nearest"
                    });
                }
            });
        },
    }
})