const app = new Vue({
    el: '#jina-docbot',
    delimiters: ['${', '}'],
    data: {
        is_busy: false,
        is_conn_broken: false,
        general_config: {
            server_port: 65123,
            server_address: `http://localhost`,
            search_endpoint: '/search',
            slack_endpoint: '/slack'
        },
        qa_pairs: [],
        cur_question: '',
    },
    computed: {
        host_address: function () {
            return `${this.general_config.server_address}:${this.general_config.server_port}`
        },
        search_address: function () {
            return `${this.host_address}${this.general_config.search_endpoint}`
        },
        slack_address: function () {
            return `${this.host_address}${this.general_config.slack_endpoint}`
        },
    },
    methods: {
        submit_q: function () {
            app.is_busy = true
            app.is_conn_broken = false
            app.qa_pairs.push({"question": app.cur_question})
            $.ajax({
                type: "POST",
                url: app.fit_address,
                data: JSON.stringify({
                    data: [{'text': app.cur_question}],
                }),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function (data, textStatus, jqXHR) {
                    // reset current question to empty
                    app.cur_question = ""
                },
                error: function () {
                    app.qa_pairs.slice(-1)[0]['answer'] = `Server (${app.host_address}) is not responding atm! Please report this issue via Slack.`
                    app.is_conn_broken = true

                },
                complete: function () {
                    app.is_busy = false
                    Array.from(document.getElementsByClassName("answer-bubble")).slice(-1)[0].scrollIntoView({block: "nearest", inline: "nearest"});
                }
            });
        },
    }
})